from pathlib import Path
import click
from ..analyzers.project_analyzer import ProjectAnalyzer
from ..formatters.status_formatter import StatusFormatter

def status_command():
    """Show current project status and quick metrics"""
    current_dir = Path.cwd()
    
    # Initialize analyzer and formatter
    analyzer = ProjectAnalyzer(current_dir)
    formatter = StatusFormatter()
    
    # Get project statistics
    click.echo("\n🗄️  Project Overview")
    click.echo("=" * 50)
    
    # Basic stats
    stats = analyzer.get_basic_stats()
    stats['project_name'] = current_dir.name
    click.echo(formatter.format_project_overview(stats))
    
    # File types
    file_types = analyzer.get_file_types(top_n=5)
    click.echo(formatter.format_file_types(file_types))
    
    # Recent activity
    recent_activity = analyzer.get_recent_activity(limit=5)
    click.echo(formatter.format_recent_activity(recent_activity))
    
    # Quick actions
    click.echo(formatter.format_quick_actions(stats['python_files'] > 0))
    
    # Concerns
    concerns = analyzer.get_concerns(size_threshold_mb=1)
    click.echo(formatter.format_concerns(concerns)) 