import ast
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List
import click
import json

import radon.complexity as cc
from radon.visitors import ComplexityVisitor
from pylint import epylint as lint

from datavault.config.quality_config import QualityConfig
from datavault.analysis.cache import AnalysisCache
from datavault.analysis.trends import QualityTrends
from datavault.vcs.git_integration import GitIntegration

class CodeQualityAnalyzer:
    def __init__(self, config: QualityConfig, cache: AnalysisCache = None, 
                 trends: QualityTrends = None, vcs: GitIntegration = None):
        self.config = config
        self.cache = cache
        self.trends = trends
        self.vcs = vcs

    def analyze_file(self, file_path: Path) -> dict:
        # Check cache first
        if self.cache:
            cached = self.cache.get_cached_result(file_path)
            if cached:
                return cached

        # Perform analysis
        results = super().analyze_file(file_path)

        # Store results
        if self.cache:
            self.cache.cache_result(file_path, results)
        if self.trends:
            self.trends.store_metrics(str(file_path), results)

        return results
    
    def analyze_complexity(self, content: str) -> Dict[str, Any]:
        """Analyze code complexity"""
        try:
            complexity_visitor = ComplexityVisitor.from_code(content)
            classes = complexity_visitor.classes
            functions = complexity_visitor.functions
            
            all_complexities = [c.complexity for c in classes + functions]
            avg_complexity = sum(all_complexities) / len(all_complexities) if all_complexities else 0
            
            complex_items = [
                (item.name, item.complexity)
                for item in classes + functions
                if item.complexity > self.config.thresholds['complexity']
            ]
            
            return {
                'average_complexity': round(avg_complexity, 2),
                'max_complexity': max(all_complexities) if all_complexities else 0,
                'complex_items': complex_items
            }
        except Exception as e:
            return {'error': f'Complexity analysis failed: {str(e)}'}
    
    def find_duplicates(self, content: str) -> Dict[str, Any]:
        """Find duplicate code blocks"""
        def get_code_blocks(content: str) -> List[str]:
            blocks = []
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        blocks.append(ast.get_source_segment(content, node))
            except:
                pass
            return blocks
        
        blocks = get_code_blocks(content)
        duplicates = defaultdict(list)
        
        for i, block1 in enumerate(blocks):
            normalized1 = re.sub(r'\s+', ' ', block1.strip())
            if len(normalized1) < self.config.thresholds['duplication_length']:
                continue
                
            for j, block2 in enumerate(blocks[i+1:], i+1):
                normalized2 = re.sub(r'\s+', ' ', block2.strip())
                if normalized1 == normalized2:
                    duplicates[normalized1].extend([i, j])
        
        return {
            'duplicate_blocks': len(duplicates),
            'details': [{'block': k[:100] + '...', 'occurrences': len(set(v))} 
                       for k, v in duplicates.items()]
        }
    
    def run_lint(self, file_path: Path) -> Dict[str, Any]:
        """Run pylint on file"""
        try:
            (pylint_stdout, pylint_stderr) = lint.py_run(
                str(file_path), return_std=True
            )
            
            issues = []
            for line in pylint_stdout.readlines():
                if ':' in line and any(level in line for level in ['C', 'W', 'E', 'F']):
                    issues.append(line.strip())
            
            return {
                'issues_count': len(issues),
                'issues': issues[:5]
            }
        except Exception as e:
            return {'error': f'Lint analysis failed: {str(e)}'}

class ResultFormatter:
    @staticmethod
    def format_results(results: Dict[str, Any], threshold: int, format_type: str = 'text') -> str:
        if format_type == 'json':
            return json.dumps(results, indent=2)
        
        output = []
        for file_path, metrics in results.items():
            output.append(f"\n📄 {file_path}")
            output.append("-" * 50)
            
            if 'complexity' in metrics:
                complexity = metrics['complexity']
                if 'error' not in complexity:
                    output.append("\n🔄 Complexity Metrics:")
                    output.append(f"  Average Complexity: {complexity['average_complexity']}")
                    output.append(f"  Max Complexity: {complexity['max_complexity']}")
                    
                    if complexity['complex_items']:
                        output.append(f"\n  ⚠️  Items exceeding threshold ({threshold}):")
                        for name, score in complexity['complex_items']:
                            output.append(f"    - {name}: {score}")
            
            # ... similar formatting for duplication and lint results ...
        
        return '\n'.join(output) 