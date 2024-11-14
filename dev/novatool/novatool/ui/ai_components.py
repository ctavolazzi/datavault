from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.console import Console
from rich import box
from rich.markdown import Markdown
from rich.table import Table
from rich.style import Style
from rich.text import Text
from time import sleep
from typing import List, Optional, Callable, Dict

class AIThinkingSpinner:
    """A playful spinner animation for when AI is thinking"""

    DEFAULT_THOUGHTS = [
        "🤔 Thinking",
        "🧠 Processing",
        "💭 Contemplating",
        "🔄 Computing",
        "✨ Creating response"
    ]

    def __init__(
        self,
        thoughts: Optional[List[str]] = None,
        console: Optional[Console] = None,
        refresh_rate: float = 0.3
    ):
        self.thoughts = thoughts or self.DEFAULT_THOUGHTS
        self.console = console or Console()
        self.refresh_rate = refresh_rate
        self.current_index = 0

    def think(self, operation: Callable):
        """Execute an operation while the AI appears to be thinking"""
        with Progress(
            SpinnerColumn("dots"),
            TextColumn("[bold blue]{task.description}"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task(self.thoughts[0], total=None)

            def update_thoughts():
                self.current_index = (self.current_index + 1) % len(self.thoughts)
                progress.update(task, description=self.thoughts[self.current_index])
                sleep(self.refresh_rate)

            return operation(update_thoughts)

class AIEmotiveResponse:
    """Adds emotion-aware formatting to AI responses"""

    EMOTIONS = {
        "happy": "💫",
        "thinking": "🤔",
        "excited": "✨",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅"
    }

    @staticmethod
    def format(content: str, emotion: str = "thinking") -> Panel:
        emoji = AIEmotiveResponse.EMOTIONS.get(emotion, "🤖")
        return Panel(
            content,
            title=f"{emoji} AI Response",
            border_style="blue",
            box=box.ROUNDED
        )

class AIProgressBar:
    """Shows AI task progress with personality"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def process(self, total: int, description: str = "AI Processing"):
        with Progress(
            SpinnerColumn("dots"),
            TextColumn("[bold blue]{task.description}"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task(description, total=total)
            return task

class AICodeBlock:
    """Pretty formats code snippets from AI"""

    @staticmethod
    def format(
        code: str,
        language: str,
        filename: Optional[str] = None,
        line_numbers: bool = True
    ) -> Panel:
        title = f"📝 {filename}" if filename else f"💻 {language} code"
        return Panel(
            Markdown(f"```{language}\n{code}\n```"),
            title=title,
            border_style="blue",
            box=box.ROUNDED
        )

class AIConversationTracker:
    """Tracks and displays AI conversation context"""

    def __init__(self):
        self.messages = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def display_context(self) -> Panel:
        table = Table(box=box.ROUNDED)
        table.add_column("Role", style="bold blue")
        table.add_column("Content")

        for msg in self.messages[-5:]:  # Show last 5 messages
            table.add_row(msg["role"], Text(msg["content"], no_wrap=True))

        return Panel(
            table,
            title="🧠 AI Context",
            border_style="blue",
            box=box.ROUNDED
        )

def create_ai_error_box(error: str, context: Optional[str] = None) -> Panel:
    """Format AI errors consistently"""
    content = f"[bold red]Error:[/] {error}"
    if context:
        content += f"\n[dim]Context: {context}[/]"

    return Panel(
        content,
        title="❌ AI Error",
        border_style="red",
        box=box.ROUNDED
    )

def create_ai_success_box(message: str, stats: Optional[Dict] = None) -> Panel:
    """Format AI success messages"""
    content = f"[bold green]✓[/] {message}"
    if stats:
        stats_text = "\n".join(f"[dim]{k}:[/] {v}" for k, v in stats.items())
        content += f"\n\n{stats_text}"

    return Panel(
        content,
        title="✨ Success",
        border_style="green",
        box=box.ROUNDED
    )

def create_ai_markdown_box(markdown: str) -> Panel:
    """Format AI markdown responses"""
    return Panel(
        Markdown(markdown),
        title="📝 AI Response",
        border_style="blue",
        box=box.ROUNDED
    )

class AITypingEffect:
    """Simulates AI typing responses character by character"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def type(self, text: str, speed: float = 0.05):
        for char in text:
            self.console.print(char, end="", flush=True)
            sleep(speed)
        self.console.print()

class AIStatusIndicator:
    """Shows AI system status with fun indicators"""

    STATES = {
        "ready": ("🟢", "green", "AI Ready"),
        "thinking": ("🟡", "yellow", "AI Thinking"),
        "busy": ("🟠", "yellow", "AI Busy"),
        "error": ("🔴", "red", "AI Error"),
        "sleeping": ("💤", "blue", "AI Resting"),
        "updating": ("⚡", "yellow", "AI Updating")
    }

    @staticmethod
    def show(state: str) -> Panel:
        emoji, color, text = AIStatusIndicator.STATES.get(
            state, ("❓", "white", "Unknown State")
        )
        return Panel(
            f"[{color}]{text}[/]",
            title=f"{emoji} AI Status",
            border_style=color,
            box=box.ROUNDED
        )

class AIModelInfo:
    """Displays AI model information in a pretty format"""

    @staticmethod
    def display(
        model: str,
        provider: str,
        stats: Optional[Dict] = None
    ) -> Panel:
        table = Table(box=None, show_header=False)
        table.add_row("Model", f"[bold blue]{model}[/]")
        table.add_row("Provider", f"[blue]{provider}[/]")

        if stats:
            for key, value in stats.items():
                table.add_row(
                    f"[dim]{key}[/]",
                    f"[blue]{value}[/]"
                )

        return Panel(
            table,
            title="🤖 Model Info",
            border_style="blue",
            box=box.ROUNDED
        )

class AICommandPalette:
    """Shows available AI commands in a pretty format"""

    @staticmethod
    def show_commands(commands: Dict[str, str]) -> Panel:
        table = Table(box=None)
        table.add_column("Command", style="bold blue")
        table.add_column("Description")

        for cmd, desc in commands.items():
            table.add_row(f"/{cmd}", desc)

        return Panel(
            table,
            title="🎮 AI Commands",
            border_style="blue",
            box=box.ROUNDED
        )

def create_ai_tooltip(
    message: str,
    tip: str
) -> Panel:
    """Shows a helpful AI tip"""
    return Panel(
        f"{message}\n[dim]💡 Tip: {tip}[/]",
        title="✨ AI Helper",
        border_style="blue",
        box=box.ROUNDED
    )

def create_ai_timer_box(
    operation_name: str,
    elapsed: float,
    extra_stats: Optional[Dict] = None
) -> Panel:
    """Shows operation timing in a pretty box"""
    content = f"[bold blue]{operation_name}[/]\n"
    content += f"⏱️ Time: [yellow]{elapsed:.2f}s[/]"

    if extra_stats:
        content += "\n\n[dim]Additional Stats:[/]"
        for key, value in extra_stats.items():
            content += f"\n• {key}: {value}"

    return Panel(
        content,
        title="⏱️ AI Timer",
        border_style="blue",
        box=box.ROUNDED
    )

class AITaskProgress:
    """Shows AI task progress with phases"""

    PHASES = [
        ("🧠", "Thinking"),
        ("📝", "Planning"),
        ("⚡", "Processing"),
        ("✨", "Finalizing")
    ]

    @staticmethod
    def show_progress(current_phase: int) -> Panel:
        progress = ""
        for i, (emoji, name) in enumerate(AITaskProgress.PHASES):
            if i < current_phase:
                progress += f"[green]{emoji} {name} ✓[/] → "
            elif i == current_phase:
                progress += f"[yellow]{emoji} {name} ...[/] → "
            else:
                progress += f"[dim]{emoji} {name}[/] → "

        return Panel(
            progress[:-3],  # Remove last arrow
            title="🎯 Task Progress",
            border_style="blue",
            box=box.ROUNDED
        )

class AIMemoryStats:
    """Shows AI conversation memory stats"""

    @staticmethod
    def display_stats(
        messages: int,
        tokens: int,
        context_length: int
    ) -> Panel:
        table = Table(box=None, show_header=False)
        table.add_row("Messages", f"[bold blue]{messages}[/]")
        table.add_row("Tokens Used", f"[yellow]{tokens}[/]")
        table.add_row("Context Length", f"[green]{context_length}[/]")

        return Panel(
            table,
            title="💭 Memory Stats",
            border_style="blue",
            box=box.ROUNDED
        )

class AISystemHealth:
    """Shows AI system health metrics"""

    @staticmethod
    def show_health(metrics: Dict[str, float]) -> Panel:
        """Display system health metrics"""
        health_table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            expand=True
        )

        health_table.add_column("Metric")
        health_table.add_column("Status", justify="right")
        health_table.add_column("Health", justify="left")

        # Add metrics rows with health indicators
        for name, value in metrics.items():
            health_dots = "●" * int(value / 20)
            health_table.add_row(
                name.upper(),
                f"[cyan]{value:.1f}%[/]",
                health_dots
            )

        return Panel(
            health_table,
            title="🏥 System Health",
            border_style="cyan",
            box=box.ROUNDED
        )