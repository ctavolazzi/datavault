import matplotlib.pyplot as plt
from pathlib import Path
import json
from typing import List, Dict
from datetime import datetime
from collections import Counter
from ..core import get_logger
import numpy as np
import nltk
from nltk.corpus import stopwords

logger = get_logger(__name__)

class NewsVisualizer:
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("output/figures")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        plt.style.use('default')
    
    def plot_source_distribution(self, data: Dict) -> Path:
        """Create a bar plot of news sources"""
        plt.figure(figsize=(12, 8))
        
        # Count sources and sort by frequency
        sources = Counter(article['source'] for article in data['articles'])
        sources_sorted = dict(sorted(sources.items(), key=lambda x: x[1], reverse=True))
        
        # Colors and style
        colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(sources_sorted)))
        
        # Create bar plot
        bars = plt.bar(range(len(sources_sorted)), 
                      sources_sorted.values(),
                      color=colors)
        
        # Customize appearance
        plt.title('Distribution of News Sources', fontsize=14, pad=20)
        plt.xlabel('Source', fontsize=12, labelpad=10)
        plt.ylabel('Number of Articles', fontsize=12, labelpad=10)
        
        # Rotate labels and adjust layout
        plt.xticks(range(len(sources_sorted)), 
                   sources_sorted.keys(), 
                   rotation=45,
                   ha='right')
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom')
        
        # Add collection timestamp
        plt.figtext(0.99, 0.01, 
                    f'Collected: {data["collected_at"][:16]}',
                    ha='right', 
                    fontsize=8, 
                    style='italic')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save plot
        output_path = self.output_dir / f"sources_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Generated source distribution plot: {output_path}")
        return output_path
    
    def plot_keyword_trends(self, data: Dict) -> Path:
        """Create a word cloud of keywords"""
        from wordcloud import WordCloud
        
        # Download required NLTK data
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        # Combine all text
        text = " ".join(
            f"{article['title']} {article.get('description', '')}"
            for article in data['articles']
        )
        
        # Custom stopwords
        stop_words = set(stopwords.words('english'))
        custom_stops = {'says', 'said', 'would', 'could', 'may', 'also', 'one', 'two', 'first'}
        stop_words.update(custom_stops)
        
        # Generate word cloud
        wordcloud = WordCloud(
            width=1600,
            height=800,
            background_color='white',
            max_words=100,
            stopwords=stop_words,
            colormap='viridis',
            min_font_size=10,
            max_font_size=150,
            prefer_horizontal=0.7
        ).generate(text.lower())
        
        # Create figure
        plt.figure(figsize=(16, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        
        # Add title and timestamp
        plt.title('News Keywords Visualization', 
                  fontsize=16, 
                  pad=20)
        
        plt.figtext(0.99, 0.01, 
                    f'Collected: {data["collected_at"][:16]}',
                    ha='right', 
                    fontsize=8, 
                    style='italic')
        
        # Save plot
        output_path = self.output_dir / f"keywords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Generated keyword cloud: {output_path}")
        return output_path
    
    def plot_publication_timeline(self, data: Dict) -> Path:
        """Create a timeline of article publications"""
        # Convert timestamps to datetime
        timestamps = [datetime.fromisoformat(article['publishedAt'].rstrip('Z'))
                     for article in data['articles']]
        
        # Create figure
        plt.figure(figsize=(12, 6))
        
        # Plot timeline
        plt.hist(timestamps, bins=12, color='skyblue', alpha=0.7)
        
        # Customize appearance
        plt.title('Article Publication Timeline', fontsize=14, pad=20)
        plt.xlabel('Publication Time (UTC)', fontsize=12, labelpad=10)
        plt.ylabel('Number of Articles', fontsize=12, labelpad=10)
        
        # Rotate x-axis labels
        plt.xticks(rotation=30, ha='right')
        
        # Add collection timestamp
        plt.figtext(0.99, 0.01, 
                    f'Collected: {data["collected_at"][:16]}',
                    ha='right', 
                    fontsize=8, 
                    style='italic')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save plot
        output_path = self.output_dir / f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Generated publication timeline: {output_path}")
        return output_path

def main():
    """Generate visualizations for latest collection"""
    try:
        # Get latest collection
        data_dir = Path("datasets/news/raw")
        latest_file = sorted(data_dir.glob("*.json"))[-1]
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create visualizations
        visualizer = NewsVisualizer()
        sources_plot = visualizer.plot_source_distribution(data)
        keywords_plot = visualizer.plot_keyword_trends(data)
        timeline_plot = visualizer.plot_publication_timeline(data)
        
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")
        raise

if __name__ == "__main__":
    main() 