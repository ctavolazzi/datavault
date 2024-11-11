import click
import logging
from pathlib import Path
import re
import sys
from ..ai_processor import AIProcessor
from ..utils.errors import handle_error

logger = logging.getLogger('datavault.analyze')

@click.command()
@click.argument('input_source', required=True)
@handle_error
def analyze(input_source):
    """Analyze a file or URL using AI."""
    logger.info(f"Analyzing input source: {input_source}")

    processor = AIProcessor()
    content = ""

    # Determine if input_source is a URL or a file
    if re.match(r'^(http|https)://', input_source):
        # It's a URL
        logger.info("Input source is a URL.")
        content = processor.scrape_url(input_source)
    else:
        # Assume it's a file path
        logger.info("Input source is a file path.")
        content = processor.read_file(input_source)

    if not content:
        click.echo(click.style("No content to analyze.", fg='red'))
        sys.exit(1)

    # Analyze the content
    analysis = processor.analyze_content(content)

    # Display the analysis
    processor.display_analysis(analysis)