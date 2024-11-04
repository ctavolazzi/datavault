from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import logging
import platform
from typing import Dict, List, Optional, Union, Iterator
import time
import shutil
from filelock import FileLock
from threading import Lock
import tempfile
import os

class OperationType(Enum):
    """Types of operations that can be logged"""
    ANALYZE = "analyze"
    MOVE = "move"
    BACKUP = "backup"
    ERROR = "error"
    CONFIG = "config"

@dataclass
class RunMetadata:
    """Metadata about a project manager run"""
    run_id: str
    timestamp: str
    dry_run: bool
    root_directory: str
    python_version: str
    system: str
    structure_config: Dict
    status: str = "running"
    end_timestamp: Optional[str] = None
    duration_seconds: Optional[float] = None

@dataclass
class FileOperation:
    """Record of a file operation"""
    run_id: str
    timestamp: str
    operation_type: OperationType
    source: str
    target: str
    success: bool
    reason: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None

    def validate(self) -> None:
        """Validate operation fields"""
        if not self.source:
            raise ValueError("Source path cannot be empty")
        if not self.target:
            raise ValueError("Target path cannot be empty")
        if not isinstance(self.operation_type, OperationType):
            raise ValueError(f"Invalid operation type: {self.operation_type}")

    def to_dict(self) -> Dict:
        """Convert to dictionary with serializable values"""
        data = asdict(self)
        data['operation_type'] = self.operation_type.value
        return data

class ProjectLogger:
    """Handles structured logging for project operations"""
    
    def __init__(self, root_dir: Path):
        self.root = root_dir
        self.logs_dir = root_dir / 'logs'
        self.runs_dir = self.logs_dir / 'runs'
        self.index_path = self.logs_dir / 'index.json'
        self.lock = Lock()
        
        # Create directory structure
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(exist_ok=True)
        
        # Initialize or load index
        self.index = self._load_index()
        
        # Setup file logging
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure logging"""
        logger = logging.getLogger('project_manager')
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        logger.handlers = []
        
        # Console handler
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(console)
        
        return logger

    def _load_index(self) -> Dict:
        """Load or create the runs index"""
        if self.index_path.exists():
            with open(self.index_path) as f:
                return json.load(f)
        return {
            "runs": {},
            "last_updated": datetime.now().isoformat()
        }

    def _save_index(self):
        """Save the runs index atomically"""
        with self.lock:
            temp_file = self.index_path.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self.index, f, indent=2)
            temp_file.replace(self.index_path)

    def start_run(self, dry_run: bool, structure_config: Dict) -> str:
        """Start a new run and return run_id"""
        timestamp = datetime.now()
        # Add microseconds to ensure unique run_ids
        run_id = timestamp.strftime('%Y%m%d_%H%M%S') + f"_{timestamp.microsecond}"
        
        # Create run directory with exist_ok=True
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / 'operations').mkdir(exist_ok=True)
        
        # Create metadata
        metadata = RunMetadata(
            run_id=run_id,
            timestamp=timestamp.isoformat(),
            dry_run=dry_run,
            root_directory=str(self.root),
            python_version=platform.python_version(),
            system=platform.system(),
            structure_config=structure_config
        )
        
        # Save metadata
        with open(run_dir / 'metadata.json', 'w') as f:
            json.dump(asdict(metadata), f, indent=2)
        
        # Update index
        self.index["runs"][run_id] = {
            "timestamp": timestamp.isoformat(),
            "status": "running",
            "dry_run": dry_run
        }
        self._save_index()
        
        return run_id

    def log_operation(self, operation: FileOperation):
        """Log a file operation"""
        # Validate operation
        operation.validate()
        
        run_dir = self.runs_dir / operation.run_id / 'operations'
        op_file = run_dir / f'{operation.operation_type.value}s.json'
        
        # Use a file lock for thread safety
        lock_file = op_file.with_suffix('.lock')
        lock = FileLock(str(lock_file), timeout=10)
        
        with lock:
            operations = []
            if op_file.exists():
                try:
                    with open(op_file) as f:
                        operations = json.load(f)
                except json.JSONDecodeError:
                    operations = []
            
            operations.append(operation.to_dict())
            
            # Write atomically using temporary file
            temp_file = op_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(operations, f, indent=2)
            temp_file.replace(op_file)

    def log_operations_batch(self, operations: List[FileOperation]):
        """Log multiple operations efficiently"""
        # Group operations by type
        by_type = {}
        for op in operations:
            op.validate()
            op_type = op.operation_type.value
            if op_type not in by_type:
                by_type[op_type] = []
            by_type[op_type].append(op.to_dict())
        
        # Write each type's operations in one go
        for op_type, ops in by_type.items():
            op_file = self.runs_dir / operations[0].run_id / 'operations' / f'{op_type}s.json'
            
            lock_file = op_file.with_suffix('.lock')
            lock = FileLock(str(lock_file), timeout=10)
            
            with lock:
                existing_ops = []
                if op_file.exists():
                    try:
                        with open(op_file) as f:
                            existing_ops = json.load(f)
                    except json.JSONDecodeError:
                        existing_ops = []
                
                existing_ops.extend(ops)
                
                temp_file = op_file.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(existing_ops, f, separators=(',', ':'))
                temp_file.replace(op_file)

    def complete_run(self, run_id: str, status: str = "completed") -> None:
        """Complete a run and update its status"""
        run_dir = self.runs_dir / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run directory not found: {run_dir}")
        
        metadata_file = run_dir / 'metadata.json'
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        end_timestamp = datetime.now().isoformat()
        start_time = datetime.fromisoformat(metadata['timestamp'])
        end_time = datetime.fromisoformat(end_timestamp)
        duration = (end_time - start_time).total_seconds()
        
        metadata.update({
            "status": status,
            "end_timestamp": end_timestamp,
            "duration_seconds": duration
        })
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update index
        self.index["runs"][run_id]["status"] = status
        self._save_index()

    def get_recent_runs(self, days: int = 7) -> List[Dict]:
        """Get runs from the last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []
        
        for run_id, info in self.index["runs"].items():
            run_time = datetime.fromisoformat(info["timestamp"])
            if run_time >= cutoff:
                run_dir = self.runs_dir / run_id
                with open(run_dir / 'metadata.json') as f:
                    recent.append(json.load(f))
        
        return sorted(recent, key=lambda x: x["timestamp"], reverse=True)

    def get_run_summary(self, run_id: str) -> Dict:
        """Get summary of operations for a run"""
        run_dir = self.runs_dir / run_id
        operations_dir = run_dir / 'operations'
        
        summary = {
            "metadata": {},
            "operations": {
                "analyze": {"total": 0, "successful": 0, "failed": 0},
                "move": {"total": 0, "successful": 0, "failed": 0},
                "backup": {"total": 0, "successful": 0, "failed": 0},
                "error": {"total": 0}
            }
        }
        
        # Load metadata
        with open(run_dir / 'metadata.json') as f:
            summary["metadata"] = json.load(f)
        
        # Count operations
        for op_type in OperationType:
            op_file = operations_dir / f'{op_type.value}s.json'
            if op_file.exists():
                with open(op_file) as f:
                    ops = json.load(f)
                    summary["operations"][op_type.value]["total"] = len(ops)
                    if op_type != OperationType.ERROR:
                        summary["operations"][op_type.value].update({
                            "successful": sum(1 for op in ops if op["success"]),
                            "failed": sum(1 for op in ops if not op["success"])
                        })
        
        return summary

    def get_failed_operations(self, run_id: str) -> List[Dict]:
        """Get all failed operations for a run"""
        failed_ops = []
        run_dir = self.runs_dir / run_id / 'operations'
        
        for op_type in OperationType:
            if op_type == OperationType.ERROR:
                continue
                
            op_file = run_dir / f'{op_type.value}s.json'
            if op_file.exists():
                with open(op_file) as f:
                    ops = json.load(f)
                    failed_ops.extend([
                        op for op in ops 
                        if not op["success"]
                    ])
        
        return failed_ops 

    def cleanup_old_runs(self, max_age_days: int = 30) -> None:
        """Remove run data older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        print(f"\nCutoff date: {cutoff_date.isoformat()}")
        
        # First, update the index
        for run_id in list(self.index["runs"].keys()):
            run_dir = self.runs_dir / run_id
            metadata_file = run_dir / "metadata.json"
            
            if not metadata_file.exists():
                print(f"Removing {run_id} (no metadata file)")
                del self.index["runs"][run_id]
                continue
                
            with open(metadata_file) as f:
                metadata = json.load(f)
                run_date = datetime.fromisoformat(metadata["timestamp"])
                
            days_old = (datetime.now() - run_date).days
            if days_old > max_age_days:  # Changed from < to >
                print(f"Removing {run_id} ({days_old} days old)")
                shutil.rmtree(run_dir)
                del self.index["runs"][run_id]
            else:
                print(f"Keeping {run_id} ({days_old} days old)")
        
        self._save_index()

def test_cleanup_old_runs(tmp_path):
    """Test cleaning up old run data"""
    logger = ProjectLogger(tmp_path)
    
    # Use a fixed reference time
    now = datetime.now()
    print(f"\nReference time: {now.isoformat()}")
    
    # Create runs with different timestamps
    test_dates = {
        "current": now,
        "yesterday": now - timedelta(days=1),
        "week_ago": now - timedelta(days=7),
        "month_ago": now - timedelta(days=30),
        "old": now - timedelta(days=90)
    }
    
    run_ids = {}
    for label, timestamp in test_dates.items():
        run_id = timestamp.strftime('%Y%m%d_%H%M%S')
        run_ids[label] = run_id
        
        # Create run directory and metadata
        run_dir = tmp_path / "logs" / "runs" / run_id
        run_dir.mkdir(parents=True)
        
        # Add to index
        logger.index["runs"][run_id] = {
            "timestamp": timestamp.isoformat(),
            "status": "completed",
            "dry_run": True
        }
        
        # Create metadata file
        with open(run_dir / "metadata.json", "w") as f:
            json.dump({
                "timestamp": timestamp.isoformat(),
                "status": "completed",
                "dry_run": True
            }, f)
        
        print(f"Created {label} run: {run_id} ({timestamp.isoformat()})")
    
    logger._save_index()
    
    print("\nBefore cleanup:")
    for run_dir in (tmp_path / "logs" / "runs").glob("*"):
        print(f"- {run_dir.name}")
    
    # Clean up runs older than 30 days
    logger.cleanup_old_runs(max_age_days=30)
    
    print("\nAfter cleanup:")
    remaining_runs = list((tmp_path / "logs" / "runs").glob("*"))
    for run_dir in remaining_runs:
        with open(run_dir / "metadata.json") as f:
            metadata = json.load(f)
            print(f"- {run_dir.name} ({metadata['timestamp']})")
    
    # Verify old runs were removed
    assert len(remaining_runs) == 4, (
        f"Expected 4 runs (current, yesterday, week_ago, month_ago), but got {len(remaining_runs)}:\n"
        + "\n".join(f"- {run.name}" for run in remaining_runs)
    )
    
    # Verify the correct runs remain
    remaining_run_ids = {run.name for run in remaining_runs}
    expected_remaining = {
        run_ids["current"],
        run_ids["yesterday"],
        run_ids["week_ago"],
        run_ids["month_ago"]
    }
    assert remaining_run_ids == expected_remaining, (
        f"Unexpected remaining runs.\nExpected: {sorted(expected_remaining)}\n"
        f"Got: {sorted(remaining_run_ids)}"
    )