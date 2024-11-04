from pathlib import Path
from project_manager.project_indexer import ProjectIndexer
import json
from pprint import pprint
import os
from datetime import datetime
from typing import Dict, List, Set, Tuple

def format_size(size: int) -> str:
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def print_directory_tree(directories: List[Dict[str, str]]) -> None:
    """Print directory structure in a tree-like format"""
    # Sort directories by path
    sorted_dirs = sorted(directories, key=lambda x: x['path'])
    
    # Track indentation level
    current_level = []
    
    for dir_info in sorted_dirs:
        path_parts = dir_info['path'].split('/')
        
        # Calculate common prefix length
        level = 0
        if current_level:
            for curr, new in zip(current_level, path_parts):
                if curr != new:
                    break
                level += 1
        
        # Update current level
        current_level = path_parts
        
        # Print with proper indentation
        indent = "  " * level
        print(f"{indent}├── {path_parts[-1]}")

def print_search_results(results: Dict[str, List[Dict]], pattern: str) -> None:
    """Print search results in a tree-like structure"""
    if not results['files'] and not results['directories']:
        print("No matches found.")
        return
        
    # Remove duplicate "Found X matches" message
    print(f"\nFound {len(results['files']) + len(results['directories'])} matches for '{pattern}':")
    
    # Build tree structure
    tree = {'__files': [], '__dirs': [], '__matched': False}  # Initialize root
    
    # Add all necessary directories to tree
    for dir_path in sorted(results['parent_dirs'] | results['directories']):
        current = tree
        parts = Path(dir_path).parts
        
        # Build path
        for part in parts:
            if part not in current:
                current[part] = {'__files': [], '__dirs': [], '__matched': False}
            current = current[part]
    
    # Mark matched directories
    for dir_path in results['directories']:
        current = tree
        for part in Path(dir_path).parts:
            if part not in current:
                current[part] = {'__files': [], '__dirs': [], '__matched': False}
            current = current[part]
            current['__matched'] = True
    
    # Add files to their directories
    for file_info in sorted(results['files'], key=lambda x: x['path']):
        path = Path(file_info['path'])
        current = tree
        
        # Navigate to parent directory
        for part in path.parent.parts:
            if part not in current:
                current[part] = {'__files': [], '__dirs': [], '__matched': False}
            current = current[part]
            
        current['__files'].append((path.name, file_info['size']))
    
    # Print tree
    def print_tree(node, prefix="", is_last=True):
        # Sort and filter directory entries
        dirs = [(k, v) for k, v in node.items() if not k.startswith('__')]
        
        for i, (name, content) in enumerate(sorted(dirs)):
            is_current_last = i == len(dirs) - 1
            
            # Print directory
            marker = '└── ' if is_current_last else '├── '
            matched_marker = '*' if content.get('__matched', False) else ' '
            print(f"{prefix}{marker}{matched_marker}{name}")
            
            # Print files in this directory
            new_prefix = prefix + ('    ' if is_current_last else '│   ')
            for j, (file_name, size) in enumerate(sorted(content['__files'])):
                is_last_file = j == len(content['__files']) - 1 and not [k for k in content if not k.startswith('__')]
                file_marker = '└── ' if is_last_file else '├── '
                print(f"{new_prefix}{file_marker}{file_name} ({format_size(size)})")
            
            # Recurse into subdirectories
            print_tree(content, new_prefix, is_current_last)
    
    # Start printing from root
    print_tree(tree)

def print_search_help() -> None:
    """Print available search options"""
    print("\nSearch Options:")
    print("  pattern          - Search for files/directories containing pattern")
    print("  type:py pattern - Search only Python files containing pattern")
    print("  size:>1M        - Find files larger than 1MB")
    print("  date:>2024-11   - Find files modified after November 2024")
    print("  q               - Quit")

def main() -> None:
    """
    Main function to index and analyze project structure.
    Provides:
    - Project summary (files, directories, total size)
    - File type analysis
    - Recent changes
    - Large files
    - Directory structure
    - Activity analysis
    - Interactive file search
    """
    project_root = Path.cwd()
    indexer = ProjectIndexer(project_root)
    
    print(f"Indexing project at: {project_root}")
    print("(Excluding: __pycache__, .git, backups, and system files)")
    index = indexer.index_project()
    
    # Get additional analytics
    size_summary = indexer.get_size_summary(index)
    recent_changes = indexer.get_recent_changes(index)
    
    # Basic summary
    print("\nProject Summary:")
    print(f"Total Files: {index['metadata']['total_files']}")
    print(f"Total Directories: {index['metadata']['total_dirs']}")
    print(f"Total Size: {format_size(size_summary['total_size'])}")
    
    # File types and sizes
    print("\nFile Types and Sizes:")
    for ext, info in sorted(size_summary['by_type'].items()):
        print(f"  {ext:12} Count: {info['count']:3d}  "
              f"Total: {format_size(info['total_size']):8}  "
              f"Avg: {format_size(info['avg_size'])}")
    
    # Recent changes
    print("\nRecent Changes (Last 7 Days):")
    for change in recent_changes[:5]:  # Show 5 most recent
        print(f"  {change['modified'].strftime('%Y-%m-%d %H:%M')} - {change['path']}")
    
    # Large files
    if size_summary['large_files']:
        print("\nLarge Files (>1MB):")
        for file in size_summary['large_files'][:5]:  # Show 5 largest
            print(f"  {format_size(file['size']):8} - {file['path']}")
    
    print("\nDirectory Structure:")
    print_directory_tree(index['directories'])
    
    # Add activity analysis
    print("\nProject Activity (Last 30 Days):")
    activity = indexer.analyze_activity(index)
    print(f"Total Changes: {activity['total_changes']}")
    
    print("\nMost Active Directories:")
    for dir_path, count in activity['most_active_dirs']:
        print(f"  {count:3d} changes - {dir_path}")
    
    print("\nMost Active File Types:")
    for file_type, count in activity['most_active_types']:
        print(f"  {count:3d} changes - {file_type}")
    
    # Add interactive search
    print("\nType 'help' for search options")
    while True:
        try:
            search_term = input("\nEnter search pattern (or 'q' to quit): ").strip()
            if search_term.lower() == 'q':
                break
            elif search_term.lower() == 'help':
                print_search_help()
                continue
                
            # Parse search options
            if search_term.startswith('type:'):
                try:
                    file_type = search_term[5:].split()[0]
                    pattern = ' '.join(search_term.split()[1:])
                    if not pattern:
                        print("Error: No search pattern provided after file type")
                        continue
                    results = indexer.search_files(index, pattern, file_type=file_type)
                except IndexError:
                    print("Error: Invalid type: format. Use 'type:ext pattern'")
                    continue
            else:
                results = indexer.search_files(index, search_term)
                
            if results['message']:
                print(f"\n{results['message']}")
                
            if results['files'] or results['directories']:
                print(f"\nFound {len(results['files']) + len(results['directories'])} matches for '{search_term}':")
                print_search_results(results, search_term)
        except KeyboardInterrupt:
            print("\nSearch cancelled")
            break
        except Exception as e:
            print(f"Error during search: {e}")
            continue

if __name__ == "__main__":
    main()