from pathlib import Path
import typer
from rich.console import Console
from rich.prompt import Confirm
import json
from datetime import datetime
import os
import shutil

console = Console()

def save_file_list(files: list, path: str, include_hidden: bool):
    """Save list of files to JSON in outputs directory"""
    # Create outputs directory if it doesn't exist
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"file_list_{timestamp}.json"

    # Check if file exists and create unique name if it does
    output_file = output_dir / filename
    counter = 1
    while output_file.exists():
        new_filename = f"file_list_{timestamp}_{counter}.json"
        output_file = output_dir / new_filename
        counter += 1

    output_data = {
        "path": str(path),
        "include_hidden": include_hidden,
        "files": files,
        "timestamp": timestamp
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    return output_file

def format_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}GB"

def get_all_files(path: Path, include_hidden: bool = False):
    """Recursively get all files including those in hidden directories"""
    files = []
    hidden_files = []

    try:
        for item in path.iterdir():
            # Skip __pycache__ and other system directories
            if any(skip in str(item) for skip in ["__pycache__", ".DS_Store", ".idea"]):
                continue

            is_hidden = item.name.startswith('.')
            file_info = {
                'path': item,
                'name': item.name,
                'is_file': item.is_file(),
                'size': item.stat().st_size if item.is_file() else 0
            }

            if is_hidden and not include_hidden:
                continue

            if is_hidden:
                hidden_files.append(file_info)
            else:
                files.append(file_info)

    except PermissionError:
        console.print(f"[yellow]Warning: Permission denied for {path}[/]")
    except Exception as e:
        console.print(f"[yellow]Warning: Error accessing {path}: {str(e)}[/]")

    return files, hidden_files

def handle_list(
    path: str = typer.Option(".", help="Path to list files from"),
    show_hidden: bool = typer.Option(False, "--show-hidden", "-h", help="Show hidden files"),
    show_size: bool = typer.Option(False, "--show-size", "-s", help="Show file sizes"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all information"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
    no_save: bool = typer.Option(False, "--no-save", help="Don't save output to file")
):
    """List files in the specified directory"""
    if all:
        show_hidden = True
        show_size = True

    try:
        abs_path = Path(path).resolve()
        if not quiet:
            console.print(f"\nListing files in: {abs_path}\n")

        regular_files, hidden_files = get_all_files(abs_path, True)
        regular_files.sort(key=lambda x: (not x['is_file'], x['name'].lower()))

        if not quiet:
            console.print("[bold blue]Files and Directories:[/]")
        for file in regular_files:
            if not file['name'].startswith('.'):
                prefix = "📄 " if file['is_file'] else "📁 "
                size_info = f" ({format_size(file['size'])})" if show_size and file['is_file'] else ""
                console.print(f"{prefix}{file['name']}{size_info}")

        if show_hidden and hidden_files:
            hidden_files.sort(key=lambda x: (not x['is_file'], x['name'].lower()))
            if not quiet:
                console.print("\n[bold yellow]Hidden files and directories:[/]")
            for file in hidden_files:
                if file['name'].startswith('.'):
                    prefix = "📄 " if file['is_file'] else "📁 "
                    size_info = f" ({format_size(file['size'])})" if show_size and file['is_file'] else ""
                    console.print(f"{prefix}{file['name']}{size_info}")

        if not no_save:
            all_files = [str(f['path'].relative_to(abs_path)) for f in regular_files]
            if show_hidden:
                all_files.extend(str(f['path'].relative_to(abs_path)) for f in hidden_files)

            output_file = save_file_list(all_files, str(abs_path), show_hidden)
            if not quiet:
                console.print(f"\n[green]File list saved to: {output_file}[/]")

    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/]")