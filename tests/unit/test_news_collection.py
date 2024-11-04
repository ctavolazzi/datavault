import os
from pathlib import Path
from dotenv import load_dotenv
from project_manager.collectors.news_collector import NewsDataset
from ..utils.news_analysis import analyze_news_file, print_analysis
from ..core import get_logger, setup_logging
from ..utils.visualize import NewsVisualizer
from ..utils.cleanup import cleanup_collections
from ..utils.setup import setup_nltk
from ..utils.report import NewsReport

logger = get_logger(__name__)

def test_collection(force: bool = False, view_browser: bool = False):
    """
    Test news collection process
    
    Args:
        force (bool): Force new data collection
        view_browser (bool): Open report in browser when done
    """
    setup_logging()
    load_dotenv()
    
    try:
        # Setup
        setup_nltk()
        cleanup_collections()
        
        # Initialize collector and report
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key:
            raise ValueError("NEWS_API_KEY environment variable not set")
        
        news = NewsDataset(api_key=api_key)
        report = NewsReport()
        
        # Collect and process
        raw_news = news.fetch_articles(force=force)
        processed_news = news.process_articles(raw_news)
        
        # Save raw data
        saved_path = news.save_articles(processed_news)
        report.save_data(processed_news, "raw_news")
        
        # Analyze
        analysis = analyze_news_file(saved_path)
        report.save_data(analysis, "analysis")
        
        # Generate visualizations
        visualizer = NewsVisualizer()
        
        # Save visualizations to report
        report.save_image(
            visualizer.plot_source_distribution(processed_news),
            "sources"
        )
        report.save_image(
            visualizer.plot_keyword_trends(processed_news),
            "keywords"
        )
        report.save_image(
            visualizer.plot_publication_timeline(processed_news),
            "timeline"
        )
        
        # Generate final reports
        report.generate_report(analysis, format='both', view_in_browser=view_browser)
        
        logger.info("News collection and analysis complete")
        if not view_browser:
            logger.info(f"To view report, open: {report.report_dir}/report.html")
            
    except Exception as e:
        logger.error(f"Error in news collection: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect and analyze news data')
    parser.add_argument('--force', '-f', action='store_true', 
                       help='Force new data collection')
    parser.add_argument('--browser', '-b', action='store_true',
                       help='Open report in browser when complete')
    
    args = parser.parse_args()
    test_collection(force=args.force, view_browser=args.browser) 