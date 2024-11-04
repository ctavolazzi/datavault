import click
import time
from typing import Iterable, Any, Optional
from contextlib import contextmanager

class ProgressTracker:
    """Handle progress reporting for long-running operations"""
    
    def __init__(self, total: int = None, message: str = None):
        self.total = total
        self.current = 0
        self.message = message
        self.start_time = None
        
    def start(self, message: Optional[str] = None):
        """Start the progress tracking"""
        self.start_time = time.time()
        self.message = message or self.message
        if self.message:
            click.echo(f"\n{self.message}")
    
    def update(self, amount: int = 1):
        """Update progress"""
        self.current += amount
        if self.total:
            percentage = (self.current / self.total) * 100
            click.echo(f"\rProgress: {percentage:.1f}% ({self.current}/{self.total})", nl=False)
    
    def finish(self, message: Optional[str] = None):
        """Complete the progress tracking"""
        duration = time.time() - self.start_time
        click.echo(f"\nCompleted in {duration:.2f} seconds")
        if message:
            click.echo(message)

@contextmanager
def track_progress(iterable: Iterable[Any], message: str = None) -> Iterable[Any]:
    """Context manager for tracking progress of an iterable"""
    tracker = ProgressTracker(total=len(list(iterable)), message=message)
    tracker.start()
    try:
        yield tracker
    finally:
        tracker.finish() 