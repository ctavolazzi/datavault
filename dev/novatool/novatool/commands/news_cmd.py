from rich.console import Console
import typer
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv
import ollama
import openai
from datetime import datetime
from ..utils.ai_config import AIConfig, AIService

console = Console()
load_dotenv()

def get_news_summary(
    topic: str = typer.Option(None, help="Topic to search for (optional)"),
    ai_service: str = typer.Option("ollama", help="AI service to use (ollama/openai)"),
    limit: int = typer.Option(5, help="Number of articles to summarize")
):
    """Get and summarize top news headlines"""
    try:
        console.print(f"[bold blue]Fetching news{'about ' + topic if topic else ''}...[/]")

        # Initialize NewsAPI
        newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))

        # Get headlines
        if topic:
            headlines = newsapi.get_top_headlines(q=topic, language='en', page_size=limit)
        else:
            headlines = newsapi.get_top_headlines(language='en', page_size=limit)

        if not headlines['articles']:
            console.print("[yellow]No headlines found.[/]")
            return

        # Print raw headlines first
        console.print("\n[bold green]Latest Headlines:[/]")
        for idx, article in enumerate(headlines['articles'], 1):
            console.print(f"\n[cyan]{idx}. {article['title']}[/]")
            console.print(f"   Source: {article['source']['name']}")
            if article['description']:
                console.print(f"   {article['description']}")

        # Prepare text for summarization
        articles_text = "\n\n".join([
            f"Headline: {article['title']}\n"
            f"Source: {article['source']['name']}\n"
            f"Description: {article['description']}"
            for article in headlines['articles']
        ])

        summary_prompt = f"""Summarize these news headlines into a brief, coherent report:

{articles_text}

Please provide:
1. A brief overview
2. Key points
3. Any notable trends or patterns"""

        console.print(f"\n[bold blue]Generating summary using {ai_service}...[/]")

        # Get summary using specified AI service
        if ai_service == "ollama":
            service = AIService.OLLAMA
            model = AIConfig.get_model(service)

            # Check if model is available
            available_models = AIConfig.get_available_models(service)
            if model not in available_models:
                fallback = AIConfig.get_fallback_model(service)
                console.print(f"[yellow]Model {model} not found, falling back to {fallback}[/]")
                model = fallback

            response = ollama.generate(
                model=model,
                prompt=summary_prompt
            )
            summary = response['response']

        elif ai_service == "openai":
            service = AIService.OPENAI
            model = AIConfig.get_model(service)

            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful news summarizer."},
                    {"role": "user", "content": summary_prompt}
                ]
            )
            summary = response.choices[0].message['content']

        # Print results
        console.print("\n[bold green]AI Summary Report[/]")
        console.print("[bold blue]" + "─" * 50 + "[/]")
        console.print(f"[italic]Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]")
        console.print(f"[italic]Using {ai_service} service with model {model}[/]\n")
        console.print(summary)
        console.print("[bold blue]" + "─" * 50 + "[/]")

    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/]")

if __name__ == "__main__":
    typer.run(get_news_summary)