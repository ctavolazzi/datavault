from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import logging
import platform
from typing import Dict, List, Optional, Union, Iterator

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
    status: str = "running"  # running, completed, failed
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

class ProjectLogger:
    """Handles structured logging using JSON files"""
    
    def __init__(self, root_dir: Path):
        self.root = root_dir
        self.logs_dir = root_dir / 'logs'
        self.runs_dir = self.logs_dir / 'runs'
        self.index_path = self.logs_dir / 'index.json'
        
        # Create directory structure
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(exist_ok=True)
        
        # Initialize or load index
        self.index = self._load_index()
        
        # Setup file logging
        self.logger = self._setup_logger()

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
        """Save the runs index"""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_path, 'w') as f:
            json.dump(self.index, f, indent=2)

    def start_run(self, dry_run: bool, structure_config: Dict) -> str:
        """Start a new run and return run_id"""
        timestamp = datetime.now().isoformat()
        run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create run directory structure
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True)
        (run_dir / 'operations').mkdir()
        
        # Create run metadata
        metadata = RunMetadata(
            run_id=run_id,
            timestamp=timestamp,
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
            "timestamp": timestamp,
            "status": "running",
            "dry_run": dry_run
        }
        self._save_index()
        
        return run_id

    def log_operation(self, operation: FileOperation):
        """Log a file operation"""
        run_dir = self.runs_dir / operation.run_id / 'operations'
        
        # Save operation to type-specific file
        op_file = run_dir / f'{operation.operation_type.value}s.json'
        
        # Append operation to file
        operations = []
        if op_file.exists():
            with open(op_file) as f:
                operations = json.load(f)
        
        operations.append(asdict(operation))
        
        with open(op_file, 'w') as f:
            json.dump(operations, f, indent=2)

    def complete_run(self, run_id: str, status: str = "completed"):
        """Mark a run as complete and calculate duration"""
        run_dir = self.runs_dir / run_id
        
        # Load metadata
        with open(run_dir / 'metadata.json') as f:
            metadata = RunMetadata(**json.load(f))
        
        # Update metadata
        metadata.status = status
        metadata.end_timestamp = datetime.now().isoformat()
        if metadata.timestamp:
            start_time = datetime.fromisoformat(metadata.timestamp)
            end_time = datetime.fromisoformat(metadata.end_timestamp)
            metadata.duration_seconds = (end_time - start_time).total_seconds()
        
        # Save updated metadata
        with open(run_dir / 'metadata.json', 'w') as f:
            json.dump(asdict(metadata), f, indent=2)
        
        # Update index
        self.index["runs"][run_id].update({
            "status": status,
            "end_timestamp": metadata.end_timestamp,
            "duration_seconds": metadata.duration_seconds
        })
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

    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('project_logger')
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not logger.handlers:
            # Create logs directory if it doesn't exist
            log_file = self.logs_dir / 'project.log'
            
            # File handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger