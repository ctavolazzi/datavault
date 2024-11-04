#!/usr/bin/env python3
from pathlib import Path
import argparse
from typing import List, Set

def generate_tree(
    directory: Path,
    prefix: str = "",
    ignore_dirs: Set[str] = {
        '.git', '__pycache__', '.pytest_cache', 
        'venv', 'env', '.idea', '.vscode', 
        'node_modules', 'backup_'
    },
    ignore_files: Set[str] = {
        '.gitignore', '.env', '*.pyc', '*.pyo', 
        '*.pyd', '.DS_Store', 'Thumbs.db'
    },
    max_depth: int = None,
    current_depth: int = 0
) -> List[str]:
    """Generate a tree structure of the given directory"""
    
    if max_depth is not None and current_depth > max_depth:
        return ['│   ' + prefix + '...']
    
    # Initialize the tree
    tree = []
    
    # Get all items in directory, sorted with directories first
    items = sorted(directory.iterdir(), 
                  key=lambda x: (not x.is_dir(), x.name.lower()))
    
    # Process each item
    for i, item in enumerate(items):
        # Skip ignored directories and files
        if (item.is_dir() and item.name in ignore_dirs) or \
           (item.is_file() and any(item.match(pat) for pat in ignore_files)):
            continue
        
        # Skip backup directories
        if 'backup_' in str(item):
            continue
        
        # Determine if this is the last item
        is_last = i == len(items) - 1
        
        # Create the branch symbol
        branch = '└── ' if is_last else '├── '
        
        # Add the item to the tree
        tree.append(prefix + branch + item.name)
        
        # If it's a directory, recursively process its contents
        if item.is_dir():
            ext_prefix = prefix + ('    ' if is_last else '│   ')
            tree.extend(
                generate_tree(
                    item, 
                    ext_prefix,
                    ignore_dirs,
                    ignore_files,
                    max_depth,
                    current_depth + 1
                )
            )
    
    return tree

def main():
    parser = argparse.ArgumentParser(description='Generate a file tree structure')
    parser.add_argument('path', nargs='?', default='.',
                      help='Path to generate tree from (default: current directory)')
    parser.add_argument('--max-depth', type=int, default=None,
                      help='Maximum depth to traverse')
    parser.add_argument('--output', '-o', type=str,
                      help='Output file (default: print to stdout)')
    parser.add_argument('--ignore-dirs', type=str, nargs='+',
                      default=['.git', '__pycache__', '.pytest_cache', 'venv', 'env'],
                      help='Directories to ignore')
    parser.add_argument('--ignore-files', type=str, nargs='+',
                      default=['.gitignore', '.env', '*.pyc'],
                      help='File patterns to ignore')
    
    args = parser.parse_args()
    
    # Convert path to absolute Path object
    directory = Path(args.path).resolve()
    
    # Generate the tree
    tree = [str(directory)] + generate_tree(
        directory,
        ignore_dirs=set(args.ignore_dirs),
        ignore_files=set(args.ignore_files),
        max_depth=args.max_depth
    )
    
    # Output the tree
    output = '\n'.join(tree)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)

if __name__ == '__main__':
    main()