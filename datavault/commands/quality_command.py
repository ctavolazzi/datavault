import click
from pathlib import Path
from collections import defaultdict
from ..analysis.code_quality import CodeQualityAnalyzer, ResultFormatter

def quality_command(complexity: bool, duplication: bool, lint: bool, 
                   threshold: int, format: str):
    """Analyze code quality metrics"""
    current_dir = Path.cwd()
    py_files = list(current_dir.rglob("*.py"))
    
    if not py_files:
        click.echo("No Python files found")
        return
    
    click.echo("\n📊 Code Quality Analysis")
    click.echo("=" * 50)
    
    analyzer = CodeQualityAnalyzer(threshold=threshold)
    results = defaultdict(dict)
    
    # Analyze each file
    with click.progressbar(py_files, label='Analyzing files') as files:
        for file in files:
            rel_path = file.relative_to(current_dir)
            file_results = analyzer.analyze_file(file)
            
            # Filter results based on options
            if not complexity:
                file_results.pop('complexity', None)
            if not duplication:
                file_results.pop('duplication', None)
            if not lint:
                file_results.pop('lint', None)
                
            results[str(rel_path)] = file_results
    
    # Format and display results
    formatter = ResultFormatter()
    output = formatter.format_results(results, threshold, format)
    click.echo(output) 