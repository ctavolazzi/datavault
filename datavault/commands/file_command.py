import click
from pathlib import Path
from ..analyzers.file_analyzer import FileAnalyzer
from ..utils.formatters import format_file_info

@click.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--hash/--no-hash', default=False, help='Calculate file hash')
@click.option('--preview/--no-preview', default=False, help='Show file preview')
@click.option('--encoding', default='utf-8', help='File encoding')
def file(filepath: str, hash: bool, preview: bool, encoding: str):
    """Analyze a specific file"""
    analyzer = FileAnalyzer(encoding=encoding)
    info = analyzer.analyze(Path(filepath), calculate_hash=hash)
    
    if preview:
        info['preview'] = analyzer.get_preview(Path(filepath))
    
    click.echo(format_file_info(info)) 