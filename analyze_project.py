#!/usr/bin/env python3
from pathlib import Path
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import os

# Import from setup_scripts
from setup_scripts.project_indexer import ProjectIndexer
from setup_scripts.generate_filetree import generate_tree
from setup_scripts.manage_backups import list_backups
from setup_scripts.logging import ProjectLogger

def format_size(size: int) -> str:
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def normalize_path(path: str) -> str:
    """Normalize path separators for consistent display"""
    return str(Path(path)).replace('\\', '/')

class ProjectAnalyzer:
    """Comprehensive project analysis tool"""
    
    def __init__(self, root_dir: Path = None):
        self.root = root_dir or Path.cwd()
        self.indexer = ProjectIndexer(self.root)
        self.logger = ProjectLogger(self.root)
    
    def analyze(self, show_backups: bool = True, max_tree_depth: int = 3) -> Dict:
        """Perform comprehensive project analysis"""
        print(f"\n📊 Analyzing Project: {self.root.name}")
        print("=" * 50)
        
        # Get project index
        print("\n🔍 Indexing project structure...")
        index = self.indexer.index_project()
        size_summary = self.indexer.get_size_summary(index)
        recent_changes = self.indexer.get_recent_changes(index)
        activity = self.indexer.analyze_activity(index)
        
        # Basic project stats
        print("\n📈 Project Statistics:")
        print(f"Total Files: {index['metadata']['total_files']}")
        print(f"Total Directories: {index['metadata']['total_dirs']}")
        print(f"Total Size: {format_size(size_summary['total_size'])}")
        
        # File type analysis
        print("\n📁 File Types:")
        for ext, info in sorted(size_summary['by_type'].items(), 
                              key=lambda x: x[1]['total_size'], reverse=True):
            print(f"  {ext:12} Count: {info['count']:4d}  "
                  f"Total: {format_size(info['total_size']):8}  "
                  f"Avg: {format_size(info['avg_size'])}")
        
        # Recent changes
        print("\n🕒 Recent Changes (Last 7 Days):")
        for change in recent_changes[:5]:
            print(f"  {change['modified'].strftime('%Y-%m-%d %H:%M')} - {normalize_path(change['path'])}")
        
        # Large files
        if size_summary['large_files']:
            print("\n💾 Large Files (>1MB):")
            for file in size_summary['large_files'][:5]:
                print(f"  {format_size(file['size']):8} - {normalize_path(file['path'])}")
        
        # Activity summary
        print("\n📊 Project Activity (Last 30 Days):")
        print(f"Total Changes: {activity['total_changes']}")
        
        print("\nMost Active Directories:")
        # Deduplicate and normalize paths
        active_dirs = {}
        for dir_path, count in activity['most_active_dirs']:
            norm_path = normalize_path(dir_path)
            active_dirs[norm_path] = active_dirs.get(norm_path, 0) + count
        
        for dir_path, count in sorted(active_dirs.items(), key=lambda x: (-x[1], x[0]))[:5]:
            print(f"  {count:3d} changes - {dir_path}")
        
        print("\nMost Active File Types:")
        for file_type, count in activity['most_active_types'][:5]:
            print(f"  {count:3d} changes - {file_type}")
        
        # Project structure tree with potential improvements
        print("\n📂 Project Structure Analysis:")
        
        # Track duplicate files (excluding backups)
        file_locations = {}
        for root, _, files in os.walk(self.root):
            if 'backup_' in root:
                continue
            for file in files:
                if file.endswith('.py'):  # Focus on Python files
                    rel_path = normalize_path(Path(root).relative_to(self.root))
                    file_locations.setdefault(file, []).append(rel_path)
        
        duplicates = {f: locs for f, locs in file_locations.items() if len(locs) > 1}
        if duplicates:
            print("\n⚠️ Duplicate Files Found:")
            for file, locations in duplicates.items():
                print(f"\n  {file} appears in:")
                for loc in locations:
                    print(f"    - {loc}")
        
        # Add recommendations section
        print("\n🔧 Recommendations:")
        
        # 1. Directory Structure Issues
        print("\n1. Directory Structure:")
        print("  ⚠️ Project has both 'src' and 'project_manager' directories:")
        print("  Recommended Actions:")
        print("  1. Move project_manager contents to src/:")
        print("     - project_manager/collectors/* → src/collectors/")
        print("     - project_manager/file_analyzer.py → src/core/")
        print("     - project_manager/log_manager.py → src/core/")
        print("     - project_manager/project_*.py → src/utils/")
        print("\n  2. Consolidate setup scripts:")
        print("     - Move setup_scripts/*.py to src/utils/setup/")
        print("     - Keep only one copy of each utility")
        
        # 2. File Consolidation
        if duplicates:
            print("\n2. File Consolidation:")
            print("  ⚠️ Several files exist in multiple locations. Here are the commands to fix:")
            
            print("\n  ```bash")
            print("  # Create backup first")
            print("  python setup_scripts/backup_project.py")
            print("\n  # Move and consolidate files")
            
            # Group files by type
            utils_files = []
            collector_files = []
            core_files = []
            
            for file, locations in duplicates.items():
                if file == '__init__.py':
                    continue
                
                if 'utils' in str(locations) or file.startswith('project_'):
                    utils_files.append(file)
                elif 'collectors' in str(locations):
                    collector_files.append(file)
                elif 'core' in str(locations) or file in ['logging.py', 'file_analyzer.py']:
                    core_files.append(file)
            
            # Utils consolidation
            if utils_files:
                print("\n  # Utility Files")
                print("  mkdir -p src/utils/setup")
                for f in utils_files:
                    if f == 'setup.py' and '.' in str(duplicates[f]):
                        print("  # Keep setup.py in root, remove others")
                        print(f"  rm project_manager/{f} src/utils/{f}")
                    else:
                        print(f"  mv project_manager/{f} src/utils/")
                        if f in ['project_indexer.py', 'project_manager.py']:
                            print(f"  rm setup_scripts/{f}")
            
            # Collectors consolidation
            if collector_files:
                print("\n  # Collector Files")
                for f in collector_files:
                    print(f"  mv project_manager/collectors/{f} src/collectors/")
                    print(f"  rm src/collectors/{f}")
            
            # Core files consolidation
            if core_files:
                print("\n  # Core Files")
                for f in core_files:
                    if f == 'logging.py':
                        print(f"  mv setup_scripts/{f} src/core/")
                    elif f == 'file_analyzer.py':
                        print(f"  mv project_manager/{f} src/core/")
                        print(f"  rm project_manager/{f}.bak")
            
            print("  ```")
            
            print("\n  After consolidation, verify each file's content and merge if needed.")
            print("  Some files might have different functionality despite same names.")
        
        # 3. Project Organization with improved structure
        print("\n3. Project Organization:")
        print("  Recommended Structure:")
        print("  src/                    # All source code")
        print("  ├── core/              # Core functionality")
        print("  │   ├── logging.py     # Logging configuration")
        print("  │   └── exceptions.py  # Custom exceptions")
        print("  ├── collectors/        # Data collection modules")
        print("  │   └── news_collector.py")
        print("  ├── utils/            # Utility functions")
        print("  │   ├── setup/        # Project setup utilities")
        print("  │   │   ├── project_setup.py")
        print("  │   │   └── backup_utils.py")
        print("  │   ├── analysis/     # Analysis utilities")
        print("  │   │   ├── file_analyzer.py")
        print("  │   │   └── news_analysis.py")
        print("  │   └── project_indexer.py")
        print("  └── scripts/          # Analysis scripts")
        print("")
        print("  tests/                # All test files")
        print("  ├── unit/            # Unit tests")
        print("  └── integration/     # Integration tests")
        print("")
        print("  docs/                 # Documentation")
        print("  ├── api/            # API documentation")
        print("  └── guides/         # User guides")
        print("")
        print("  datasets/             # Data storage")
        print("  output/               # Generated content")
        print("  logs/                 # Application logs")
        
        # 4. Additional Recommendations
        print("\n4. Additional Recommendations:")
        print("  Code Quality:")
        print("  • Add docstrings to all Python modules")
        print("  • Ensure consistent code style (run black formatter)")
        print("  • Add type hints to function signatures")
        
        print("\n  Project Structure:")
        print("  • Move setup.py to project root (remove duplicates)")
        print("  • Remove .bak files")
        print("  • Consolidate test files into test/unit/")
        
        print("\n  Dependencies:")
        print("  • Update requirements.txt")
        print("  • Consider using pyproject.toml")
        print("  • Add dev-requirements.txt for development dependencies")
        
        # 5. Action Plan with commands
        print("\n5. Suggested Action Plan:")
        print("  ```bash")
        print("  # 1. Create backup")
        print("  python setup_scripts/backup_project.py")
        print("\n  # 2. Reorganize directory structure")
        print("  mkdir -p src/utils/setup src/utils/analysis")
        print("  # ... (use move commands from section 2)")
        print("\n  # 3. Update imports")
        print("  # Use your IDE's refactoring tools or:")
        print("  find . -name '*.py' -exec sed -i 's/from project_manager/from src/g' {} +")
        print("\n  # 4. Run tests")
        print("  pytest")
        print("\n  # 5. Format code")
        print("  black src/ tests/ setup_scripts/")
        print("  ```")
        
        # Add a new section for Windows-specific commands
        print("\n6. Windows-Specific Commands:")
        print("  ```powershell")
        print("  # 1. Create backup")
        print("  python setup_scripts\\backup_project.py")
        print("\n  # 2. Create directories")
        print("  mkdir src\\utils\\setup, src\\utils\\analysis")
        print("\n  # 3. Move files (PowerShell)")
        print("  Move-Item project_manager\\collectors\\* src\\collectors\\")
        print("  Move-Item project_manager\\file_analyzer.py src\\core\\")
        print("  Move-Item project_manager\\log_manager.py src\\core\\")
        print("  Move-Item project_manager\\project_*.py src\\utils\\")
        print("\n  # 4. Remove duplicates")
        print("  Remove-Item project_manager\\setup.py")
        print("  Remove-Item src\\utils\\setup.py")
        print("  Remove-Item project_manager\\*.bak")
        print("\n  # 5. Update imports using PowerShell")
        print("  Get-ChildItem -Recurse -Filter *.py | ")
        print("    ForEach-Object {")
        print("      (Get-Content $_.FullName) -replace 'from project_manager', 'from src' | ")
        print("      Set-Content $_.FullName")
        print("    }")
        print("  ```")

        # Add a section for cleanup recommendations
        print("\n7. Cleanup Recommendations:")
        print("  Output Directory:")
        print("  • Consider archiving or removing old figure files")
        print("  • Current figure count: 29, Total size: 21.8 MB")
        print("  • Implement automatic cleanup for files older than X days")
        
        print("\n  Logs Directory:")
        print("  • Implement log rotation")
        print("  • Consider compressing old logs")
        print("  • Set up automated cleanup for logs older than 30 days")
        
        print("\n  Development:")
        print("  • Add .gitignore if not present")
        print("  • Consider adding pre-commit hooks for:")
        print("    - Code formatting (black)")
        print("    - Import sorting (isort)")
        print("    - Type checking (mypy)")
        
        print("\n  Testing:")
        print("  • Add test coverage reporting")
        print("  • Set up GitHub Actions for CI/CD")
        print("  • Add integration tests directory")

        # Add a section for next steps
        print("\n8. Next Steps:")
        print("  1. Review and merge duplicate files")
        print("  2. Update project documentation")
        print("  3. Set up automated testing")
        print("  4. Implement suggested cleanup procedures")
        print("  5. Create development guidelines")
        print("  6. Set up CI/CD pipeline")

        # Generate and display tree
        print("\nCurrent Structure:")
        tree = generate_tree(self.root, max_depth=max_tree_depth)
        for line in tree:
            print(normalize_path(line))
        
        # Backup information
        if show_backups:
            print("\n💾 Backup Information:")
            list_backups(self.root)
        
        return {
            'index': index,
            'size_summary': size_summary,
            'recent_changes': recent_changes,
            'activity': activity,
            'duplicates': duplicates
        }

    def generate_recommendations(self):
        print("\n🔄 Recommended Migration Steps:")
        print("\n1. Preparation:")
        print("  • Create a feature branch for reorganization")
        print("  • Review and diff duplicate files:")
        for file in ["project_indexer.py", "logging.py", "news_collector.py"]:
            print(f"    - Compare all versions of {file}")
            print(f"    - Document differences and required merges")
        
        print("\n2. Safe Migration Process:")
        print("  1. Create comprehensive tests first:")
        print("     • Add tests for any untested functionality")
        print("     • Ensure high coverage for critical files")
        print("  2. Create new directory structure")
        print("  3. Merge and migrate files (don't just move):")
        print("     • Start with core functionality")
        print("     • Maintain git history using git mv")
        print("     • Update imports as you go")
        print("  4. Run tests after each significant change")
        
        print("\n3. Output Management:")
        print("  • Implement figure archiving strategy")
        print("  • Add timestamp-based cleanup for old outputs")
        print("  • Consider compression for older files")
        
        print("\n4. Logging Strategy:")
        print("  • Centralize logging configuration")
        print("  • Implement log rotation")
        print("  • Define log retention policy")
        
        print("\n⚠️ Migration Risks:")
        print("  • Different versions of same file might have unique features")
        print("  • Import statements will need careful updating")
        print("  • Existing scripts might break during transition")
        print("  • Backup system might need reconfiguration")

    def generate_structure_updates(self):
        print("\n🔨 Structure Alignment Plan:")
        
        print("\n1. Create Missing Directories:")
        print("  ```bash")
        print("  # Core structure")
        print("  mkdir -p src/api src/handlers")
        print("  mkdir -p datasets/{processed,interim,external}")
        print("  mkdir -p docs/{api,guides,references}")
        print("  mkdir -p output/{reports,exports}")
        print("  mkdir -p config/{env,schemas}")
        print("  mkdir -p logs/{app,audit}")
        print("  ```")
        
        print("\n2. Move Existing Files:")
        print("  ```bash")
        print("  # Move tests to correct location")
        print("  mv tests src/tests")
        print("  mkdir -p src/tests/{integration,fixtures}")
        
        # Move scattered logs to centralized location
        print("  mv logs/project.log logs/app/")
        print("  mv file_analysis.log logs/app/")
        
        # Organize documentation
        print("  mv docs/cleanup_config.yaml config/")
        print("  ```")
        
        print("\n3. Update Import Paths:")
        print("  • Update all test imports to use src.tests")
        print("  • Update logging configuration to use new paths")
        print("  • Update documentation references")
        
        print("\n4. Configuration Updates:")
        print("  • Move configuration from YAML files to config/")
        print("  • Create environment-specific configs in config/env/")
        print("  • Add schema validation files in config/schemas/")
        
        print("\n5. Documentation Structure:")
        print("  • Create basic README files in each new directory")
        print("  • Move API documentation to docs/api/")
        print("  • Create initial user guides in docs/guides/")
        
        print("\n⚠️ Important Considerations:")
        print("  • Backup all data before restructuring")
        print("  • Update CI/CD pipelines to reflect new paths")
        print("  • Update .gitignore for new directory structure")
        print("  • Document all path changes for team reference")

def main():
    parser = argparse.ArgumentParser(description='Analyze project structure and activity')
    parser.add_argument('--root', type=Path, default=None,
                      help='Root directory to analyze (default: current directory)')
    parser.add_argument('--no-backups', action='store_true',
                      help='Skip backup analysis')
    parser.add_argument('--max-depth', type=int, default=3,
                      help='Maximum depth for directory tree (default: 3)')
    
    args = parser.parse_args()
    
    try:
        analyzer = ProjectAnalyzer(args.root)
        analyzer.analyze(
            show_backups=not args.no_backups,
            max_tree_depth=args.max_depth
        )
    except KeyboardInterrupt:
        print("\nAnalysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main() 