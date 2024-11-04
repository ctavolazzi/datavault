import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import pytest
from project_manager.log_manager import ProjectLogger, RunMetadata, FileOperation, OperationType
import json
import threading

def test_logger_initialization(tmp_path):
    """Test basic logger initialization"""
    logger = ProjectLogger(tmp_path)
    
    # Check directory structure
    assert (tmp_path / "logs").exists()
    assert (tmp_path / "logs" / "runs").exists()
    
    # Test basic logging
    run_id = logger.start_run(dry_run=True, structure_config={})
    assert (tmp_path / "logs" / "runs" / run_id).exists()

def test_basic_operation_logging(tmp_path):
    """Test logging a simple operation"""
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Log a test operation
    test_op = FileOperation(
        run_id=run_id,
        timestamp="2024-03-11T12:00:00",
        operation_type=OperationType.MOVE,
        source="/test/source",
        target="/test/target",
        success=True
    )
    
    logger.log_operation(test_op)
    
    # Verify operation was logged
    ops_file = tmp_path / "logs" / "runs" / run_id / "operations" / "moves.json"
    assert ops_file.exists()
    
    # Verify content
    with open(ops_file) as f:
        operations = json.load(f)
        assert len(operations) == 1
        assert operations[0]["operation_type"] == "move"
        assert operations[0]["source"] == "/test/source"
        assert operations[0]["target"] == "/test/target"
        assert operations[0]["success"] is True

def test_multiple_operations(tmp_path):
    """Test logging multiple operations"""
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Log multiple operations of different types
    operations = [
        FileOperation(
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            operation_type=OperationType.ANALYZE,
            source="/test/file1",
            target="/test/dest1",
            success=True
        ),
        FileOperation(
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            operation_type=OperationType.MOVE,
            source="/test/file2",
            target="/test/dest2",
            success=False,
            error="Permission denied"
        )
    ]
    
    for op in operations:
        logger.log_operation(op)
    
    # Verify separate files for different operation types
    assert (tmp_path / "logs" / "runs" / run_id / "operations" / "analyzes.json").exists()
    assert (tmp_path / "logs" / "runs" / run_id / "operations" / "moves.json").exists()

def test_run_metadata(tmp_path):
    """Test run metadata handling"""
    logger = ProjectLogger(tmp_path)
    config = {"test": "config"}
    run_id = logger.start_run(dry_run=True, structure_config=config)
    
    # Check metadata file content
    with open(tmp_path / "logs" / "runs" / run_id / "metadata.json") as f:
        metadata = json.load(f)
        assert metadata["dry_run"] is True
        assert metadata["structure_config"] == config
        assert metadata["status"] == "running"
        assert "timestamp" in metadata
        assert "python_version" in metadata
        assert "system" in metadata

def test_index_updates(tmp_path):
    """Test that the index file is properly updated"""
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Check index file
    with open(tmp_path / "logs" / "index.json") as f:
        index = json.load(f)
        assert run_id in index["runs"]
        assert index["runs"][run_id]["status"] == "running"
        assert index["runs"][run_id]["dry_run"] is True

def test_failed_operation_logging(tmp_path):
    """Test logging failed operations with error messages"""
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Log a failed operation
    failed_op = FileOperation(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        operation_type=OperationType.MOVE,
        source="/test/source",
        target="/test/target",
        success=False,
        error="Permission denied",
        metadata={"attempt": 1, "user": "test"}
    )
    
    logger.log_operation(failed_op)
    
    # Verify error details are logged
    ops_file = tmp_path / "logs" / "runs" / run_id / "operations" / "moves.json"
    with open(ops_file) as f:
        operations = json.load(f)
        assert len(operations) == 1
        assert operations[0]["success"] is False
        assert operations[0]["error"] == "Permission denied"
        assert operations[0]["metadata"]["attempt"] == 1

def test_concurrent_runs(tmp_path):
    """Test handling multiple runs simultaneously"""
    logger = ProjectLogger(tmp_path)
    
    # Start multiple runs
    run_ids = [
        logger.start_run(dry_run=True, structure_config={})
        for _ in range(3)
    ]
    
    # Verify each run has its own directory
    for run_id in run_ids:
        assert (tmp_path / "logs" / "runs" / run_id).exists()
        assert (tmp_path / "logs" / "runs" / run_id / "operations").exists()
    
    # Verify runs are tracked in index
    with open(tmp_path / "logs" / "index.json") as f:
        index = json.load(f)
        for run_id in run_ids:
            assert run_id in index["runs"]

def test_invalid_operation_handling(tmp_path):
    """Test handling invalid operations"""
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Test with missing required fields
    with pytest.raises(ValueError):
        invalid_op = FileOperation(
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            operation_type=OperationType.MOVE,
            source="",  # Empty source
            target="/test/target",
            success=True
        )
        logger.log_operation(invalid_op)

def test_run_completion(tmp_path):
    """Test completing a run and updating its status"""
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Complete the run
    logger.complete_run(run_id, status="completed")
    
    # Verify metadata and index are updated
    with open(tmp_path / "logs" / "runs" / run_id / "metadata.json") as f:
        metadata = json.load(f)
        assert metadata["status"] == "completed"
        assert metadata["end_timestamp"] is not None
        assert metadata["duration_seconds"] is not None
    
    with open(tmp_path / "logs" / "index.json") as f:
        index = json.load(f)
        assert index["runs"][run_id]["status"] == "completed"

def test_large_metadata_handling(tmp_path):
    """Test handling large metadata objects"""
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Create operation with large metadata
    large_metadata = {
        "files": [f"file_{i}" for i in range(1000)],
        "stats": {f"stat_{i}": i for i in range(100)},
        "nested": {"level1": {"level2": {"level3": "deep"}}}
    }
    
    op = FileOperation(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        operation_type=OperationType.ANALYZE,
        source="/test/source",
        target="/test/dest",
        success=True,
        metadata=large_metadata
    )
    
    logger.log_operation(op)
    
    # Verify operation was logged
    ops_file = tmp_path / "logs" / "runs" / run_id / "operations" / "analyzes.json"
    assert ops_file.exists()
    
    # Verify content
    with open(ops_file) as f:
        operations = json.load(f)
        assert len(operations) == 1
        assert operations[0]["operation_type"] == "analyze"
        assert operations[0]["source"] == "/test/source"
        assert operations[0]["target"] == "/test/dest"
        assert operations[0]["success"] is True
        assert operations[0]["metadata"] == large_metadata

def test_run_recovery(tmp_path):
    """Test recovery of interrupted runs"""
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Simulate crash by not completing the run
    del logger
    
    # Create new logger instance
    new_logger = ProjectLogger(tmp_path)
    
    # Should be able to complete the interrupted run
    new_logger.complete_run(run_id, status="failed")
    
    # Verify run was marked as failed
    with open(tmp_path / "logs" / "runs" / run_id / "metadata.json") as f:
        metadata = json.load(f)
        assert metadata["status"] == "failed"

def test_operation_validation(tmp_path):
    """Test comprehensive operation validation"""
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Test various invalid operations
    invalid_cases = [
        # Empty source
        ({"source": ""}, "Source path cannot be empty"),
        # Empty target
        ({"target": ""}, "Target path cannot be empty"),
        # Invalid operation type
        ({"operation_type": "INVALID"}, "Invalid operation type"),
    ]
    
    for invalid_fields, expected_error in invalid_cases:
        base_op = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "operation_type": OperationType.MOVE,
            "source": "/test/source",
            "target": "/test/target",
            "success": True
        }
        # Update with invalid fields
        base_op.update(invalid_fields)
        
        with pytest.raises(ValueError, match=expected_error):
            op = FileOperation(**base_op)
            logger.log_operation(op)

def test_index_consistency(tmp_path):
    """Test index file consistency across logger instances"""
    # First logger instance
    logger1 = ProjectLogger(tmp_path)
    run_id1 = logger1.start_run(dry_run=True, structure_config={})
    
    # Second logger instance
    logger2 = ProjectLogger(tmp_path)
    run_id2 = logger2.start_run(dry_run=False, structure_config={})
    
    # Third logger instance should see both runs
    logger3 = ProjectLogger(tmp_path)
    with open(tmp_path / "logs" / "index.json") as f:
        index = json.load(f)
        assert run_id1 in index["runs"]
        assert run_id2 in index["runs"]
        assert index["runs"][run_id1]["dry_run"] is True
        assert index["runs"][run_id2]["dry_run"] is False

def test_error_operation_logging(tmp_path):
    """Test logging error operations"""
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Log an error operation
    error_op = FileOperation(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        operation_type=OperationType.ERROR,
        source="system",
        target="file_processing",
        success=False,
        error="Stack trace...",
        metadata={
            "exception_type": "FileNotFoundError",
            "stack_trace": "detailed stack trace...",
            "context": {"file": "test.txt"}
        }
    )
    
    logger.log_operation(error_op)
    
    # Verify error was logged properly
    error_file = tmp_path / "logs" / "runs" / run_id / "operations" / "errors.json"
    assert error_file.exists()
    with open(error_file) as f:
        errors = json.load(f)
        assert len(errors) == 1
        assert errors[0]["error"] == "Stack trace..."
        assert errors[0]["metadata"]["exception_type"] == "FileNotFoundError"

def test_performance_large_volume(tmp_path):
    """Test logging performance with large volume of operations"""
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Create operations
    operations = [
        FileOperation(
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            operation_type=OperationType.MOVE,
            source=f"/source/file_{i}",
            target=f"/target/file_{i}",
            success=True,
            metadata={"index": i}
        )
        for i in range(1000)
    ]
    
    # Log operations in batch
    start_time = datetime.now()
    logger.log_operations_batch(operations)
    duration = (datetime.now() - start_time).total_seconds()
    
    assert duration < 5.0  # Should complete within 5 seconds

def test_concurrent_write_safety(tmp_path):
    """Test concurrent write safety with multiple loggers"""
    def log_operations(logger, run_id, count):
        for i in range(count):
            op = FileOperation(
                run_id=run_id,
                timestamp=datetime.now().isoformat(),
                operation_type=OperationType.ANALYZE,
                source=f"/test/source_{i}",
                target=f"/test/target_{i}",
                success=True
            )
            logger.log_operation(op)
    
    logger = ProjectLogger(tmp_path)
    run_id = logger.start_run(dry_run=True, structure_config={})
    
    # Create multiple threads logging operations
    threads = []
    for i in range(3):
        t = threading.Thread(
            target=log_operations,
            args=(logger, run_id, 100)
        )
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    # Verify all operations were logged
    ops_file = tmp_path / "logs" / "runs" / run_id / "operations" / "analyzes.json"
    with open(ops_file) as f:
        operations = json.load(f)
        assert len(operations) == 300  # 3 threads * 100 operations

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

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 