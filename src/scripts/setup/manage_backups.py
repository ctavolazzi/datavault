#!/usr/bin/env python3
from pathlib import Path
import json
from datetime import datetime, timedelta
import shutil
import sys

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def list_backups(root_dir: Path = None) -> None:
    """List all backups and their details"""
    root = root_dir or Path.cwd()
    backups = []
    
    # Collect backup information
    for backup_dir in root.glob('backup_*'):
        if not backup_dir.is_dir():
            continue
            
        manifest_path = backup_dir / 'backup_manifest.json'
        if not manifest_path.exists():
            continue
            
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            backup_time = datetime.fromisoformat(manifest['timestamp'])
            backups.append({
                'dir': backup_dir,
                'time': backup_time,
                'files': manifest['files_backed_up'],
                'size': manifest['total_size']
            })
        except Exception as e:
            print(f"Warning: Could not read manifest for {backup_dir.name}: {e}")
    
    if not backups:
        print("No backups found!")
        return
    
    # Sort backups by time (newest first)
    backups.sort(key=lambda x: x['time'], reverse=True)
    
    # Print backup summary
    print("\n📂 Available Backups:")
    print("\nID  Date                 Files    Size     Directory")
    print("-" * 60)
    
    for i, backup in enumerate(backups, 1):
        age = datetime.now() - backup['time']
        age_str = f"({age.days}d ago)" if age.days > 0 else "(today)"
        
        print(f"{i:2d}  {backup['time'].strftime('%Y-%m-%d %H:%M:%S')} {age_str:8} "
              f"{backup['files']:6d}  {format_size(backup['size']):8}  {backup['dir'].name}")
    
    total_size = sum(b['size'] for b in backups)
    print("\nTotal backup storage:", format_size(total_size))

def cleanup_old_backups(max_age_days: int = 30, keep_min: int = 3) -> None:
    """Remove backups older than specified days, keeping at least keep_min backups"""
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    backups = []
    
    print(f"\n🔍 Looking for backups older than {max_age_days} days...")
    
    # Collect backup information
    for backup_dir in Path.cwd().glob('backup_*'):
        if not backup_dir.is_dir():
            continue
            
        manifest_path = backup_dir / 'backup_manifest.json'
        if not manifest_path.exists():
            continue
            
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            backup_time = datetime.fromisoformat(manifest['timestamp'])
            backups.append({
                'dir': backup_dir,
                'time': backup_time,
                'files': manifest['files_backed_up'],
                'size': manifest['total_size']
            })
        except Exception as e:
            print(f"Warning: Could not read manifest for {backup_dir.name}: {e}")
    
    if not backups:
        print("No backups found!")
        return
    
    # Sort backups by time (newest first)
    backups.sort(key=lambda x: x['time'], reverse=True)
    
    # Keep at least keep_min backups
    to_keep = max(keep_min, len([b for b in backups if b['time'] > cutoff_date]))
    
    if len(backups) <= to_keep:
        print(f"\nNo backups to remove (keeping minimum {keep_min} backups)")
        return
    
    # Remove old backups
    for backup in backups[to_keep:]:
        print(f"\nRemoving old backup: {backup['dir'].name}")
        print(f"  Created: {backup['time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Size: {format_size(backup['size'])}")
        
        try:
            shutil.rmtree(backup['dir'])
            print("  ✅ Removed successfully")
        except Exception as e:
            print(f"  ❌ Error removing backup: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage project backups')
    parser.add_argument('--list', action='store_true',
                      help='List all backups')
    parser.add_argument('--cleanup', type=int, metavar='DAYS',
                      help='Remove backups older than DAYS days')
    parser.add_argument('--keep-min', type=int, default=3,
                      help='Minimum number of backups to keep (default: 3)')
    
    args = parser.parse_args()
    
    if args.list:
        list_backups()
    elif args.cleanup:
        cleanup_old_backups(args.cleanup, args.keep_min)
    else:
        list_backups()

if __name__ == '__main__':
    main() 