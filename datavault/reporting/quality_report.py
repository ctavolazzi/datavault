from pathlib import Path
import matplotlib.pyplot as plt
from jinja2 import Template

class QualityReport:
    def __init__(self, results: dict, trends: dict):
        self.results = results
        self.trends = trends

    def generate_html(self, template_path: Path) -> str:
        with open(template_path, 'r') as f:
            template = Template(f.read())
        
        return template.render(
            results=self.results,
            trends=self.trends,
            summary=self._generate_summary(),
            charts=self._generate_charts()
        )

    def _generate_summary(self) -> dict:
        total_files = len(self.results)
        total_issues = sum(
            r.get('lint', {}).get('issues_count', 0) 
            for r in self.results.values()
        )
        avg_complexity = sum(
            r.get('complexity', {}).get('average_complexity', 0) 
            for r in self.results.values()
        ) / total_files if total_files else 0

        return {
            'total_files': total_files,
            'total_issues': total_issues,
            'average_complexity': round(avg_complexity, 2)
        }

    def _generate_charts(self) -> dict:
        # Generate various charts using matplotlib
        # Save them as base64 strings for HTML embedding
        pass 