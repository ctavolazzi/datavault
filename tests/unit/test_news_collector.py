import pytest
from datetime import datetime
from pathlib import Path
import json

from src.collectors.news_collector import NewsDataset

@pytest.fixture
def mock_news_data():
    return {
        "status": "ok",
        "totalResults": 2,
        "articles": [
            {
                "source": {"id": "bbc", "name": "BBC News"},
                "title": "Test Article 1",
                "description": "Test Description 1",
                "url": "https://example.com/1",
                "publishedAt": "2024-11-03T12:00:00Z",
                "content": "Full content 1"
            },
            {
                "source": {"id": "cnn", "name": "CNN"},
                "title": "Test Article 2",
                "description": "Test Description 2",
                "url": "https://example.com/2",
                "publishedAt": "2024-11-03T13:00:00Z",
                "content": "Full content 2"
            }
        ]
    }

@pytest.fixture
def news_dataset(tmp_path):
    return NewsDataset(
        api_key="test_key",
        base_path=tmp_path
    )

def test_news_dataset_initialization(news_dataset):
    assert news_dataset.metadata.name == "news"
    assert "news" in news_dataset.metadata.tags
    assert news_dataset.metadata.source == "newsapi.org"

def test_process_articles(news_dataset, mock_news_data):
    processed = news_dataset.process_articles(mock_news_data)
    
    assert len(processed['articles']) == 2
    article = processed['articles'][0]
    assert set(article.keys()) == {'title', 'description', 'url', 'source', 'publishedAt'}
    assert article['source'] == "BBC News"

def test_save_articles(news_dataset, mock_news_data):
    processed = news_dataset.process_articles(mock_news_data)
    saved_path = news_dataset.save_articles(processed)
    
    assert saved_path.exists()
    assert saved_path.parent.name == "raw"
    
    # Verify saved content
    with open(saved_path) as f:
        saved_data = json.load(f)
    assert saved_data['totalResults'] == 2
    assert len(saved_data['articles']) == 2 