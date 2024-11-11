from typing import Optional
import click

class DatavaultError(Exception):
    """Base exception class for Datavault"""
    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code or 1
        super().__init__(self.message)

class ConfigurationError(DatavaultError):
    """Raised when there's a configuration issue"""
    pass

class APIError(DatavaultError):
    """Raised when there's an API-related issue"""
    pass

class FileError(DatavaultError):
    """Raised when there's a file-related issue"""
    pass

def handle_error(func):
    """Decorator for handling errors in commands"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DatavaultError as e:
            click.secho(f"Error: {e.message}", fg='red', err=True)
            return e.code
        except Exception as e:
            click.secho(f"Unexpected error: {str(e)}", fg='red', err=True)
            return 1
    return wrapper