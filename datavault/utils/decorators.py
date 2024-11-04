import functools
import click

def debug_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        click.echo(f"Calling: {func.__name__}")
        result = func(*args, **kwargs)
        click.echo(f"Finished: {func.__name__}")
        return result
    return wrapper 