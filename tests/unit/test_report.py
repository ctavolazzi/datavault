import pytest
from pathlib import Path
import webbrowser
from unittest.mock import Mock, patch
from src.utils.report import NewsReport

@pytest.fixture
def sample_analysis():
    """Sample analysis data for testing"""
    return {
        'total_articles': 20,
        'time_range': {
            'earliest': '2024-11-02T20:52:32Z',
            'latest': '2024-11-03T02:04:29Z'
        },
        'sources': {
            'BBC News': 2,
            'Associated Press': 2,
            'CBS News': 2
        },
        'top_keywords': {
            'test': 5,
            'news': 3
        }
    }

@pytest.fixture
def report():
    """Fresh report instance for each test"""
    return NewsReport()

def test_report_generation_basic(report, sample_analysis):
    """Test basic report generation without browser"""
    paths = report.generate_report(sample_analysis, format='both')
    assert isinstance(paths, tuple)
    assert len(paths) == 2
    assert (report.report_dir / "report.md").exists()
    assert (report.report_dir / "report.html").exists()

def test_browser_view_option(report, sample_analysis):
    """Test browser viewing option"""
    with patch('webbrowser.open') as mock_open:
        # Generate with browser view
        report.generate_report(analysis=sample_analysis, 
                             format='html', 
                             view_in_browser=True)
        
        # Verify browser was opened
        mock_open.assert_called_once()
        called_path = mock_open.call_args[0][0]
        assert str(report.report_dir) in called_path
        assert called_path.endswith('report.html')

def test_browser_view_missing_file(report):
    """Test browser view with missing file"""
    with patch('webbrowser.open') as mock_open:
        report.open_in_browser()  # No file generated yet
        mock_open.assert_not_called()

def test_cli_browser_option():
    """Test CLI browser option integration"""
    with patch('webbrowser.open') as mock_open:
        with patch('src.scripts.test_news_collection.test_collection') as mock_test:
            from src.scripts.test_news_collection import main
            main(['--browser'])
            mock_test.assert_called_once_with(force=False, view_browser=True) 