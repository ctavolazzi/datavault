#!/usr/bin/env python3
"""
Project Structure Manager
Maintains project structure based on YAML configuration
"""

import yaml
from pathlib import Path
import shutil
import logging
from typing import Dict, Set, List, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass
from tqdm import tqdm
from project_manager.file_analyzer import FileAnalyzer
import warnings

@dataclass
class FileMove:
    """Represents a file that needs to be moved"""
    source: Path
    target: Path
    reason: str
    metadata: Optional[Dict] = None

class ProjectManager:
    def __init__(self, root_dir: Optional[Path] = None, dry_run: bool = False):
        self.root = root_dir or Path.cwd()
        self.dry_run = dry_run
        self.structure = self._load_structure()
        self.logger = self._setup_logger()
        # Initialize FileAnalyzer without file logging
        self.file_analyzer = FileAnalyzer(use_magic=True, enable_file_logging=False)
        self.file_analyzer.root = self.root

    def _load_structure(self) -> dict:
        """Load and validate project structure from YAML"""
        structure_file = self.root / 'project_structure.yaml'
        if not structure_file.exists():
            raise FileNotFoundError("project_structure.yaml not found")
        
        try:
            with open(structure_file) as f:
                structure = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in project_structure.yaml: {str(e)}")
            
        if structure is None:
            raise ValueError("Invalid project structure: empty file")
            
        if not isinstance(structure, dict):
            raise ValueError("Project structure must be a dictionary")
            
        # First validate basic structure
        self._validate_directory_structure(structure)
        
        # Then check for duplicate paths and collect name locations
        all_paths = []  # Track all paths to check for conflicts
        name_locations: Dict[str, List[str]] = {}  # Track where each name appears
        root_names = set()  # Track names at root level
        
        # First collect root level names
        for name in structure.keys():
            root_names.add(name)
        
        self._check_duplicate_paths(structure, '', all_paths, name_locations, root_names)
        
        # Warn about directories with same name in different locations
        self._warn_about_duplicates(name_locations)
        
        return structure

    def _check_duplicate_paths(self, structure: dict, current_path: str, all_paths: list, 
                             name_locations: Dict[str, List[str]], root_names: set) -> None:
        """Check for duplicate directory paths"""
        for name, config in structure.items():
            path = f"{current_path}/{name}" if current_path else name
            
            # Track locations of each directory name
            if name not in name_locations:
                name_locations[name] = []
            name_locations[name].append(path)
            
            # If this is a nested path and the name exists at root level, it's an error
            if current_path and name in root_names:
                raise ValueError(f"Duplicate directory path found: '{name}'")
            
            # Check subdirectories
            if 'subdirs' in config and isinstance(config['subdirs'], dict):
                self._check_duplicate_paths(config['subdirs'], path, all_paths, name_locations, root_names)

    def _warn_about_duplicates(self, name_locations: Dict[str, List[str]]) -> None:
        """Warn about directories with the same name in different locations"""
        print("\nDEBUG: _warn_about_duplicates called")
        print(f"name_locations = {name_locations}")
        
        for name, locations in name_locations.items():
            print(f"\nChecking '{name}' with locations: {locations}")
            
            if len(locations) > 1:
                print(f"Found duplicate: {name} in multiple locations")
                
                # Sort locations for consistent output
                locations_str = "\n    - ".join(sorted(locations))
                print(f"Formatted locations:\n    - {locations_str}")
                
                # Generate context-aware examples
                example_suggestions = []
                for loc in locations:
                    parts = loc.split('/')
                    print(f"Processing location '{loc}' with parts: {parts}")
                    if len(parts) > 1:
                        parent = parts[-2]
                        suggestion = f"{parent}_{name}"
                        print(f"Generated suggestion: {suggestion}")
                        example_suggestions.append(suggestion)
                
                # Use the first two suggestions as examples
                examples = " or ".join(f"'{s}'" for s in example_suggestions[:2])
                print(f"Final examples: {examples}")
                
                warning_msg = (
                    f"\nPotential naming conflict detected:\n"
                    f"  Directory name '{name}' is used in multiple locations:\n"
                    f"    - {locations_str}\n"
                    f"  Suggestions:\n"
                    f"    • Use more specific names (e.g., {examples})\n"
                    f"    • Add prefixes to clarify purpose\n"
                    f"    • Keep as-is if the context is clear enough"
                )
                print(f"\nFinal warning message:\n{warning_msg}")
                
                warnings.warn(warning_msg, UserWarning)

    def _validate_directory_structure(self, structure: dict, path: str = '') -> None:
        """Recursively validate directory structure"""
        for name, config in structure.items():
            # Validate directory name
            if '/' in name or '\\' in name:
                raise ValueError(f"Invalid directory name '{name}': must not contain path separators")
                
            # Validate config is a dictionary
            if not isinstance(config, dict):
                raise ValueError(f"Configuration for '{name}' must be a dictionary")
                
            # Validate description exists
            if 'description' not in config:
                raise ValueError(f"Missing required 'description' for directory '{name}'")
                
            # Validate subdirectories if they exist
            if 'subdirs' in config:
                if not isinstance(config['subdirs'], dict):
                    raise ValueError(f"'subdirs' in '{name}' must be a dictionary")
                self._validate_directory_structure(config['subdirs'], f"{path}/{name}" if path else name)

    def _collect_all_paths(self, structure: dict, current_path: str = '') -> list[str]:
        """Collect all directory paths in the structure"""
        paths = []
        for name, config in structure.items():
            path = f"{current_path}/{name}" if current_path else name
            paths.append(path)
            
            if 'subdirs' in config and isinstance(config['subdirs'], dict):
                paths.extend(self._collect_all_paths(config['subdirs'], path))
        
        return paths

    def _find_duplicate_paths(self, paths: list[str]) -> list[str]:
        """Find any duplicate paths in the list"""
        seen = set()
        duplicates = []
        
        for path in paths:
            if path in seen:
                duplicates.append(path)
            else:
                seen.add(path)
                # Also check if any parent path exists as a leaf node
                parts = path.split('/')
                for i in range(len(parts)):
                    partial = '/'.join(parts[:i+1])
                    if partial != path and partial in seen:
                        duplicates.append(partial)
        
        return duplicates

    def _setup_logger(self) -> logging.Logger:
        """Configure logging"""
        logger = logging.getLogger('project_manager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            logger.addHandler(handler)
        
        return logger

    def _get_required_dirs(self) -> Set[Path]:
        """Extract required directories from structure"""
        dirs = set()
        
        def process_dir(path: Path, config: dict):
            if 'subdirs' in config:
                for name, subconfig in config['subdirs'].items():
                    subpath = path / name
                    dirs.add(subpath)
                    if isinstance(subconfig, dict):
                        process_dir(subpath, subconfig)
        
        process_dir(self.root, self.structure)
        return dirs

    def _get_file_patterns(self) -> Dict[str, str]:
        """Generate file placement rules from structure"""
        patterns = {}
        
        def process_dir(config: dict, path: str = ''):
            if 'file_patterns' in config:
                for pattern, info in config['file_patterns'].items():
                    # Handle both string values and dict configurations
                    if isinstance(info, dict):
                        target_dir = info.get('target', path)
                    else:
                        target_dir = info if isinstance(info, str) else path
                    patterns[pattern] = target_dir
                    
            if 'subdirs' in config:
                for name, subconfig in config['subdirs'].items():
                    subpath = f"{path}/{name}" if path else name
                    if isinstance(subconfig, dict):
                        process_dir(subconfig, subpath)
        
        process_dir(self.structure)
        return patterns

    def _should_move_file(self, source: Path, target_dir: str) -> bool:
        """Determine if file should be moved to target directory"""
        # Get the full target path
        target_path = self.root / target_dir
        
        # Don't move if file is already in correct directory
        if source.parent == target_path:
            return False
            
        # Don't move if file is in a more specific subdirectory
        if str(source.parent).startswith(str(target_path)):
            return False
            
        return True

    def _analyze_files(self) -> List[FileMove]:
        """Analyze files and determine required moves"""
        moves = []
        patterns = self._get_file_patterns()
        
        for file_path in tqdm(list(self.root.rglob('*')), desc="Analyzing files"):
            if not file_path.is_file():
                continue
                
            # Skip special files/directories
            if any(part.startswith('.') for part in file_path.parts):
                continue
            if any(part.startswith('backup_') for part in file_path.parts):
                continue
            if '__pycache__' in file_path.parts:
                continue
            
            # First try pattern matching from YAML config
            target_dir = None
            reason = None
            for pattern, dir_path in patterns.items():
                if re.match(pattern, file_path.name):
                    target_dir = dir_path
                    reason = f"Matches pattern: {pattern}"
                    break
            
            # If no pattern match, use FileAnalyzer
            if not target_dir:
                suggested_dir, metadata = self.file_analyzer.analyze_file(file_path)
                if suggested_dir:
                    target_dir = suggested_dir
                    reason = f"File analysis: {metadata.get('mime_type', 'unknown type')}"
            
            if target_dir and self._should_move_file(file_path, target_dir):
                target_path = self.root / target_dir / file_path.name
                # Don't suggest moving if target would be the same directory
                if file_path.parent != target_path.parent:
                    moves.append(FileMove(
                        source=file_path,
                        target=target_path,
                        reason=reason,
                        metadata=metadata if 'metadata' in locals() else None
                    ))
        
        return moves

    def _create_backup(self) -> Path:
        """Create timestamped backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.root / f'backup_{timestamp}'
        
        self.logger.info("\n📦 Creating backup...")
        backup_dir.mkdir(exist_ok=True)
        
        # Copy files
        for file_path in tqdm(list(self.root.rglob('*')), desc="Backing up files"):
            if file_path.is_file():
                rel_path = file_path.relative_to(self.root)
                if not any(part.startswith('.') for part in rel_path.parts):
                    target = backup_dir / rel_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, target)
        
        return backup_dir

    def _remove_empty_dirs(self) -> List[Path]:
        """Remove empty directories"""
        removed = []
        for path in sorted(self.root.rglob('*'), reverse=True):
            if path.is_dir() and not any(path.iterdir()):
                if not self.dry_run:
                    path.rmdir()
                removed.append(path)
        return removed

    def reset(self) -> None:
        """Reset project structure to match configuration"""
        self.logger.info("\n=== Project Structure Analysis ===")
        
        # Analyze first
        moves = self._analyze_files()
        if not moves:
            self.logger.info("\n✨ Project structure is already correct - no changes needed")
            self._print_structure_summary()
            return
        
        # Show planned changes
        self.logger.info("\n🔄 Planned changes:")
        for move in moves:
            self.logger.info(f"  {move.source.relative_to(self.root)} → {move.target.relative_to(self.root)}")
            self.logger.info(f"    Reason: {move.reason}")
        
        # Confirm if not dry run
        if not self.dry_run:
            confirm = input("\nProceed with changes? (y/N): ").lower()
            if confirm != 'y':
                self.logger.info("❌ Reset cancelled")
                return
        
        self.logger.info("\n=== Project Structure Reset ===")
        
        # Create backup only if changes will be made
        if not self.dry_run:
            backup_dir = self._create_backup()
            self.logger.info(f"✓ Backup created: {backup_dir.name}")
        
        # Ensure required directories exist
        self.logger.info("\n📁 Verifying directory structure...")
        required_dirs = self._get_required_dirs()
        for dir_path in required_dirs:
            if not dir_path.exists():
                if not self.dry_run:
                    dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"{'Would create' if self.dry_run else '✓ Created'}: {dir_path}")
        
        # Move files to correct locations
        self.logger.info("\n📦 Organizing files...")
        moves = self._analyze_files()
        
        for move in tqdm(moves, desc="Moving files"):
            if not self.dry_run:
                move.target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.move(str(move.source), str(move.target))
                    self.logger.info(f"✓ Moved: {move.source.relative_to(self.root)} → {move.target.relative_to(self.root)}")
                except PermissionError as e:
                    self.logger.error(f"❌ Failed to move {move.source.relative_to(self.root)}: File in use")
                    continue
                except Exception as e:
                    self.logger.error(f"❌ Failed to move {move.source.relative_to(self.root)}: {str(e)}")
                    continue
            else:
                self.logger.info(f"Would move: {move.source.relative_to(self.root)} → {move.target.relative_to(self.root)}")
        
        # Clean up empty directories
        self.logger.info("\n🗑️  Cleaning up empty directories...")
        removed = self._remove_empty_dirs()
        for dir_path in removed:
            self.logger.info(f"{'Would remove' if self.dry_run else '✓ Removed'}: {dir_path.relative_to(self.root)}")
        
        self.logger.info(f"\n=== {'[DRY RUN] ' if self.dry_run else ''}Reset Complete ===\n")

    def analyze(self) -> None:
        """Analyze current project structure"""
        self.logger.info("\n=== Project Structure Analysis ===")
        
        # Show current structure
        self.logger.info("\n📁 Current Directory Structure:")
        for path in sorted(p for p in self.root.rglob('*') if p.is_dir()):
            rel_path = path.relative_to(self.root)
            if not any(part.startswith('.') for part in rel_path.parts):
                self.logger.info(f"  {rel_path}")
        
        # Check for any files that would be moved
        self.logger.info("\n📄 File Organization:")
        moves = self._analyze_files()
        
        if moves:
            self.logger.info(f"\nFound {len(moves)} files that need organizing:")
            for move in moves:
                self.logger.info(f"  - {move.source.relative_to(self.root)} → {move.target.relative_to(self.root)}")
                self.logger.info(f"    Reason: {move.reason}")
        else:
            self.logger.info("\n✨ All files are in their correct locations")
        
        self.logger.info("\n=== Analysis Complete ===\n")

    def _print_structure_summary(self) -> None:
        """Print a concise summary of the current project structure"""
        # Group files by directory and extension
        structure = {}
        for file_path in self.root.rglob('*'):
            if file_path.is_file():
                # Skip backup directories, cache files, and hidden files
                if any(part.startswith(('backup_', '__', '.')) for part in file_path.parts):
                    continue
                
                parent = file_path.parent.relative_to(self.root)
                ext = file_path.suffix
                if ext and parent not in structure:
                    structure[parent] = set()
                if ext:
                    structure[parent].add(ext)

        # Print concise summary
        self.logger.info("\nProject contains:")
        for dir_path, extensions in sorted(structure.items()):
            if extensions:  # Only show directories containing files
                dir_name = 'root' if str(dir_path) == '.' else str(dir_path)
                exts = ', '.join(sorted(ext[1:] for ext in extensions))  # Remove leading dots
                self.logger.info(f"  📁 {dir_name}: {exts}")

    def analyze_project(self) -> Dict[str, any]:
        """Analyze project structure and files"""
        results = {
            'structure': {},
            'files': {},
            'issues': []
        }

        # Analyze directory structure
        print("\n=== 🔍 Analyzing Project Structure ===")
        self.file_analyzer.analyze_structure()
        
        # Analyze files
        print("\n=== 📄 Analyzing Files ===")
        moves = self._analyze_files()
        
        if moves:
            print("\nSuggested File Moves:")
            for move in moves:
                print(f"\n  • {move.source.relative_to(self.root)} → {move.target.relative_to(self.root)}")
                print(f"    Reason: {move.reason}")
                if move.metadata:
                    print(f"    Type: {move.metadata.get('mime_type', 'unknown')}")
                    if 'line_count' in move.metadata:
                        print(f"    Lines: {move.metadata['line_count']}")
                    if 'encoding' in move.metadata:
                        print(f"    Encoding: {move.metadata['encoding']} ({move.metadata['confidence']})")
        else:
            print("\n✨ All files appear to be in their correct locations!")

        return results

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage project structure')
    parser.add_argument('--root', type=Path, help='Project root directory')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without executing')
    parser.add_argument('--analyze', action='store_true', help='Analyze without making changes')
    
    args = parser.parse_args()
    
    manager = ProjectManager(root_dir=args.root, dry_run=args.dry_run)
    
    if args.analyze:
        manager.analyze()
    else:
        manager.reset()

if __name__ == '__main__':
    main()