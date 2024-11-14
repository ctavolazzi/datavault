from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.status import Status
import typer
from openai import OpenAI
import ollama
import datetime
from ..utils.ai_config import AIConfig, AIService
from typing import Optional
import sys
from dotenv import load_dotenv
import requests
import os
import subprocess
from typing import Dict
from rich.live import Live
from time import time
from datetime import datetime
from pathlib import Path
import json
import traceback
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich import box
from time import sleep
from ..ui.ai_components import AIThinkingSpinner, create_ai_response_box, AIEmotiveResponse, AICodeBlock, AIConversationTracker, create_ai_error_box, create_ai_success_box, create_ai_markdown_box, AIStatusIndicator, AIModelInfo, AICommandPalette, create_ai_tooltip, create_ai_timer_box

console = Console()
client = OpenAI()

def check_ollama_available() -> bool:
    """Check if Ollama is running and available"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_outputs_dir() -> Path:
    """Get the novatool outputs directory"""
    # Using the same path structure as seen in the file list output
    base_path = Path("/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/outputs")
    base_path.mkdir(exist_ok=True)
    return base_path

def save_to_history(prompt: str, response: str, model: str, elapsed: float):
    """Save interaction to history file"""
    try:
        # Use the novatool outputs directory
        outputs_dir = get_outputs_dir()
        history_file = outputs_dir / "ai_history.json"

        # Create entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "model": model,
            "time": f"{elapsed:.2f}s",
            "words": len(response.split()),
            "chars": len(response)
        }

        # Load existing history
        history = []
        if history_file.exists():
            with open(history_file) as f:
                history = json.load(f)

        # Add new entry and save
        history.append(entry)
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

        console.print(f"[dim]History saved to {history_file}[/]")

    except Exception as e:
        console.print(f"[yellow]Warning: Could not save to history: {str(e)}[/]")

def handle_ai(
    prompt: str = typer.Argument(..., help="Your question or prompt"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help=f"AI service to use ({AIService.OLLAMA.value}/{AIService.OPENAI.value})"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    system: str = typer.Option("You are a helpful assistant.", "--system", "-s", help="System prompt"),
    save: bool = typer.Option(False, "--save", "-s", help="Save response to file"),
    no_history: bool = typer.Option(False, "--no-history", help="Don't save to history")
):
    """Ask a question using configured AI service"""
    try:
        total_start_time = time()  # Start total timing
        load_dotenv()

        # Fun intro animation
        with Progress(
            SpinnerColumn("dots"),
            TextColumn("[bold blue]Initializing AI...[/]"),
            TimeElapsedColumn(),  # Add elapsed time here too
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("", total=None)
            sleep(0.5)  # Brief pause for effect

            # Determine provider and update progress
            if provider:
                provider_str = str(provider).lower()
                use_provider = AIService(provider_str)
            else:
                use_provider = (
                    AIService.OLLAMA if check_ollama_available()
                    else AIService.OPENAI
                )
                if use_provider == AIService.OPENAI:
                    progress.update(task, description="[yellow]Ollama not available, falling back to OpenAI[/]")
                    sleep(0.5)

        # Display prompt panel with emoji based on content
        emoji = "🤖"  # default
        if "joke" in prompt.lower():
            emoji = "😄"
        elif "why" in prompt.lower():
            emoji = "🤔"
        elif "how" in prompt.lower():
            emoji = "🛠️"

        console.print(Panel.fit(
            f"{emoji} Asking {use_provider.value} using {model or 'default model'}...",
            style="bold blue",
            box=box.ROUNDED
        ))

        # Get and display the response
        response, response_time = None, 0  # Track response time separately
        if use_provider == AIService.OLLAMA:
            response, response_time = ask_ollama(prompt=prompt, model=model, system=system)
        else:
            response, response_time = ask_openai(prompt=prompt, model=model, system=system)

        if not response:
            console.print("[yellow]Warning: No response received from AI[/]")
            return

        # Calculate total time
        total_elapsed = time() - total_start_time

        # Show total time if initialization took significant time
        if total_elapsed > response_time + 1:  # If initialization took more than 1 second
            console.print(f"[dim]Total time including initialization: {total_elapsed:.2f}s[/]")

        return response

    except Exception as e:
        error_traceback = traceback.format_exc()
        console.print(f"❌ [bold red]Error in handle_ai:[/]")
        console.print(f"[red]{error_traceback}[/]")
        raise typer.Exit(1)

def ask_ollama(prompt: str, model: str = None, system: str = None) -> tuple[str, float]:
    """Query Ollama API with standardized format"""
    try:
        if model is None:
            model = AIConfig.get_model(AIService.OLLAMA)

        context = get_directory_context()

        # Enhanced conciseness directives
        system_base = system or create_system_prompt(context)
        system = f"""
{system_base}

STRICT RESPONSE RULES:
1. Maximum response length: 50 words
2. Use bullet points for lists
3. No pleasantries or unnecessary words
4. Focus on core information only
5. Skip examples unless specifically requested
"""

        stream = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Provide a concise response (max 50 words) to: {prompt}"}
            ],
            stream=True,
            options={
                "temperature": 0.3,     # Even lower temperature for more focused responses
                "top_k": 30,            # More restrictive token selection
                "top_p": 0.7,           # More focused sampling
                "num_predict": 50,      # Strict token limit
                "stop": ["\n\n", ".\n"] # Stop on paragraph breaks
            }
        )

        response, response_time = format_streamed_response(stream)
        return response, response_time

    except Exception as e:
        error_traceback = traceback.format_exc()
        console.print(f"❌ [bold red]Error in ask_ollama:[/]")
        console.print(f"[red]{error_traceback}[/]")
        raise typer.Exit(1)

def get_openai_key() -> str:
    """Get OpenAI API key from environment"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        console.print("❌ [bold red]Error:[/] OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        raise typer.Exit(1)
    return api_key

def ask_openai(prompt: str, model: str = None, system: str = None) -> str:
    """Query OpenAI API with standardized format"""
    api_key = get_openai_key()
    if not api_key:
        console.print("❌ [bold red]Error:[/] OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        raise typer.Exit(1)

    try:
        if model is None:
            model = AIConfig.get_model(AIService.OPENAI)

        client = OpenAI(api_key=api_key)
        context = get_directory_context()
        system = system or create_system_prompt(context)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )

        return format_streamed_response(response)

    except Exception as e:
        error_traceback = traceback.format_exc()
        console.print(f"❌ [bold red]Error in ask_openai:[/]")
        console.print(f"[red]{error_traceback}[/]")
        raise typer.Exit(1)

def format_ai_response(
    result: str,
    elapsed_time: float,
    style: str = "panel"  # or "markdown", "simple"
) -> None:
    """Format AI response with timing and style options"""
    console.print("\n")
    if style == "panel":
        console.print(Panel(
            Markdown(result),
            title=f"AI Response (took {elapsed_time:.1f}s)",
            border_style="blue",
            padding=(1, 2),
            expand=False
        ))
    elif style == "markdown":
        console.print(Markdown(result))
        console.print(f"\n[italic]Response took {elapsed_time:.1f}s[/]")
    else:
        console.print(result)
        console.print(f"\nResponse took {elapsed_time:.1f}s")

def get_directory_context(path: str = ".") -> dict:
    """Get detailed information about the current directory context"""
    context = {
        "current_dir": os.path.abspath(path),
        "files": [],
        "git_info": get_git_info()
    }

    try:
        # List files and directories
        for item in os.listdir(path):
            if item.startswith('.'):  # Skip hidden files
                continue
            full_path = os.path.join(path, item)
            if os.path.isfile(full_path):
                context["files"].append({
                    "name": item,
                    "type": "file",
                    "size": os.path.getsize(full_path)
                })
            else:
                context["files"].append({
                    "name": item,
                    "type": "directory"
                })
    except Exception as e:
        console.print(f"[yellow]Warning: Could not read directory contents: {str(e)}[/]")

    return context

def get_git_info() -> Dict[str, str]:
    """Get git repository information if available"""
    git_info = {
        "branch": None,
        "status": None,
        "remote": None
    }

    try:
        # Check if git repo
        subprocess.run(["git", "rev-parse", "--git-dir"],
                      capture_output=True, check=True)

        # Get current branch
        result = subprocess.run(["git", "branch", "--show-current"],
                              capture_output=True, text=True)
        git_info["branch"] = result.stdout.strip()

        # Get status
        result = subprocess.run(["git", "status", "--porcelain"],
                              capture_output=True, text=True)
        git_info["status"] = "clean" if not result.stdout else "dirty"

        # Get remote
        result = subprocess.run(["git", "remote", "get-url", "origin"],
                              capture_output=True, text=True)
        git_info["remote"] = result.stdout.strip()

    except subprocess.CalledProcessError:
        pass  # Not a git repo or git not available

    return git_info

def create_system_prompt(context: dict) -> str:
    """Create a system prompt with context"""
    return f"""You are a helpful but concise AI assistant. You aim to provide clear, direct answers in as few words as possible.

Current context:
- Directory: {context['current_dir']}
- Files: {len(context['files'])} items
- Git: {context['git_info']['branch'] or 'Not a git repo'} ({context['git_info']['status'] or 'N/A'})

Guidelines:
- Keep responses under 100 words
- Use bullet points when listing
- Focus on essential information
- Avoid unnecessary explanations"""

def format_streamed_response(stream) -> tuple[str, float]:
    """Format and display streaming response with animations"""
    collected_response = []
    start_time = time()

    # Create our AI thinking spinner
    ai_spinner = AIThinkingSpinner(console=console)

    def process_stream(update_thoughts):
        waiting_for_response = True
        first_content = True

        with Live(
            create_ai_response_box("Initializing..."),
            console=console,
            refresh_per_second=10
        ) as live:
            for chunk in stream:
                if waiting_for_response:
                    update_thoughts()  # Make the AI look thoughtful
                    content = get_content_from_chunk(chunk)
                    if content:
                        waiting_for_response = False
                        collected_response.append(content)
                    continue

                # ... rest of streaming logic ...
                live.update(create_ai_response_box("".join(collected_response)))

    # Let the AI think about it
    final_response = ai_spinner.think(process_stream)
    elapsed = time() - start_time

    # Show final response with stats
    stats = f"[dim]{len(final_response.split())} words, {len(final_response)} chars ({elapsed:.2f}s)[/]"
    console.print(create_ai_response_box(final_response, stats=stats))

    return final_response, elapsed

def view_history(
    limit: int = typer.Option(5, "--limit", "-l", help="Number of entries to show"),
    full: bool = typer.Option(False, "--full", "-f", help="Show full responses")
):
    """View AI interaction history"""
    try:
        history_file = get_outputs_dir() / "ai_history.json"
        if not history_file.exists():
            console.print("[yellow]No history found.[/]")
            return

        with open(history_file) as f:
            history = json.load(f)

        # Show most recent entries first
        history = list(reversed(history[-limit:]))

        for entry in history:
            console.print("\n[bold blue]" + "─" * 50 + "[/]")
            console.print(f"[bold]Time:[/] {entry['timestamp']}")
            console.print(f"[bold]Model:[/] {entry['model']}")
            console.print(f"[bold]Prompt:[/] {entry['prompt']}")
            if full:
                console.print(f"\n[bold]Response:[/]\n{entry['response']}")
            else:
                # Show truncated response
                response = entry['response'][:100] + "..." if len(entry['response']) > 100 else entry['response']
                console.print(f"[bold]Response:[/] {response}")
            console.print(f"[dim]Stats: {entry['words']} words, {entry['chars']} chars, {entry['time']}[/]")

    except Exception as e:
        console.print(f"❌ Error: {str(e)}")
        sys.exit(1)

# Show an emotive response
console.print(AIEmotiveResponse.format("I found the answer!", "excited"))

# Display code
console.print(AICodeBlock.format(
    code="print('Hello, World!')",
    language="python",
    filename="example.py"
))

# Track conversation
tracker = AIConversationTracker()
tracker.add_message("user", "What is Python?")
tracker.add_message("assistant", "Python is a programming language...")
console.print(tracker.display_context())

# Show errors nicely
console.print(create_ai_error_box(
    "API rate limit exceeded",
    "Try again in 60 seconds"
))

# Show success
console.print(create_ai_success_box(
    "Response generated successfully",
    {"Time": "2.3s", "Tokens": 150}
))

# Show AI status
console.print(AIStatusIndicator.show("thinking"))

# Display model info
console.print(AIModelInfo.display(
    model="gpt-4",
    provider="OpenAI",
    stats={"Temperature": 0.7}
))

# Show available commands
console.print(AICommandPalette.show_commands({
    "ask": "Ask AI a question",
    "clear": "Clear conversation",
    "help": "Show help"
}))

# Show a helpful tip
console.print(create_ai_tooltip(
    "Your question was very broad",
    "Try being more specific"
))

# Show operation timing
console.print(create_ai_timer_box(
    "Model Inference",
    2.34,
    {"Tokens": 150}
))