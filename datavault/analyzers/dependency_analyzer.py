from pathlib import Path
import ast
from typing import Dict, List, Tuple
import click

class DependencyAnalyzer:
    """Analyze Python file dependencies"""
    
    def __init__(self, files: List[Path]):
        self.files = files
        self.module_map = self._build_module_map()
    
    def _build_module_map(self) -> Dict[str, Dict[str, str]]:
        """Create a mapping of module names to file paths"""
        module_map = {}
        for file in self.files:
            module_name = file.stem
            module_map[module_name] = {
                'abs': str(file.absolute()),
                'rel': str(file.relative_to(Path.cwd()))
            }
        return module_map
    
    def analyze_dependencies(self, debug: bool = False) -> Dict[str, List[str]]:
        """Analyze internal dependencies between Python files"""
        if debug:
            click.echo("Starting dependency analysis")
        
        internal_deps = {}
        
        for file in self.files:
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
                            if base_module in self.module_map:
                                internal_deps[file_path].add(
                                    self.module_map[base_module]['rel']
                                )
                    
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        base_module = node.module.split('.')[0]
                        if base_module in self.module_map:
                            internal_deps[file_path].add(
                                self.module_map[base_module]['rel']
                            )
            
            except Exception as e:
                if debug:
                    click.echo(f"\n⚠️  Error parsing {file_path}: {str(e)}")
                continue
        
        # Convert sets to sorted lists and remove empty dependencies
        return {k: sorted(v) for k, v in internal_deps.items() if v}