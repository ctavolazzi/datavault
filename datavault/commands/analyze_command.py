import click
from pathlib import Path
from ..analyzers.project_analyzer import ProjectAnalyzer
from ..utils.decorators import debug_calls

@click.command()
@click.argument('dataset_name')
@debug_calls
def analyze(dataset_name):
    """Analyze a specific dataset"""
    dataset_path = Path("datasets") / dataset_name
    
    if not dataset_path.exists():
        click.echo(f"Error: Dataset '{dataset_name}' not found")
        return
    
    analyzer = ProjectAnalyzer(dataset_path)
    stats = analyzer.get_basic_stats()
    file_types = analyzer.get_file_types()
    
    click.echo(f"\nAnalyzing dataset: {dataset_name}")
    click.echo("-" * 20)
    
    click.echo(f"Files found: {stats['total_files']}")
    click.echo(f"Total size: {stats['total_size_mb']:.2f} MB")
    
    click.echo("\nFile types:")
    for ext, count in file_types:
        click.echo(f"  {ext or 'no extension'}: {count} files")