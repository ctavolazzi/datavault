import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import openai
import os
import click
import json

class AIProcessor:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI processor with OpenAI client"""
        self.logger = logging.getLogger('datavault.ai_processor')
        self.assistant_id = "asst_PUwMytINKeLj1MWFVlHAKrDu"

        # Load environment variables from .env
        from dotenv import load_dotenv
        load_dotenv()

        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            self.logger.error("OpenAI API key not found. Set OPENAI_API_KEY in .env.")
            raise ValueError("OpenAI API key not found.")

        openai.api_key = self.api_key

        try:
            self.client = openai.ChatCompletion
            self._validate_assistant()
        except Exception as e:
            self.logger.error(f"Failed to initialize AI processor: {str(e)}")
            raise

    def _validate_assistant(self):
        """Validate that we can access the specified assistant"""
        try:
            # Assuming using ChatCompletion, modify as per your OpenAI usage
            # Example: send a simple message to verify
            response = self.client.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Validate assistant."}]
            )
            self.logger.info("Successfully connected to OpenAI Assistant.")
        except Exception as e:
            self.logger.error(f"Failed to validate assistant: {str(e)}")
            raise

    def read_file(self, file_path: str) -> str:
        """Read content from a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"File not found: {path}")
                return ""
            self.logger.debug(f"Reading file: {path.resolve()}")
            content = path.read_text(encoding='utf-8')
            return content
        except Exception as e:
            self.logger.error(f"Failed to read file: {str(e)}")
            return ""

    def scrape_url(self, url: str) -> str:
        """Scrape content from a URL."""
        try:
            self.logger.debug(f"Scraping URL: {url}")
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            # Extract text content; customize as needed
            content = soup.get_text(separator='\n', strip=True)
            return content
        except Exception as e:
            self.logger.error(f"Failed to scrape URL: {str(e)}")
            return ""

    def analyze_content(self, content: str, timeout: float = 30.0, stream: bool = False) -> Dict[str, Any]:
        """Analyze the content using OpenAI API."""
        if not content:
            self.logger.error("No content provided for analysis.")
            return {}

        try:
            self.logger.info("Sending content to OpenAI for analysis.")

            # Define the messages for the chat completion
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Please analyze the following content:\n\n{content}"}
            ]

            # Call the OpenAI API
            response = self.client.create(
                model="gpt-3.5-turbo",
                messages=messages,
                timeout=timeout,
                stream=stream
            )

            if stream:
                # Handle streaming responses
                analysis = ""
                click.echo(click.style("\n🔍 AI Analysis Results", fg='bright_blue', bold=True))
                click.echo("─" * 80)
                for chunk in response:
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0]['delta']
                        if 'content' in delta:
                            analysis += delta['content']
                            click.echo(delta['content'], nl=False)
                click.echo("\n" + "─" * 80)
                return {"analysis": analysis}
            else:
                # Complete response
                analysis_text = response.choices[0].message['content'].strip()
                return {"analysis": analysis_text}
        except Exception as e:
            self.logger.error(f"AI analysis failed: {str(e)}")
            return {}

    def display_analysis(self, analysis: Dict[str, Any]):
        """Display the analysis results with colored output."""
        if not analysis:
            click.echo(click.style("❌ No analysis available.", fg='red'))
            return

        click.echo(click.style("\n🔍 AI Analysis Results", fg='bright_blue', bold=True))
        click.echo("─" * 80)
        for key, value in analysis.items():
            click.echo(click.style(f"\n{key.capitalize()}:\n", fg='green', bold=True))
            click.echo(click.style(value, fg='white'))
        click.echo("─" * 80)