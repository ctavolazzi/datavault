from pathlib import Path
from datetime import datetime
import json
import shutil
import webbrowser
from typing import Dict, List, Any, Union, Tuple
from ..core import get_logger

logger = get_logger(__name__)

class ReportTemplate:
    """Handles report templating and styling"""
    
    DEFAULT_STYLES = {
        'body': {
            'font-family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            'line-height': '1.6',
            'max-width': '1200px',
            'margin': '0 auto',
            'padding': '20px',
            'color': '#24292e'
        },
        'img': {
            'max-width': '100%',
            'margin': '20px 0',
            'border': '1px solid #e1e4e8',
            'border-radius': '6px',
            'box-shadow': '0 1px 2px rgba(0,0,0,0.1)'
        },
        'section': {
            'margin': '30px 0'
        },
        'metadata': {
            'background': '#f5f5f5',
            'padding': '15px',
            'border-radius': '5px',
            'margin': '20px 0'
        }
    }
    
    def __init__(self):
        self.styles = self.DEFAULT_STYLES
    
    def generate_css(self) -> str:
        """Convert style dictionary to CSS string"""
        css = []
        for selector, properties in self.styles.items():
            css.append(f"{selector} {{")
            for prop, value in properties.items():
                css.append(f"    {prop}: {value};")
            css.append("}")
        return "\n".join(css)

class NewsReport:
    """Handles report generation and organization"""
    
    def __init__(self):
        # Create report directory with timestamp
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.report_dir = Path(f"reports/news_report_{self.timestamp}")
        self.template = ReportTemplate()
        
        # Create directory structure
        self.report_dir.mkdir(parents=True, exist_ok=True)
        (self.report_dir / "images").mkdir(exist_ok=True)
        (self.report_dir / "data").mkdir(exist_ok=True)
    
    def save_data(self, data: Dict[str, Any], filename: str) -> Path:
        """Save JSON data to the report directory"""
        output_path = self.report_dir / "data" / f"{filename}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return output_path
    
    def save_image(self, image_path: Path, name: str) -> Path:
        """Save an image to the report directory"""
        dest_path = self.report_dir / "images" / f"{name}.png"
        shutil.copy2(image_path, dest_path)
        return dest_path
    
    def generate_report(self, analysis: Dict[str, Any], format: str = 'both', view_in_browser: bool = False) -> Union[Path, Tuple[Path, Path]]:
        """
        Generate report in specified format
        
        Args:
            analysis: Analysis data dictionary
            format: Output format ('html', 'markdown', or 'both')
            view_in_browser: Whether to open HTML report in browser after generation
        
        Returns:
            Path to the generated report(s)
        """
        if format not in ('html', 'markdown', 'both'):
            raise ValueError(f"Unsupported format: {format}")
        
        paths = []
        if format in ('markdown', 'both'):
            paths.append(self._generate_markdown(analysis))
        if format in ('html', 'both'):
            html_path = self._generate_html(analysis)
            paths.append(html_path)
            if view_in_browser:
                self.open_in_browser()
        
        return paths[0] if len(paths) == 1 else tuple(paths)
    
    def _generate_markdown(self, analysis: Dict[str, Any]) -> Path:
        """Generate markdown report"""
        content = f"""# News Analysis Report

## Collection Information
- Report Generated: {datetime.now().isoformat()}
- Articles Collected: {analysis['total_articles']}
- Collection Period: {analysis['time_range']['earliest']} to {analysis['time_range']['latest']}

## Source Distribution
![Source Distribution](images/sources.png)

## Keyword Analysis
![Keyword Cloud](images/keywords.png)

## Publication Timeline
![Publication Timeline](images/timeline.png)

## Top Sources
{self._format_sources(analysis['sources'])}

## Top Keywords
{self._format_keywords(analysis['top_keywords'])}
"""
        report_path = self.report_dir / "report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return report_path
    
    def _generate_html(self, analysis: Dict[str, Any]) -> Path:
        """Generate HTML report"""
        content = f"""<!DOCTYPE html>
<html>
<head>
    <title>News Analysis Report - {self.timestamp}</title>
    <style>
        {self.template.generate_css()}
    </style>
</head>
<body>
    <h1>News Analysis Report</h1>
    
    <div class="metadata">
        <h2>Collection Information</h2>
        <ul>
            <li>Report Generated: {datetime.now().isoformat()}</li>
            <li>Articles Collected: {analysis['total_articles']}</li>
            <li>Collection Period: {analysis['time_range']['earliest']} to {analysis['time_range']['latest']}</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Source Distribution</h2>
        <img src="images/sources.png" alt="Source Distribution">
    </div>
    
    <div class="section">
        <h2>Keyword Analysis</h2>
        <img src="images/keywords.png" alt="Keyword Cloud">
    </div>
    
    <div class="section">
        <h2>Publication Timeline</h2>
        <img src="images/timeline.png" alt="Publication Timeline">
    </div>
    
    <div class="section">
        <h2>Top Sources</h2>
        {self._format_sources_html(analysis['sources'])}
    </div>
    
    <div class="section">
        <h2>Top Keywords</h2>
        {self._format_keywords_html(analysis['top_keywords'])}
    </div>
    
    <div class="section">
        <h2>Raw Data</h2>
        <ul>
            <li><a href="data/analysis.json">Analysis Data (JSON)</a></li>
            <li><a href="data/raw_news.json">Raw News Data (JSON)</a></li>
        </ul>
    </div>
</body>
</html>"""
        
        report_path = self.report_dir / "report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return report_path
    
    def _format_sources(self, sources: Dict[str, int]) -> str:
        """Format source information for markdown"""
        sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)
        return "\n".join(f"- {source}: {count} articles" 
                        for source, count in sorted_sources[:5])
    
    def _format_keywords(self, keywords: Dict[str, int]) -> str:
        """Format keyword information for markdown"""
        return "\n".join(f"- {keyword}: {count} occurrences" 
                        for keyword, count in keywords.items())
    
    def _format_sources_html(self, sources: Dict[str, int]) -> str:
        """Format source information for HTML"""
        sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)
        return "<ul>" + "\n".join(
            f"<li><strong>{source}</strong>: {count} articles</li>" 
            for source, count in sorted_sources[:5]
        ) + "</ul>"
    
    def _format_keywords_html(self, keywords: Dict[str, int]) -> str:
        """Format keyword information for HTML"""
        return "<ul>" + "\n".join(
            f"<li><strong>{keyword}</strong>: {count} occurrences</li>" 
            for keyword, count in keywords.items()
        ) + "</ul>"
    
    def open_in_browser(self) -> None:
        """Open the HTML report in the default web browser"""
        html_path = self.report_dir / "report.html"
        if html_path.exists():
            try:
                webbrowser.open(html_path.absolute().as_uri())
                logger.info(f"Opened report in browser: {html_path}")
            except Exception as e:
                logger.error(f"Failed to open report in browser: {e}")
        else:
            logger.error("HTML report not found")