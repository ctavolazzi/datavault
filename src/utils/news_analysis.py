from pathlib import Path
import json
from datetime import datetime
from collections import Counter
import re
from typing import Dict, List, Set
from ..core import get_logger

logger = get_logger(__name__)

def extract_keywords(text: str, min_length: int = 4) -> Set[str]:
    """Extract meaningful keywords from text"""
    if not text:
        return set()
    # Convert to lowercase and split into words
    words = re.findall(r'\b\w+\b', text.lower())
    # Filter out common words and short words
    stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'says'}
    return {w for w in words if len(w) >= min_length and w not in stopwords}

def analyze_news_file(file_path: Path) -> Dict:
    """Analyze a news data file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data['articles']
    
    # Extract all keywords from titles and descriptions
    all_keywords = set()
    for article in articles:
        all_keywords.update(extract_keywords(article['title']))
        all_keywords.update(extract_keywords(article.get('description', '')))
    
    # Count keyword frequency
    keyword_freq = Counter()
    for article in articles:
        keywords = extract_keywords(article['title'])
        keywords.update(extract_keywords(article.get('description', '')))
        keyword_freq.update(keywords)
    
    # Basic analysis
    analysis = {
        'total_articles': len(articles),
        'sources': Counter(article['source'] for article in articles),
        'has_description': sum(1 for a in articles if a.get('description')),
        'time_range': {
            'earliest': min(article['publishedAt'] for article in articles),
            'latest': max(article['publishedAt'] for article in articles)
        },
        'top_keywords': dict(keyword_freq.most_common(10)),
        'collected_at': data.get('collected_at', 'unknown')
    }
    
    return analysis

def print_analysis(analysis: Dict) -> None:
    """Print analysis results"""
    print("\nNews Analysis:")
    print(f"Collected at: {analysis['collected_at']}")
    print(f"Total Articles: {analysis['total_articles']}")
    print(f"Articles with descriptions: {analysis['has_description']}")
    
    print("\nTime Range:")
    print(f"Earliest: {analysis['time_range']['earliest']}")
    print(f"Latest: {analysis['time_range']['latest']}")
    
    print("\nTop Sources:")
    for source, count in sorted(analysis['sources'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"- {source}: {count} articles")
    
    print("\nTop Keywords:")
    for keyword, count in analysis['top_keywords'].items():
        print(f"- {keyword}: {count} occurrences")

def analyze_trends(analyses: List[Dict]) -> Dict:
    """Analyze trends across collections"""
    trends = {
        'new_sources': [],
        'keyword_changes': [],
        'coverage_changes': []
    }
    
    if len(analyses) < 2:
        return trends
    
    # Sort by collection time
    analyses.sort(key=lambda x: x['collected_at'])
    
    for i in range(1, len(analyses)):
        prev = analyses[i-1]
        curr = analyses[i]
        
        # Check for new sources
        prev_sources = set(prev['sources'].keys())
        curr_sources = set(curr['sources'].keys())
        new_sources = curr_sources - prev_sources
        if new_sources:
            trends['new_sources'].append({
                'time': curr['collected_at'],
                'sources': list(new_sources)
            })
        
        # Check keyword changes
        prev_keywords = set(prev['top_keywords'].keys())
        curr_keywords = set(curr['top_keywords'].keys())
        new_keywords = curr_keywords - prev_keywords
        if new_keywords:
            trends['keyword_changes'].append({
                'time': curr['collected_at'],
                'new_keywords': list(new_keywords)
            })
        
        # Check coverage changes
        for source in curr_sources & prev_sources:
            prev_count = prev['sources'][source]
            curr_count = curr['sources'][source]
            if curr_count != prev_count:
                trends['coverage_changes'].append({
                    'time': curr['collected_at'],
                    'source': source,
                    'change': curr_count - prev_count
                })
    
    return trends

def print_trend_analysis(analyses: List[Dict]) -> None:
    """Print trend analysis across multiple collections"""
    if not analyses:
        print("No collections found to analyze")
        return
    
    trends = analyze_trends(analyses)
    
    print("\nTrend Analysis:")
    print(f"Number of collections: {len(analyses)}")
    
    if trends['new_sources']:
        print("\nNew Sources Appeared:")
        for change in trends['new_sources']:
            print(f"At {change['time']}:")
            for source in change['sources']:
                print(f"- {source}")
    
    if trends['keyword_changes']:
        print("\nNew Keywords Emerged:")
        for change in trends['keyword_changes']:
            print(f"At {change['time']}:")
            for keyword in change['new_keywords']:
                print(f"- {keyword}")
    
    if trends['coverage_changes']:
        print("\nCoverage Changes:")
        for change in trends['coverage_changes']:
            direction = "increased" if change['change'] > 0 else "decreased"
            print(f"- {change['source']} {direction} by {abs(change['change'])} at {change['time']}")