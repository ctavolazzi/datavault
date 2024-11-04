#!/usr/bin/env python3
from pathlib import Path
import json
from datetime import datetime
import sys

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def verify_backup(backup_dir: Path = None) -> None:
    """Verify the contents and structure of a backup"""
    # Find most recent backup if none specified
    if backup_dir is None:
        backups = sorted([
            d for d in Path.cwd().glob('backup_*')
            if d.is_dir() and d.name.startswith('backup_')
        ], key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not backups:
            print("❌ No backup directories found!")
            sys.exit(1)
            
        backup_dir = backups[0]
    
    print(f"\n🔍 Verifying backup: {backup_dir.name}")
    
    # Check manifest
    manifest_path = backup_dir / 'backup_manifest.json'
    if not manifest_path.exists():
        print("❌ Error: backup_manifest.json not found!")
        sys.exit(1)
    
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # Print backup info
        backup_time = datetime.fromisoformat(manifest['timestamp'])
        print(f"\n📅 Backup created: {backup_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Source directory: {manifest['source_directory']}")
        print(f"📦 Files backed up: {manifest['files_backed_up']}")
        print(f"💾 Total size: {format_size(manifest['total_size'])}")
        
        # Verify all files exist
        print("\nVerifying files...")
        missing_files = []
        extra_files = set()
        size_mismatches = []
        
        # Track all files from manifest
        manifest_files = {Path(f['path']) for f in manifest['files']}
        
        # Check each file in manifest exists in backup
        for file_info in manifest['files']:
            file_path = backup_dir / file_info['path']
            if not file_path.exists():
                missing_files.append(file_info['path'])
            elif file_path.stat().st_size != file_info['size']:
                size_mismatches.append(file_info['path'])
        
        # Check for extra files in backup
        for file_path in backup_dir.rglob('*'):
            if file_path.is_file() and file_path.name != 'backup_manifest.json':
                rel_path = file_path.relative_to(backup_dir)
                if rel_path not in manifest_files:
                    extra_files.add(str(rel_path))
        
        # Print results
        if not any([missing_files, extra_files, size_mismatches]):
            print("\n✅ Backup verified successfully!")
            print(f"   All {manifest['files_backed_up']} files present and correct")
        else:
            print("\n⚠️ Verification found issues:")
            if missing_files:
                print(f"\n❌ Missing files ({len(missing_files)}):")
                for f in sorted(missing_files)[:5]:
                    print(f"  • {f}")
                if len(missing_files) > 5:
                    print(f"  ... and {len(missing_files)-5} more")
            
            if extra_files:
                print(f"\n⚠️ Extra files found ({len(extra_files)}):")
                for f in sorted(extra_files)[:5]:
                    print(f"  • {f}")
                if len(extra_files) > 5:
                    print(f"  ... and {len(extra_files)-5} more")
            
            if size_mismatches:
                print(f"\n⚠️ Size mismatches ({len(size_mismatches)}):")
                for f in sorted(size_mismatches)[:5]:
                    print(f"  • {f}")
                if len(size_mismatches) > 5:
                    print(f"  ... and {len(size_mismatches)-5} more")
        
        # Print file type summary
        print("\n📊 File type summary:")
        type_counts = {}
        type_sizes = {}
        for file_info in manifest['files']:
            ext = Path(file_info['path']).suffix or 'no extension'
            type_counts[ext] = type_counts.get(ext, 0) + 1
            type_sizes[ext] = type_sizes.get(ext, 0) + file_info['size']
        
        for ext in sorted(type_counts.keys()):
            count = type_counts[ext]
            size = type_sizes[ext]
            print(f"  • {ext:12} {count:3d} files  {format_size(size):>8}")
        
    except Exception as e:
        print(f"\n❌ Error verifying backup: {e}")
        sys.exit(1)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify backup contents')
    parser.add_argument('--backup-dir', type=Path,
                      help='Backup directory to verify (default: most recent)')
    
    args = parser.parse_args()
    verify_backup(args.backup_dir)

if __name__ == '__main__':
    main()