#!/usr/bin/env python3
from pathlib import Path
import shutil
import logging
from typing import Dict, Set, List, Tuple
from datetime import datetime
import yaml
from collections import defaultdict
from tqdm import tqdm

class ProjectResetter:
    """Resets project to clean state while preserving essential files"""
    
    def __init__(self, root_dir: Path = None, dry_run: bool = False, force: bool = False, skip_git: bool = False):
        self.root = root_dir or Path.cwd()
        self.dry_run = dry_run
        self.force = force
        self.skip_git = skip_git
        
        # Setup logging
        self.logger = logging.getLogger('project_reset')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            console = logging.StreamHandler()
            console.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(console)
        
        # Load project structure
        try:
            with open(self.root / 'project_structure.yaml') as f:
                self.structure = yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"Could not load project_structure.yaml: {e}")
            self.structure = {}

    def find_nested_directories(self) -> List[Tuple[Path, List[Path]]]:
        """Find directories that appear to be nested incorrectly"""
        nested_dirs = []
        main_dirs = {'src', 'tests', 'output', 'datasets', 'docs', 'config', 'logs'}
        
        for main_dir in main_dirs:
            base_path = self.root / main_dir
            if base_path.exists():
                # Look for directories that match main directory names
                for path in base_path.rglob('*'):
                    if path.is_dir() and path.name in main_dirs:
                        files = list(path.rglob('*'))
                        if files:  # Only include if directory contains files
                            nested_dirs.append((path, files))
        
        return nested_dirs

    def find_duplicate_files(self) -> Dict[str, List[Path]]:
        """Find files that appear in multiple locations"""
        file_locations = defaultdict(list)
        
        # Track locations of all non-README files
        for file_path in self.root.rglob('*'):
            if file_path.is_file() and file_path.name != 'README.md':
                file_locations[file_path.name].append(file_path)
        
        # Return only files that appear in multiple locations
        return {name: locs for name, locs in file_locations.items() 
               if len(locs) > 1}

    def analyze_structure(self) -> None:
        """Analyze current project structure and identify issues"""
        print("\n=== 🔍 Project Structure Analysis ===")
        issues_found = False
        
        try:
            # 1. Find nested directories (excluding backups)
            print("\n📁 Directory Structure Issues:")
            nested_dirs = [
                (path, files) for path, files in self.find_nested_directories()
                if 'backup_' not in str(path)
            ]
            
            if nested_dirs:
                issues_found = True
                print(f"\n  Found {len(nested_dirs)} directories to reorganize:")
                for dir_path, files in nested_dirs:
                    print(f"\n  📂 {dir_path.relative_to(self.root)}:")
                    print(f"    Contains {len(files)} items, should be moved to {dir_path.parent.parent}")
                    for f in sorted(f for f in files if f.is_file())[:3]:
                        print(f"    → {f.relative_to(dir_path)}")
                    if len(files) > 3:
                        print(f"    ... and {len(files)-3} more items")
            else:
                print("  ✓ Directory structure looks good")
            
            # 2. Find duplicate files (excluding backups and cache)
            print("\n📄 File Duplication Issues:")
            duplicates = self.find_duplicate_files()
            
            # Filter and categorize duplicates
            util_scripts = {}
            source_files = {}
            generated_files = {}
            
            for name, locations in duplicates.items():
                # Skip backup files and git/cache files
                locations = [loc for loc in locations 
                            if 'backup_' not in str(loc)
                            and '__pycache__' not in str(loc)
                            and '.git' not in str(loc)]
                if not locations:
                    continue
                
                if name.endswith('.py'):
                    if name in ['cleanup_project.py', 'generate_filetree.py']:
                        util_scripts[name] = locations
                    else:
                        source_files[name] = locations
                elif any(name.endswith(ext) for ext in ['.png', '.json']):
                    generated_files[name] = locations
            
            if util_scripts:
                print("\n  Utility Scripts to Clean Up:")
                for name, locations in util_scripts.items():
                    print(f"  📎 {name}:")
                    for loc in locations:
                        print(f"    → {loc.relative_to(self.root)}")
            
            if source_files:
                print("\n  Source Files to Reorganize:")
                for name, locations in source_files.items():
                    print(f"  📎 {name}:")
                    for loc in locations:
                        print(f"    → {loc.relative_to(self.root)}")
            
            if generated_files:
                print("\n  Generated Files to Consolidate:")
                print(f"  Found {len(generated_files)} output files in multiple locations")
                print("  (Run with --show-all to see full list)")
            
            if not any([util_scripts, source_files, generated_files]):
                print("  ✓ No significant file duplication found")
            
            if issues_found:
                print("\n🛠️  Recommended Actions:")
                print("1. Clean up nested directories:")
                for dir_path, _ in nested_dirs:
                    print(f"   - Move {dir_path.relative_to(self.root)} → {dir_path.parent.parent}")
                if util_scripts:
                    print("\n2. Remove duplicate utility scripts from src/")
                if source_files:
                    print("\n3. Consolidate source files to correct locations")
                print("\nTo execute these changes:")
                print("  python reset_project.py --dry-run")
                print("  python reset_project.py  # if changes look good")
            else:
                print("\n✨ Project Structure Looks Good!")
                print("No significant issues found.")
            
        except Exception as e:
            print(f"\n⚠️  Error during analysis: {e}")
            raise
            
        print("\n=== Analysis Complete ===\n")

    def verify_safe_to_proceed(self) -> bool:
        """Verify that it's safe to proceed with reset"""
        print("\n🔍 Safety Checks:")
        
        # 1. Check for uncommitted git changes (optional)
        if (self.root / '.git').exists():
            try:
                import importlib.util
                if importlib.util.find_spec('git'):
                    import git
                    repo = git.Repo(self.root)
                    if repo.is_dirty():
                        print("  ⚠️  Warning: You have uncommitted git changes")
                        return False
                else:
                    print("  ℹ️  Git check skipped (gitpython not installed)")
            except Exception as e:
                print(f"  ℹ️  Git check skipped: {e}")
        
        # 2. Verify target locations are safe
        unsafe = False
        moves = {
            'datasets/raw/datasets': 'datasets',
            'src/src': 'src',
            'src/tests': 'tests',
            'src/tests/tests': 'tests',
            'output/figures/output': 'output/figures'
        }
        
        print("\n  Checking target directories:")
        for source, target in moves.items():
            source_path = self.root / source
            target_path = self.root / target
            if target_path.exists():
                files = list(target_path.rglob('*'))
                if files:
                    print(f"  ⚠️  Target directory not empty: {target}")
                    print(f"      Contains {len(files)} files that might be overwritten")
                    unsafe = True
            else:
                print(f"  ✓ Target clear: {target}")
        
        if unsafe:
            print("\n❌ Safety check failed. Please:")
            print("1. Review target directories for potential conflicts")
            print("2. Run with --force to override these checks")
            return False
        
        print("\n  ✓ All critical safety checks passed")
        return True

    def confirm_reset(self) -> bool:
        """Ask for user confirmation before proceeding"""
        print("\n🚨 Ready to Reset Project Structure")
        print("\nThis will:")
        print("1. Create a backup of your current project")
        print("2. Move files to their correct locations")
        print("3. Clean up duplicate files")
        print("4. Remove empty directories")
        
        try:
            response = input("\nProceed with reset? (y/N): ").lower().strip()
            return response == 'y'
        except KeyboardInterrupt:
            print("\nReset cancelled by user")
            return False

    def _create_backup(self, progress_callback=None) -> Path:
        """Create a backup of the current project state"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.root / f'backup_{timestamp}'
        
        print(f"\n📦 Creating backup...")
        
        try:
            # Create backup directory
            backup_dir.mkdir(exist_ok=True)
            
            # Define what to backup (excluding previous backups and cache)
            def backup_filter(path: Path) -> bool:
                return not any(part.startswith('backup_') or part == '__pycache__' 
                             for part in path.parts)
            
            # Copy files to backup
            files_copied = 0
            for item in self.root.rglob('*'):
                if item.is_file() and backup_filter(item.relative_to(self.root)):
                    rel_path = item.relative_to(self.root)
                    backup_path = backup_dir / rel_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, backup_path)
                    files_copied += 1
                    if files_copied % 50 == 0:  # Progress indicator
                        print(f"  → {files_copied} files backed up...", end='\r')
                    if progress_callback:
                        progress_callback(1)
            
            print(f"  ✓ Backed up {files_copied} files to: {backup_dir.name}")
            
            # Create backup manifest
            manifest = backup_dir / 'backup_manifest.txt'
            with open(manifest, 'w') as f:
                f.write(f"Backup created: {datetime.now().isoformat()}\n")
                f.write(f"Original directory: {self.root}\n")
                f.write(f"Files backed up: {files_copied}\n\n")
                f.write("Files included:\n")
                for item in sorted(backup_dir.rglob('*')):
                    if item.is_file() and item.name != 'backup_manifest.txt':
                        f.write(f"- {item.relative_to(backup_dir)}\n")
            
            return backup_dir
            
        except Exception as e:
            print(f"\n❌ Backup failed: {e}")
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            raise

    def _count_files(self, directory: Path) -> dict:
        """Count files by extension in directory"""
        from collections import defaultdict
        
        counts = defaultdict(int)
        for file in directory.rglob('*'):
            if file.is_file() and not any(part.startswith('backup_') for part in file.parts):
                counts[file.suffix or 'no_extension'] += 1
        return dict(counts)

    def verify_file_counts(self, before_counts: dict) -> bool:
        """Verify file counts match before and after"""
        print("\n🔍 Verifying file counts...")
        after_counts = self._count_files(self.root)
        
        # Compare counts
        all_extensions = set(before_counts.keys()) | set(after_counts.keys())
        has_differences = False
        
        for ext in sorted(all_extensions):
            before = before_counts.get(ext, 0)
            after = after_counts.get(ext, 0)
            if before != after:
                print(f"  ⚠️  {ext} files: {before} → {after}")
                has_differences = True
            else:
                print(f"  ✓ {ext} files: {before}")
        
        return not has_differences

    def wipe_clean(self, create_backup: bool = True) -> None:
        """Reset project to clean state"""
        # Initialize file counts before changes
        before_counts = self._count_files(self.root)
        
        if not self.dry_run:
            if not self.force and not self.verify_safe_to_proceed():
                print("\n❌ Reset aborted for safety. Use --force to override.")
                return
            
            if not self.confirm_reset():
                print("\n❌ Reset cancelled by user.")
                return
            
            if create_backup:
                with tqdm(desc="Creating backup", unit="files") as pbar:
                    backup_dir = self._create_backup(progress_callback=pbar.update)
                print(f"\n✓ Created backup in: {backup_dir.name}")
        
        print(f"\n=== {'[DRY RUN] ' if self.dry_run else ''}Executing Project Reset ===")
        
        # 1. Directory moves with progress
        print("\n📁 Cleaning up nested directories...")
        total_files = sum(len(list(self.root.glob(f"{src}/**/*"))) for src in ['tests/tests', 'output/figures/figures'])
        
        with tqdm(total=total_files, desc="Moving files", disable=self.dry_run) as pbar:
            # Move test files
            if (self.root / 'tests/tests').exists():
                self._move_directory_contents('tests/tests', 'tests', pbar)
            
            # Move and flatten figures
            if (self.root / 'output/figures/figures').exists():
                self._move_directory_contents('output/figures/figures', 'output/figures', pbar, flatten=True)
        
        # 2. Test file organization
        print("\n🧪 Organizing test files...")
        test_moves = {
            # Move collector tests to unit/collectors
            'tests/collectors/test_news_collector.py': 'tests/unit/collectors/test_news_collector.py',
            
            # Move utils tests to unit/utils
            'tests/utils/test_report.py': 'tests/unit/utils/test_report.py',
            
            # Keep other unit tests in place
            'tests/unit/test_news_collection.py': 'tests/unit/test_news_collection.py',
            'tests/unit/test_news_collection_test.py': 'tests/unit/test_news_collection_test.py'
        }
        
        for source, target in tqdm(test_moves.items(), desc="Moving test files", disable=self.dry_run):
            source_path = self.root / source
            if source_path.exists():
                if not self.dry_run:
                    target_path = self.root / target
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source_path), str(target_path))
                print(f"{'Would move' if self.dry_run else '✓ Moved'}: {source} → {target}")
        
        # 3. Verify utility scripts
        print("\n📄 Verifying utility scripts...")
        root_scripts = {
            'cleanup_project.py',
            'generate_filetree.py',
            'reset_project.py',
            'setup_project.py',
            'file_analyzer.py'
        }
        
        for script in root_scripts:
            if (self.root / 'src' / script).exists():
                if self.dry_run:
                    print(f"  Would remove duplicate: src/{script}")
                else:
                    (self.root / 'src' / script).unlink()
                    print(f"  ✓ Removed duplicate: src/{script}")
        
        # 4. Clean up source files
        print("\n📦 Verifying source files...")
        source_files = {
            'src/utils/setup_project.py': 'setup_project.py',  # Move to root
            'src/utils/setup.py': 'src/utils/setup.py',  # Keep in place
            'src/collectors/news_collector.py': None,  # None means verify exists
            'src/core/exceptions.py': None,
            'src/core/logging.py': None,
            'src/scripts/analyze_collections.py': None,
            'src/utils/news_analysis.py': None,
            'src/utils/report.py': None,
            'src/utils/visualize.py': None,
            'src/utils/cleanup.py': None
        }
        
        for source, target in source_files.items():
            source_path = self.root / source
            if source_path.exists():
                if target:  # Move file
                    if self.dry_run:
                        print(f"  Would move: {source} → {target}")
                    else:
                        target_path = self.root / target
                        shutil.move(str(source_path), str(target_path))
                        print(f"  ✓ Moved: {source} → {target}")
                else:  # Verify file
                    print(f"  ✓ Verified: {source}")
        
        # 5. Clean up empty directories
        if not self.dry_run:
            print("\n🗑️  Cleaning up empty directories...")
            removed = self._remove_empty_dirs()
            if removed:
                print(f"  ✓ Removed {len(removed)} empty directories")
        
            # Verify file counts
            print("\n🔍 Verifying file counts...")
            after_counts = self._count_files(self.root)
            
            # Compare counts
            all_extensions = set(before_counts.keys()) | set(after_counts.keys())
            has_differences = False
            
            for ext in sorted(all_extensions):
                before = before_counts.get(ext, 0)
                after = after_counts.get(ext, 0)
                if before != after:
                    print(f"  ⚠️  {ext} files: {before} → {after}")
                    has_differences = True
                else:
                    print(f"  ✓ {ext} files: {before}")
            
            if not has_differences:
                print("\n✅ All files accounted for")
            else:
                print("\n⚠️  Warning: Some files may have been moved or renamed")
                print("    Check the backup directory if needed")
        
        print(f"\n=== {'[DRY RUN] ' if self.dry_run else ''}Reset Complete ===\n")

    def _move_directory_contents(self, source: str, target: str, pbar=None, flatten=False) -> None:
        """Move directory contents with progress tracking"""
        source_path = self.root / source
        target_path = self.root / target
        
        if not self.dry_run:
            target_path.mkdir(parents=True, exist_ok=True)
            
            for item in source_path.rglob('*'):
                if item.is_file():
                    if flatten:
                        new_path = target_path / item.name
                    else:
                        rel_path = item.relative_to(source_path)
                        new_path = target_path / rel_path
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.move(str(item), str(new_path))
                    if pbar:
                        pbar.update(1)
            
            # Clean up empty source directory
            if source_path.exists():
                shutil.rmtree(source_path)

    def _remove_empty_dirs(self) -> None:
        """Remove empty directories recursively"""
        empty_dirs = []
        for dirpath in self.root.rglob('*'):
            if dirpath.is_dir() and not any(dirpath.iterdir()):
                empty_dirs.append(dirpath)
        
        for dir_path in sorted(empty_dirs, reverse=True):
            dir_path.rmdir()
            print(f"  ✓ Removed empty directory: {dir_path.relative_to(self.root)}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up and organize project structure')
    parser.add_argument('--root', type=Path, default=None,
                      help='Root directory to clean (default: current directory)')
    parser.add_argument('--dry-run', action='store_true',
                      help='Show what would be done without making changes')
    parser.add_argument('--no-backup', action='store_true',
                      help='Skip creating backup before cleaning')
    parser.add_argument('--force', action='store_true',
                      help='Override safety checks')
    parser.add_argument('--analyze', action='store_true',
                      help='Analyze project structure issues')
    parser.add_argument('--skip-git', action='store_true',
                      help='Skip git status check')
    
    args = parser.parse_args()
    
    cleaner = ProjectResetter(
        root_dir=args.root, 
        dry_run=args.dry_run, 
        force=args.force,
        skip_git=args.skip_git
    )
    
    if args.analyze:
        cleaner.analyze_structure()
    else:
        cleaner.wipe_clean(create_backup=not args.no_backup)

if __name__ == '__main__':
    main()