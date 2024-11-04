from pathlib import Path
from typing import List, Dict
from ..utils.news_analysis import analyze_news_file, print_analysis
from ..core import get_logger, setup_logging

logger = get_logger(__name__)

def analyze_collections(data_dir: Path = None) -> List[Dict]:
    """Analyze all news collections in the data directory"""
    if data_dir is None:
        data_dir = Path("datasets/news/raw")
    
    # Get all JSON files, sorted by name (which includes timestamp)
    files = sorted(data_dir.glob("*.json"))
    
    analyses = []
    for file_path in files:
        try:
            analysis = analyze_news_file(file_path)
            analysis['file_name'] = file_path.name
            analyses.append(analysis)
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
    
    return analyses

def print_trend_analysis(analyses: List[Dict]) -> None:
    """Print trend analysis across multiple collections"""
    if not analyses:
        print("No collections found to analyze")
        return
    
    print("\nTrend Analysis:")
    print(f"Number of collections: {len(analyses)}")
    
    # Source trends
    all_sources = set()
    for analysis in analyses:
        all_sources.update(analysis['sources'].keys())
    
    print("\nSource Consistency:")
    for source in sorted(all_sources):
        appearances = sum(1 for a in analyses if source in a['sources'])
        if appearances > 1:
            print(f"- {source}: appeared in {appearances}/{len(analyses)} collections")

def main():
    setup_logging()
    
    try:
        analyses = analyze_collections()
        
        # Print individual analyses
        for analysis in analyses:
            print(f"\n=== Analysis for {analysis['file_name']} ===")
            print_analysis(analysis)
        
        # Print trend analysis
        print_trend_analysis(analyses)
        
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        raise

if __name__ == "__main__":
    main() 