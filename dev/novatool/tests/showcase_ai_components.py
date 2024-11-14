from rich.console import Console
import sys
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from time import sleep

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from novatool.utils.ai_config import AIConfig, AIService
from novatool.ui.ai_components import (
    AIThinkingSpinner,
    AIEmotiveResponse,
    AIStatusIndicator,
    AIModelInfo,
    AICommandPalette,
    AICodeBlock,
    AIConversationTracker,
    create_ai_tooltip,
    create_ai_timer_box,
    create_ai_error_box,
    create_ai_success_box,
    create_ai_markdown_box
)

def showcase_components():
    console = Console()

    # Get model info from existing config
    current_model = AIConfig.get_model(AIService.OLLAMA)
    current_provider = AIService.OLLAMA.value

    console.print("\n[bold blue]🎨 AI Components Showcase[/]\n")

    # 1. Progress Demo
    console.print("[bold]1. AI Progress Demo:[/]")
    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green", finished_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False
    ) as progress:
        task1 = progress.add_task("[blue]🧠 Loading AI model...", total=100)
        task2 = progress.add_task("[yellow]⚡ Warming up neurons...", total=100)
        task3 = progress.add_task("[green]✨ Calibrating responses...", total=100)

        # Task 1: Loading model (0-100% over 1.5 seconds)
        for i in range(100):
            progress.update(task1, advance=1)
            sleep(0.015)  # 1.5 seconds total

        # Task 2: Warming up (0-100% over 1.25 seconds)
        for i in range(100):
            progress.update(task2, advance=1)
            sleep(0.0125)  # 1.25 seconds total

        # Task 3: Calibrating (0-100% over 1.25 seconds)
        for i in range(100):
            progress.update(task3, advance=1)
            sleep(0.0125)  # 1.25 seconds total

        # Total time: 4 seconds

    # 2. Status Transitions
    console.print("\n[bold]2. AI Status Transitions:[/]")
    for state in ["ready", "thinking", "busy", "error", "sleeping", "updating"]:
        console.print(AIStatusIndicator.show(state))
        sleep(0.5)  # Pause to see each state

    # 3. Emotive Responses
    console.print("\n[bold]3. AI Emotional Responses:[/]")
    for emotion in ["happy", "thinking", "excited", "warning"]:
        console.print(AIEmotiveResponse.format(
            f"This is how I look when I'm {emotion}!",
            emotion
        ))

    # 4. Code Display
    console.print("\n[bold]4. AI Code Output:[/]")
    console.print(AICodeBlock.format(
        code="def hello_ai():\n    print('Hello, Human!')\n    return '👋'",
        language="python",
        filename="greetings.py"
    ))

    # 5. Conversation Tracking
    console.print("\n[bold]5. AI Conversation History:[/]")
    tracker = AIConversationTracker()
    tracker.add_message("user", "What's the meaning of life?")
    tracker.add_message("assistant", "42, of course! 🌟")
    tracker.add_message("user", "Why 42?")
    tracker.add_message("assistant", "It's the answer to everything! 🤔")
    console.print(tracker.display_context())

    # 6. Model Information
    console.print("\n[bold]6. AI Model Details:[/]")
    console.print(AIModelInfo.display(
        model=current_model,
        provider=current_provider,
        stats={
            "Temperature": 0.7,
            "Context Window": 8192,
            "Local Model": "Yes"
        }
    ))

    # 7. Command Palette
    console.print("\n[bold]7. Available AI Commands:[/]")
    console.print(AICommandPalette.show_commands({
        "ask": "Ask AI a question",
        "clear": "Clear conversation",
        "help": "Show help",
        "save": "Save response to file",
        "history": "View chat history"
    }))

    # 8. Tooltips
    console.print("\n[bold]8. AI Helper Tips:[/]")
    console.print(create_ai_tooltip(
        "Your question was very broad",
        "Try asking about specific aspects one at a time"
    ))

    # 9. Error Handling
    console.print("\n[bold]9. AI Error Display:[/]")
    console.print(create_ai_error_box(
        "API rate limit exceeded",
        "Please wait 60 seconds before trying again"
    ))

    # 10. Success Messages
    console.print("\n[bold]10. AI Success Messages:[/]")
    console.print(create_ai_success_box(
        "Response generated successfully",
        {
            "Time": "2.3s",
            "Tokens": 150,
            "Model": current_model
        }
    ))

    # 11. Markdown Formatting
    console.print("\n[bold]11. AI Markdown Response:[/]")
    console.print(create_ai_markdown_box("""
# AI Response
- Point 1: This is formatted
- Point 2: With markdown
## Details
This supports **bold** and *italic* text!
    """))

    # 12. Operation Timer
    console.print("\n[bold]12. AI Operation Timing:[/]")
    console.print(create_ai_timer_box(
        "Model Inference",
        2.34,
        {
            "Tokens Generated": 150,
            "Cache Status": "Hit",
            "Model": current_model
        }
    ))

    console.print("\n[bold green]✨ Showcase Complete![/]\n")

if __name__ == "__main__":
    showcase_components()