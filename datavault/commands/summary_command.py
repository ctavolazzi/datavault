import click
from pathlib import Path
import json
from datetime import datetime
from ..analyzers.project_analyzer import ProjectAnalyzer
from ..analyzers.dependency_analyzer import DependencyAnalyzer
from ..visualization.graph_generator import GraphGenerator
from ..utils.decorators import debug_calls

@click.command()
@click.option('--min-size', default=0, help='Minimum file size in KB to include')
@click.option('--type', 'file_type', help='Filter by file type (e.g., py, md, log)')
@click.option('--viz/--no-viz', default=False, help='Generate dependency visualization')
@click.option('--export', type=click.Choice(['json', 'csv']), help='Export format')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--theme', type=click.Choice(['light', 'dark']), default='light')
@debug_calls
def summary(min_size: int, file_type: str, viz: bool, export: str, 
           output: str, theme: str):
    """Show a summary of all files in the project"""
    current_dir = Path.cwd()
    analyzer = ProjectAnalyzer(current_dir)
    
    # Collect basic statistics
    stats = analyzer.get_basic_stats()
    file_types = analyzer.get_file_types()
    recent_activity = analyzer.get_recent_activity()
    concerns = analyzer.get_concerns()
    
    # Filter results if needed
    if min_size or file_type:
        click.echo(f"\nApplying filters:")
        if min_size:
            click.echo(f"- Minimum size: {min_size}KB")
        if file_type:
            click.echo(f"- File type: .{file_type}")
    
    # Display results
    _display_summary(stats, file_types, recent_activity, concerns)
    
    # Generate visualization if requested
    if viz and stats['python_files'] > 0:
        _generate_visualization(current_dir, theme)
    
    # Export if requested
    if export:
        _export_results(
            stats, file_types, recent_activity, concerns,
            export, output or f"summary_{datetime.now():%Y%m%d_%H%M%S}.{export}"
        )

def _display_summary(stats: dict, file_types: list, 
                    recent_activity: list, concerns: dict):
    """Display formatted summary information"""
    click.echo("\n📊 Project Summary")
    click.echo("=" * 50)
    
    # Basic stats
    click.echo(f"\n📁 Files and Directories:")
    click.echo(f"  Total Files: {stats['total_files']}")
    click.echo(f"  Total Directories: {stats['total_dirs']}")
    click.echo(f"  Python Files: {stats['python_files']}")
    click.echo(f"  Total Size: {stats['total_size_mb']:.2f} MB")
    
    # File types
    click.echo("\n📑 File Types:")
    for ext, count in file_types:
        click.echo(f"  {ext or 'no extension'}: {count} files")
    
    # Recent activity
    click.echo("\n🕒 Recent Activity:")
    for date, file in recent_activity:
        click.echo(f"  {date:%Y-%m-%d %H:%M} - {file.name}")
    
    # Concerns
    if any(concerns.values()):
        click.echo("\n⚠️  Potential Concerns:")
        if concerns['large_files']:
            click.echo("  Large files (>1MB):")
            for file in concerns['large_files']:
                size_mb = file.stat().st_size / (1024 * 1024)
                click.echo(f"  - {file.name} ({size_mb:.1f}MB)")
        if concerns['empty_dirs']:
            click.echo("  Empty directories:")
            for dir in concerns['empty_dirs']:
                click.echo(f"  - {dir.relative_to(Path.cwd())}")

def _generate_visualization(project_dir: Path, theme: str):
    """Generate dependency visualization"""
    click.echo("\n📊 Generating dependency visualization...")
    
    # Get Python files
    py_files = list(project_dir.rglob("*.py"))
    
    # Analyze dependencies
    dep_analyzer = DependencyAnalyzer(py_files)
    dependencies = dep_analyzer.analyze_dependencies()
    
    # Generate graph
    graph_gen = GraphGenerator(theme=theme)
    fig = graph_gen.generate_graph(dependencies)
    
    if fig:
        output_path = project_dir / "dependency_graph.png"
        fig.savefig(output_path, bbox_inches='tight', facecolor=fig.get_facecolor())
        click.echo(f"Graph saved to: {output_path}")
    else:
        click.echo("No dependencies found to visualize")

def _export_results(stats: dict, file_types: list, recent_activity: list,
                   concerns: dict, format: str, output: str):
    """Export results in the specified format"""
    click.echo(f"\n📤 Exporting results to {output}...")
    
    # Prepare data
    export_data = {
        'stats': stats,
        'file_types': dict(file_types),
        'recent_activity': [
            {'date': date.isoformat(), 'file': str(file)}
            for date, file in recent_activity
        ],
        'concerns': {
            'large_files': [str(f) for f in concerns['large_files']],
            'empty_dirs': [str(d) for d in concerns['empty_dirs']]
        }
    }
    
    # Export based on format
    if format == 'json':
        with open(output, 'w') as f:
            json.dump(export_data, f, indent=2)
    elif format == 'csv':
        import csv
        with open(output, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Category', 'Metric', 'Value'])
            
            # Write stats
            for key, value in stats.items():
                writer.writerow(['Stats', key, value])
            
            # Write file types
            for ext, count in file_types:
                writer.writerow(['FileTypes', ext or 'no extension', count])
            
            # Write recent activity
            for date, file in recent_activity:
                writer.writerow(['RecentActivity', date.isoformat(), str(file)])
    
    click.echo(f"Results exported to: {output}")