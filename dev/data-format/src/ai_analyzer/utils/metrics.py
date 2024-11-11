import time
import psutil
import logging
from functools import wraps
from typing import Dict, Any
from datetime import datetime

def get_system_metrics() -> Dict[str, Any]:
    """Get detailed system metrics"""
    process = psutil.Process()
    memory = process.memory_info()

    return {
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        },
        "process": {
            "memory_rss": f"{memory.rss / 1024 / 1024:.2f}MB",
            "memory_vms": f"{memory.vms / 1024 / 1024:.2f}MB",
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads(),
            "open_files": len(process.open_files())
        },
        "timestamp": datetime.now().isoformat()
    }

def track_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(f'datavault.metrics.{func.__name__}')

        # Pre-execution metrics
        start_time = time.perf_counter()
        start_metrics = get_system_metrics()

        try:
            # Execute function
            result = func(*args, **kwargs)

            # Post-execution metrics
            end_time = time.perf_counter()
            end_metrics = get_system_metrics()

            # Calculate performance metrics
            metrics = {
                "execution": {
                    "duration_seconds": f"{end_time - start_time:.4f}",
                    "success": True,
                    "start_time": start_metrics["timestamp"],
                    "end_time": end_metrics["timestamp"]
                },
                "resources": {
                    "memory_delta": f"{float(end_metrics['process']['memory_rss'].replace('MB', '')) - float(start_metrics['process']['memory_rss'].replace('MB', '')):.2f}MB",
                    "cpu_usage": f"{end_metrics['process']['cpu_percent']:.2f}%",
                    "final_memory": end_metrics['process']['memory_rss']
                }
            }

            logger.debug("Performance metrics", extra={"metrics": metrics})
            return result

        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}",
                        extra={"metrics": {"execution": {"success": False}}},
                        exc_info=True)
            raise

    return wrapper