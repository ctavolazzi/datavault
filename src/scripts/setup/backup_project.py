#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil
import sys
import json
import os

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def safe_relative_path(path: Path, root: Path) -> Path:
    """Safely get relative path, handling path resolution issues"""
    try:
        return path.relative_to(root)
    except ValueError:
        # If relative_to fails, try with absolute paths
        abs_path = path.absolute()
        abs_root = root.absolute()
        try:
            return abs_path.relative_to(abs_root)
        except ValueError:
            # If still fails, use the full path
            return path

def create_backup(root_dir: Path = None, include_git: bool = False) -> Path:
    """Create a comprehensive backup of the project"""
    root = (root_dir or Path.cwd()).absolute()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = root / f'backup_{timestamp}'
    
    print(f"\n📦 Creating backup in: {backup_dir.name}")
    
    # Create backup directory
    backup_dir.mkdir(exist_ok=True)
    
    try:
        # Define exclusion patterns
        exclude_patterns = {
            '__pycache__',
            '.pytest_cache',
            '.coverage',
            '.env',
            'backup_',  # Exclude other backup directories
        }
        if not include_git:
            exclude_patterns.add('.git')
        
        def should_backup(path: Path) -> bool:
            """Check if path should be backed up"""
            # Don't backup the backup directory itself
            if backup_dir in path.parents or backup_dir == path:
                return False
            return not any(
                exclude in str(path) 
                for exclude in exclude_patterns
            )
        
        # First, collect all files to backup
        print("\nCollecting files to backup...")
        files_to_backup = []
        for path in root.rglob('*'):
            if path.is_file() and should_backup(path):
                files_to_backup.append(path)
        
        total_files = len(files_to_backup)
        print(f"Found {total_files} files to backup")
        
        # Create manifest data
        manifest = {
            'timestamp': datetime.now().isoformat(),
            'source_directory': str(root),
            'files_backed_up': 0,
            'total_size': 0,
            'files': []
        }
        
        # Copy files with progress indicator
        print("\nBacking up files...")
        for i, source in enumerate(files_to_backup, 1):
            try:
                # Get relative path and create target path
                rel_path = safe_relative_path(source, root)
                target = backup_dir / rel_path
                
                # Create parent directories
                target.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(source, target)
                
                # Update manifest
                file_size = source.stat().st_size
                manifest['files'].append({
                    'path': str(rel_path),
                    'size': file_size,
                    'modified': datetime.fromtimestamp(source.stat().st_mtime).isoformat()
                })
                manifest['total_size'] += file_size
                manifest['files_backed_up'] += 1
                
                # Update progress
                progress = (i / total_files) * 100
                print(f"\rProgress: {progress:.1f}% ({i}/{total_files} files)", end='')
                
            except Exception as e:
                print(f"\nWarning: Failed to backup {source}: {str(e)}")
                continue
        
        print("\n")  # New line after progress
        
        # Write manifest
        manifest_path = backup_dir / 'backup_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Print summary
        print(f"\n✅ Backup complete!")
        print(f"📁 Files backed up: {manifest['files_backed_up']}")
        print(f"💾 Total size: {format_size(manifest['total_size'])}")
        print(f"📍 Location: {backup_dir}")
        
        return backup_dir
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Backup interrupted by user!")
        if backup_dir.exists():
            print(f"Cleaning up partial backup: {backup_dir}")
            shutil.rmtree(backup_dir)
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Backup failed: {e}", file=sys.stderr)
        if backup_dir.exists():
            print(f"Cleaning up failed backup: {backup_dir}")
            shutil.rmtree(backup_dir)
        raise

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Create a project backup')
    parser.add_argument('--root', type=Path, default=None,
                      help='Root directory to backup (default: current directory)')
    parser.add_argument('--include-git', action='store_true',
                      help='Include .git directory in backup')
    
    args = parser.parse_args()
    
    try:
        backup_dir = create_backup(args.root, args.include_git)
        print("\nBackup created successfully! 🎉")
    except KeyboardInterrupt:
        print("\nBackup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nBackup failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()