import click
from pathlib import Path
from ..analyzers.project_analyzer import ProjectAnalyzer

@click.command()
def welcome():
    """Show a friendly welcome message with suggested next steps"""
    click.echo("\n🗄️  Welcome to DataVault!")
    click.echo("Your Swiss Army knife for file analysis\n")
    click.echo("-" * 50)
    
    # Get current directory stats
    analyzer = ProjectAnalyzer(Path.cwd())
    stats = analyzer.get_basic_stats()
    file_types = analyzer.get_file_types(top_n=3)
    
    click.echo(f"\n📁 Current directory: {Path.cwd().name}")
    click.echo(f"   {stats['total_files']} files, {stats['total_dirs']} directories")
    
    # Show top 3 file types if any
    if file_types:
        click.echo("\n📊 Quick Analysis:")
        for ext, count in file_types:
            click.echo(f"   {ext}: {count} files")
    
    click.echo("\n🚀 Quick Start:")
    click.echo("1. Get an overview:")
    click.echo("   datavault summary\n")
    
    click.echo("2. Find specific files:")
    click.echo("   datavault find --pattern '*.py'")
    click.echo("   datavault find --pattern '*.md'\n")
    
    click.echo("3. Analyze a file:")
    click.echo("   datavault file <filename> --preview\n")
    
    click.echo("4. Export your analysis:")
    click.echo("   datavault summary --export json\n")
    
    click.echo("📚 For more details:")
    click.echo("   datavault --help")
    click.echo("   datavault <command> --help\n")