import pytest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import json
from src.ai_analyzer.ai_processor import AIProcessor

@pytest.fixture
def mock_openai_client():
    with patch('openai.OpenAI') as mock:
        # Set up the mock client
        mock_client = Mock()
        mock.return_value = mock_client

        # Set up the response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test analysis"))]
        mock_client.chat.completions.create.return_value = mock_response

        yield mock

def test_save_analysis(mock_openai_client, tmp_path):
    """Test saving analysis results"""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        processor = AIProcessor()

        # Test analysis
        result = processor.analyze_data("test data")
        assert result == "Test analysis"

        # Test saving
        save_path = tmp_path / "analysis.txt"
        processor.save_analysis(result, save_path)
        assert save_path.exists()
        assert save_path.read_text() == "Test analysis"