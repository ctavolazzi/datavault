import click
from pathlib import Path
from ..utils.decorators import debug_calls

@click.command()
@click.option('--pattern', default='*', help='File pattern to match (e.g., *.py, *.md)')
@debug_calls
def find(pattern: str):
    """Find files that can be analyzed"""
    current_dir = Path.cwd()
    try:
        # Convert generator to list and filter for files only
        files = [f for f in current_dir.rglob(pattern) if f.is_file()]
        
        if not files:
            click.echo(f"No files matching '{pattern}' found")
            return
        
        click.echo(f"\nFound {len(files)} files matching '{pattern}':")
        click.echo("-" * 50)
        
        for file in sorted(files)[:10]:  # Show first 10 files, sorted
            size = file.stat().st_size / 1024  # KB
            click.echo(f"{file.relative_to(current_dir)} ({size:.1f} KB)")
        
        if len(files) > 10:
            click.echo(f"\n... and {len(files) - 10} more files")
            
    except Exception as e:
        click.echo(f"Error while searching: {str(e)}")