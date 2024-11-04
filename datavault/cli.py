import click
from .commands import (
    welcome_command,
    status_command,
    analyze_command,
    find_command,
    file_command,
    summary_command,
    quality_command
)

@click.group()
def cli():
    """DataVault: Analyze and understand your files and directories."""
    pass

# Register commands
cli.add_command(welcome_command.welcome)
cli.add_command(status_command.status)
cli.add_command(analyze_command.analyze)
cli.add_command(find_command.find)
cli.add_command(file_command.file)
cli.add_command(summary_command.summary)
cli.add_command(quality_command.quality)

def main():
    cli()

if __name__ == "__main__":
    main() 
import os
from pathlib import Path
from datetime import datetime, timedelta
import magic  # for file type detection
import hashlib  # for file hashing
from typing import Dict, Any
from PIL import Image  # for image analysis
import mimetypes
import imghdr
import zipfile
import ast
import pkg_resources
import pycodestyle
from collections import defaultdict
import json
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import sys
import functools
from .commands.quality_command import quality_command

@click.group()
def cli():
    """DataVault: Analyze and understand your files and directories.
    
    Common commands to get started:
    
    \b
    📊 Quick Analysis:
        datavault summary            Show overview of current directory
        datavault summary --deep     Include detailed file analysis
    
    \b
    🔍 Find Files:
        datavault find --pattern "*.py"    Find Python files
        datavault find --pattern "*.md"    Find documentation
    
    \b
    📄 File Analysis:
        datavault file README.md --preview    View file details
        datavault file script.py --hash       Get file hash
    
    \b
    💾 Export Data:
        datavault summary --export json    Save analysis as JSON
        datavault summary --export csv     Save analysis as CSV
    """
    pass

@cli.command()
def welcome():
    """Show a friendly welcome message with suggested next steps"""
    click.echo("\n🗄️  Welcome to DataVault!")
    click.echo("Your Swiss Army knife for file analysis\n")
    click.echo("-" * 50)
    
    # Get current directory stats
    current_dir = Path.cwd()
    file_count = 0
    dir_count = 0
    extensions = {}
    
    # Count files, directories, and extensions
    for item in current_dir.iterdir():
        if item.is_file():
            file_count += 1
            ext = item.suffix.lower() or 'no extension'
            extensions[ext] = extensions.get(ext, 0) + 1
        elif item.is_dir():
            dir_count += 1
    
    click.echo(f"\n📁 Current directory: {current_dir.name}")
    click.echo(f"   {file_count} files, {dir_count} directories")
    
    # Show top 3 file types if any
    if extensions:
        click.echo("\n📊 Quick Analysis:")
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:3]:
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

@cli.command()
def status():
    """Show the current status of DataVault"""
    click.echo("DataVault Status:")
    click.echo("-" * 20)
    
    # Check data directories
    data_dir = Path("datasets")
    if data_dir.exists():
        click.echo(f"✓ Data directory: {data_dir}")
        click.echo(f"  - Space used: {get_dir_size(data_dir):.2f} MB")
    else:
        click.echo("✗ Data directory not found")
    
    # Check last modified time
    if data_dir.exists():
        last_modified = datetime.fromtimestamp(data_dir.stat().st_mtime)
        click.echo(f"Last modified: {last_modified:%Y-%m-%d %H:%M:%S}")

@cli.command()
@click.argument('dataset_name')
def analyze(dataset_name):
    """Analyze a specific dataset"""
    dataset_path = Path("datasets") / dataset_name
    
    if not dataset_path.exists():
        click.echo(f"Error: Dataset '{dataset_name}' not found")
        return
    
    click.echo(f"Analyzing dataset: {dataset_name}")
    click.echo("-" * 20)
    
    # Basic dataset analysis
    files = list(dataset_path.glob("*"))
    click.echo(f"Files found: {len(files)}")
    click.echo(f"Total size: {get_dir_size(dataset_path):.2f} MB")
    
    # Show file types
    extensions = {}
    for f in files:
        ext = f.suffix
        extensions[ext] = extensions.get(ext, 0) + 1
    
    click.echo("\nFile types:")
    for ext, count in extensions.items():
        click.echo(f"  {ext or 'no extension'}: {count} files")

def debug_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        click.echo(f"Calling: {func.__name__}")
        result = func(*args, **kwargs)
        click.echo(f"Finished: {func.__name__}")
        return result
    return wrapper

@cli.command(name='list-datasets')
@debug_calls
def list_datasets():
    """List all available datasets"""
    click.echo("Starting list command")
    data_dir = Path("datasets")
    
    if not data_dir.exists():
        click.echo("No datasets directory found")
        return
    
    try:
        datasets = [d for d in data_dir.glob("*") if d.is_dir()]
        
        if not datasets:
            click.echo("No datasets found")
            return
        
        click.echo("\nAvailable datasets:")
        for dataset in sorted(datasets):
            size = sum(f.stat().st_size for f in dataset.glob("*") if f.is_file()) / (1024 * 1024)
            files = sum(1 for _ in dataset.glob("*") if _.is_file())
            click.echo(f"- {dataset.name}")
            click.echo(f"  Size: {size:.2f} MB")
            click.echo(f"  Files: {files}")
                
    except Exception as e:
        click.echo(f"Error listing datasets: {str(e)}")

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--hash/--no-hash', default=False, help='Calculate file hash (may be slow for large files)')
@click.option('--preview/--no-preview', default=False, help='Show file preview (first few lines)')
@click.option('--encoding', default='utf-8', help='File encoding (e.g., utf-8, utf-16)')
def file(filepath: str, hash: bool, preview: bool, encoding: str):
    """Analyze a specific file"""
    path = Path(filepath)
    
    click.echo(f"\nFile Analysis: {path.name}")
    click.echo("-" * 50)
    
    info = analyze_file(path, calculate_hash=hash, encoding=encoding)
    
    # Display results
    for key, value in info.items():
        click.echo(f"{key}: {value}")
    
    if preview:
        click.echo("\nPreview:")
        click.echo("-" * 50)
        try:
            with open(path, 'r', encoding=encoding) as f:
                lines = f.readlines()[:5]  # First 5 lines
                for line in lines:
                    click.echo(line.rstrip())
        except UnicodeDecodeError:
            click.echo("Cannot preview: file appears to be binary")

def analyze_file(path: Path, calculate_hash: bool = False, encoding: str = 'utf-8') -> Dict[str, Any]:
    """Analyze a file and return its properties"""
    stats = path.stat()
    mime_type = magic.from_file(str(path), mime=True)
    
    info = {
        "Size": f"{stats.st_size / 1024:.2f} KB",
        "Created": datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
        "Modified": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        "Type": magic.from_file(str(path)),
        "MIME": mime_type,
        "Extension": path.suffix or "No extension",
        "Permissions": oct(stats.st_mode)[-3:],
        "Path": str(path.absolute())
    }
    
    if calculate_hash:
        info["MD5"] = calculate_file_hash(path)
    
    # Handle different file types
    main_type = mime_type.split('/')[0]
    
    if main_type == "text":
        analyze_text_file(path, info, encoding)
    elif main_type == "image":
        analyze_image_file(path, info)
    elif mime_type == "application/pdf":
        analyze_pdf_file(path, info)
    elif mime_type in ["application/zip", "application/x-zip-compressed"]:
        analyze_zip_file(path, info)
    
    return info

def analyze_text_file(path: Path, info: Dict[str, Any], encoding: str):
    """Analyze text files"""
    try:
        with open(path, 'r', encoding=encoding) as f:
            lines = f.readlines()
            info["Lines"] = len(lines)
            info["Characters"] = sum(len(line) for line in lines)
            info["Encoding"] = encoding
            
            # Count non-empty lines
            info["Non-empty Lines"] = sum(1 for line in lines if line.strip())
            
            # Detect programming language
            if path.suffix in ['.py', '.js', '.java', '.cpp', '.cs']:
                info["Language"] = path.suffix[1:].upper()
    except UnicodeDecodeError:
        try:
            with open(path, 'r', encoding='utf-16') as f:
                lines = f.readlines()
                info["Lines"] = len(lines)
                info["Characters"] = sum(len(line) for line in lines)
                info["Encoding"] = 'utf-16'
        except UnicodeDecodeError:
            info["Note"] = "File encoding could not be determined"

def analyze_image_file(path: Path, info: Dict[str, Any]):
    """Analyze image files"""
    try:
        with Image.open(path) as img:
            info["Dimensions"] = f"{img.width}x{img.height}"
            info["Mode"] = img.mode
            info["Format"] = img.format
            
            if hasattr(img, 'info'):
                if 'dpi' in img.info:
                    info["DPI"] = img.info['dpi']
                if 'exif' in img.info:
                    info["Has EXIF"] = "Yes"
    except Exception as e:
        info["Note"] = f"Error analyzing image: {str(e)}"

def analyze_zip_file(path: Path, info: Dict[str, Any]):
    """Analyze zip files"""
    try:
        with zipfile.ZipFile(path) as zf:
            files = zf.namelist()
            info["Files in Archive"] = len(files)
            info["Compressed Size"] = f"{sum(zi.compress_size for zi in zf.filelist) / 1024:.2f} KB"
            info["Uncompressed Size"] = f"{sum(zi.file_size for zi in zf.filelist) / 1024:.2f} KB"
            
            # List first 5 files
            if files:
                info["Contents (first 5)"] = ", ".join(files[:5])
    except Exception as e:
        info["Note"] = f"Error analyzing zip: {str(e)}"

def calculate_file_hash(path: Path) -> str:
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_dir_size(path: Path) -> float:
    """Get directory size in MB"""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = Path(dirpath) / f
            if fp.exists():
                total += fp.stat().st_size
    return total / (1024 * 1024)  # Convert to MB

@cli.command()
@click.option('--pattern', default='*', help='File pattern to match (e.g., *.py, *.md)')
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

def format_dependency_path(path: str) -> str:
    """Format a file path for display in dependency summary"""
    # Convert Windows paths to forward slashes for display
    return str(Path(path)).replace('\\', '/')

def deduplicate_dependencies(deps: dict) -> dict:
    """Remove duplicate dependencies and sort them"""
    clean_deps = {}
    for source, targets in deps.items():
        # Convert to set to remove duplicates, then back to sorted list
        clean_deps[source] = sorted(set(targets))
    return dict(sorted(clean_deps.items()))

def clean_dependencies(deps: dict, files: list, debug: bool = False) -> dict:
    """Clean and filter dependencies"""
    if debug:
        click.echo("\nCleaning dependencies...")
    
    # Convert all paths to strings for consistent comparison
    current_dir = Path.cwd()
    file_paths = {str(f.relative_to(current_dir)) for f in files}
    
    # Clean up dependencies
    clean_deps = {}
    for source, targets in deps.items():
        # Skip build directory files
        if 'build' in Path(source).parts:
            if debug:
                click.echo(f"Skipping build file: {source}")
            continue
        
        # Source is already relative, just normalize it
        source_path = str(Path(source))
        if source_path not in file_paths:
            if debug:
                click.echo(f"Skipping non-filtered file: {source}")
            continue
        
        # Filter and clean target paths
        clean_targets = []
        for target in targets:
            target_path = str(Path(target))
            if target_path in file_paths and 'build' not in Path(target).parts:
                clean_targets.append(target_path)
            elif debug:
                click.echo(f"Skipping target: {target}")
        
        if clean_targets:
            clean_deps[source_path] = sorted(set(clean_targets))
    
    if debug:
        click.echo(f"\nFound {len(clean_deps)} files with dependencies after cleaning")
        for source, targets in clean_deps.items():
            click.echo(f"  {source} -> {targets}")
    
    return clean_deps

@cli.command()
@click.option('--min-size', default=0, help='Minimum file size in KB to include')
@click.option('--type', 'file_type', help='Filter by file type (e.g., py, md, log)')
@click.option('--viz/--no-viz', default=False, help='Generate dependency visualization')
@click.option('--viz-format', type=click.Choice(['png', 'svg', 'pdf']), default='png')
@click.option('--viz-style', type=click.Choice(['spring', 'circular', 'shell']), default='spring')
@click.option('--viz-theme', type=click.Choice(['light', 'dark']), default='light')
@click.option('--output-dir', default='datavault_output', help='Output directory')
@click.option('--debug/--no-debug', default=False, help='Show debug output')
def summary(min_size: int, file_type: str, viz: bool, viz_format: str, viz_style: str, 
           viz_theme: str, output_dir: str, debug: bool):
    """Show a summary of all files in the project"""
    if debug:
        click.echo(click.style("\nDebug Mode Enabled", fg='yellow'))
        click.echo("=" * 50)
    
    current_dir = Path.cwd()
    
    # Initialize counters
    total_files = 0
    total_size = 0
    extensions = defaultdict(lambda: {'count': 0, 'size': 0})
    filtered_files = []  # Keep track of filtered files
    
    # Scan files
    for file in current_dir.rglob("*"):
        if file.is_file():
            size = file.stat().st_size / 1024  # KB
            if size < min_size:
                continue
                
            ext = file.suffix.lstrip('.') or "no extension"
            if file_type and ext != file_type:
                continue
            
            total_files += 1
            total_size += size
            extensions[ext]['count'] += 1
            extensions[ext]['size'] += size
            filtered_files.append(file)  # Add to filtered list
    
    # Display basic stats
    click.echo(f"\nTotal Files: {total_files}")
    click.echo(f"Total Size: {total_size / 1024:.2f} MB\n")
    
    if extensions:
        click.echo("File Types:")
        for ext, stats in sorted(extensions.items(), key=lambda x: x[1]['size'], reverse=True):
            size_mb = stats['size'] / 1024
            percentage = (stats['size'] / total_size) * 100
            click.echo(f"  {ext:<12} {stats['count']:>3} files ({size_mb:>6.2f} MB) {percentage:>5.1f}%")
    
    if viz and extensions.get('py', {}).get('count', 0) > 0:
        click.echo("\nGenerating visualization...")
        
        # Create output directory
        viz_dir = Path(output_dir) / 'visualizations'
        viz_dir.mkdir(parents=True, exist_ok=True)
        
        if debug:
            click.echo(f"Output directory: {viz_dir}")
            click.echo("\nFiltered files:")
            for f in filtered_files:
                click.echo(f"  {f.relative_to(current_dir)}")
        
        # Use filtered files
        py_files = [f for f in filtered_files if f.suffix == '.py']
        if debug:
            click.echo(f"\nFound {len(py_files)} Python files")
        
        # Analyze dependencies
        internal_deps, _ = analyze_dependencies(py_files, debug=debug)
        
        if internal_deps:
            # Clean and filter dependencies
            clean_deps = clean_dependencies(internal_deps, py_files, debug=debug)
            
            if clean_deps:
                # Show dependency summary
                click.echo("\nDependency Summary:")
                click.echo("-" * 50)
                
                for source, targets in sorted(clean_deps.items()):
                    source_name = format_dependency_path(source)
                    target_names = [format_dependency_path(t) for t in targets]
                    click.echo(f"  {source_name:<40} → {', '.join(target_names)}")
                
                click.echo(f"\nTotal: {len(clean_deps)} files with dependencies")
                
                # Generate graph
                plt = generate_dependency_graph(py_files, clean_deps, 
                                             viz_theme, viz_style, viz_format,
                                             debug=debug)
                if plt:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = viz_dir / f'dependency_graph_{timestamp}.{viz_format}'
                    
                    if debug:
                        click.echo(f"\nSaving visualization to: {filename}")
                    
                    plt.savefig(filename,
                               bbox_inches='tight',
                               dpi=300,
                               facecolor='white' if viz_theme == 'light' else '#1c1c1c',
                               edgecolor='none')
                    plt.close()
                    
                    click.echo(click.style(
                        f"\n✓ Visualization saved: {filename}",
                        fg='green'
                    ))
            else:
                click.echo("\nNo dependencies found between filtered files")
        else:
            click.echo("\nNo dependencies found to visualize")

@debug_calls
def analyze_dependencies(files, debug=False):
    """Analyze internal and external dependencies"""
    if debug:
        click.echo("Starting dependency analysis")
    
    internal_deps = {}
    external_deps = {}
    
    # Create a mapping of module names to file paths
    module_map = {}
    for file in files:
        module_name = file.stem
        # Store both absolute and relative paths
        module_map[module_name] = {
            'abs': str(file.absolute()),
            'rel': str(file.relative_to(Path.cwd()))
        }
    
    if debug:
        click.echo(f"Found {len(module_map)} Python modules")
    
    try:
        with click.progressbar(files, label='Processing files') as progress_files:
            for file in progress_files:
                file_path = str(file.relative_to(Path.cwd()))
                internal_deps[file_path] = set()
                
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                    
                    # Find all imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for name in node.names:
                                base_module = name.name.split('.')[0]
                                if base_module in module_map:
                                    internal_deps[file_path].add(module_map[base_module]['rel'])
                        
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            base_module = node.module.split('.')[0]
                            if base_module in module_map:
                                internal_deps[file_path].add(module_map[base_module]['rel'])
                
                except Exception as e:
                    if debug:
                        click.echo(f"\n⚠️  Error parsing {file_path}: {str(e)}")
                    continue
        
        # Filter out empty dependencies
        internal_deps = {k: list(v) for k, v in internal_deps.items() if v}
        
        if debug:
            click.echo(f"\nFound {len(internal_deps)} files with dependencies")
            if internal_deps:
                click.echo("\nDependency details:")
                for source, targets in internal_deps.items():
                    click.echo(f"  {source} -> {targets}")
        
        return internal_deps, external_deps
    
    except Exception as e:
        if debug:
            click.echo(f"\n⚠️  Error analyzing dependencies: {str(e)}")
        return {}, {}

def generate_dependency_graph(files, dependencies, theme='light', style='spring', fmt='png', debug=False):
    """Generate a visualization of project dependencies"""
    try:
        if debug:
            click.echo("\nGenerating graph...")
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add nodes and edges
        for source, targets in dependencies.items():
            source_name = Path(source).name
            G.add_node(source_name, type='source')
            for target in targets:
                target_name = Path(target).name
                G.add_node(target_name, type='target')
                G.add_edge(source_name, target_name)
        
        if debug:
            click.echo(f"Graph created with {len(G.nodes())} nodes and {len(G.edges())} edges")
        
        if not G.nodes():
            return None
        
        # Set up plot
        plt.figure(figsize=(12, 8))
        
        # Set colors based on theme
        bg_color = '#1c1c1c' if theme == 'dark' else 'white'
        text_color = 'white' if theme == 'dark' else 'black'
        edge_color = '#404040' if theme == 'dark' else '#808080'
        node_colors = ['#4a9eff' if G.nodes[n].get('type') == 'source' else '#ff4a4a' 
                      for n in G.nodes()]
        
        # Set layout
        if style == 'spring':
            pos = nx.spring_layout(G, k=1, iterations=50, seed=42)
        elif style == 'circular':
            pos = nx.circular_layout(G)
        else:
            pos = nx.shell_layout(G)
        
        # Draw graph
        nx.draw(G, pos,
                node_color=node_colors,
                node_size=2000,
                edge_color=edge_color,
                with_labels=True,
                font_size=8,
                font_weight='bold',
                font_color=text_color,
                arrows=True,
                arrowsize=20)
        
        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='#4a9eff', markersize=10, label='Source Files'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='#ff4a4a', markersize=10, label='Target Files')
        ]
        plt.legend(handles=legend_elements, loc='upper right', 
                  facecolor=bg_color, labelcolor=text_color)
        
        plt.title(f"Project Dependencies\n{len(G.nodes())} modules, {len(G.edges())} dependencies",
                 color=text_color, pad=20, size=14)
        
        plt.gca().set_facecolor(bg_color)
        plt.gcf().set_facecolor(bg_color)
        
        return plt
        
    except Exception as e:
        if debug:
            click.echo(f"\n⚠️  Error generating visualization: {str(e)}")
        return None

@cli.command()
@click.option('--complexity/--no-complexity', default=True, help='Show cyclomatic complexity')
@click.option('--duplication/--no-duplication', default=True, help='Check for code duplication')
@click.option('--lint/--no-lint', default=True, help='Run linting checks')
@click.option('--threshold', default=10, help='Complexity threshold for warnings')
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
def quality(complexity: bool, duplication: bool, lint: bool, threshold: int, format: str):
    """Analyze code quality metrics"""
    quality_command(complexity, duplication, lint, threshold, format)

def main():
    cli()

if __name__ == "__main__":
    main() 