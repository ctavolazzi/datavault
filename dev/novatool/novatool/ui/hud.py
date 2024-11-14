from rich.layout import Layout
from rich.live import Live
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import time
import psutil
import os
from typing import Tuple

class AIHUD:
    def __init__(self, console: Console):
        self.start_time = time.monotonic()
        self.console = console
        self.layout = Layout()

        # Initialize state with all possible metrics
        self.current_query = None
        self.messages = []
        self.stats = {
            "messages": [],
            "tokens": 0,
            "context_length": 0,
            "cpu": 0.0,
            "memory": 0.0,
            "api": 0.0,
            "total_queries": 0,
            "processed": 0,
            "queue_size": 0,
            "is_processing": False
        }

        # Setup layout
        self.setup_layout()
        self.last_update = time.monotonic()
        self.live = Live(
            self.generate_layout(),
            console=console,
            refresh_per_second=4,
            auto_refresh=False,
            screen=False
        )

    def setup_layout(self):
        """Setup the fixed layout sections"""
        # Main container with fixed heights
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=7)  # Fixed size for memory stats
        )

        # Split body into columns
        self.layout["body"].split_row(
            Layout(name="left_panel", ratio=1),
            Layout(name="right_panel", ratio=2)
        )

        # Split left panel into sections
        self.layout["left_panel"].split(
            Layout(name="metrics", ratio=2),
            Layout(name="health", ratio=1)
        )

    def generate_layout(self) -> Layout:
        """Generate the complete layout"""
        # Calculate elapsed time
        elapsed = int(time.monotonic() - self.start_time)
        elapsed_str = f"{elapsed}s"

        # Create header with proper timer
        header = f"AI System Monitor | Session: [bright_blue]{elapsed_str}[/] | Status: [green]● Ready[/]"
        self.layout["header"].update(Panel(
            header,
            border_style="bright_blue",
            box=box.ROUNDED
        ))

        # System Metrics Table
        metrics_table = Table(show_header=True, box=box.SIMPLE, expand=True)
        metrics_table.add_column("Metric", style="cyan", width=12)
        metrics_table.add_column("Value", justify="right", width=10)
        metrics_table.add_column("Load", justify="left", width=10)

        # Add CPU metrics with proper formatting
        cpu_val = float(self.stats.get('cpu', 0.0))
        cpu_bars = "█" * int(cpu_val/10) + "░" * (10-int(cpu_val/10))
        metrics_table.add_row(
            "CPU",
            f"{cpu_val:.1f}%",
            f"[{'green' if cpu_val < 50 else 'yellow' if cpu_val < 80 else 'red'}]{cpu_bars}[/]"
        )

        # Add Memory metrics
        mem_val = float(self.stats.get('memory', 0.0))
        mem_bars = "█" * int(mem_val/10) + "░" * (10-int(mem_val/10))
        metrics_table.add_row(
            "Memory",
            f"{mem_val:.1f}%",
            f"[{'green' if mem_val < 50 else 'yellow' if mem_val < 80 else 'red'}]{mem_bars}[/]"
        )

        # Add API metrics
        api_val = float(self.stats.get('api', 0.0))
        api_bars = "█" * int(api_val/10) + "░" * (10-int(api_val/10))
        metrics_table.add_row(
            "API",
            f"{api_val:.1f}%",
            f"[{'green' if api_val > 90 else 'yellow' if api_val > 70 else 'red'}]{api_bars}[/]"
        )

        self.layout["metrics"].update(Panel(
            metrics_table,
            title="🖥️ System Metrics",
            border_style="bright_blue"
        ))

        # Health Monitor with queue status
        health_table = Table.grid(expand=True)
        health_table.add_column("Status", style="cyan")
        health_table.add_row(
            f"System: [green]Online[/]"
        )
        health_table.add_row(
            f"Queue:  [{'yellow' if self.stats.get('queue_size', 0) > 0 else 'green'}]"
            f"{self.stats.get('queue_size', 0)} items[/]"
        )
        health_table.add_row(
            f"Load:   [{'yellow' if self.stats.get('is_processing', False) else 'green'}]"
            f"{'Processing' if self.stats.get('is_processing', False) else 'Normal'}[/]"
        )

        # Update panels
        self.layout["health"].update(Panel(
            health_table,
            title="💓 Health Monitor",
            border_style="bright_blue"
        ))

        self.layout["right_panel"].update(Panel(
            "\n".join(self.messages[-10:]) if self.messages else "No activity",
            title="📝 Recent Activity",
            subtitle=f"Showing {len(self.messages[-10:])} of {len(self.messages)} messages",
            border_style="bright_blue"
        ))

        # Memory Stats with minimal formatting
        stats_table = Table(
            show_header=True,
            header_style="bright_blue",
            box=None,  # Remove box characters completely
            expand=True,
            show_edge=False
        )

        # Simple columns
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="bright_blue", justify="right")

        # Add rows without any special characters
        stats_table.add_row("Messages", str(len(self.messages)))
        stats_table.add_row("Tokens", str(self.stats.get('tokens', 0)))
        stats_table.add_row("Queue Size", str(self.stats.get('queue_size', 0)))
        stats_table.add_row("Processed", str(self.stats.get('processed', 0)))

        # Simple panel without box characters
        self.layout["footer"].update(Panel(
            stats_table,
            title="Memory Stats",
            border_style="bright_blue",
            box=box.ASCII2,  # Use simplest ASCII characters
            padding=(0, 1)
        ))

        return self.layout

    def update(self, stats=None):
        """Update the HUD with new stats"""
        if stats:
            # Ensure all values are properly typed
            try:
                self.stats.update({
                    "cpu": float(stats.get('cpu', 0.0)),
                    "memory": float(stats.get('memory', 0.0)),
                    "api": float(stats.get('api', 0.0)),
                    "messages": int(stats.get('messages', 0)),
                    "tokens": int(stats.get('tokens', 0)),
                    "context_length": int(stats.get('context_length', 0)),
                    "total_queries": int(stats.get('total_queries', 0)),
                    "processed": int(stats.get('processed', 0)),
                    "queue_size": int(stats.get('queue_size', 0)),
                    "is_processing": bool(stats.get('is_processing', False))
                })
            except (ValueError, TypeError) as e:
                self.console.print(f"[red]Error updating stats: {str(e)}[/]")

        if self.live:
            self.live.update(self.generate_layout())

    def add_message(self, message: str):
        """Add a timestamped message to the log"""
        timestamp = time.strftime("%H:%M:%S")
        self.messages.append(f"[dim]{timestamp}[/] {message}")
        if len(self.messages) > 100:
            self.messages.pop(0)
        self.update()

    def start(self, total_queries: int = 0):
        """Start the HUD with optional total queries"""
        self.total_queries = total_queries  # Add this attribute
        self.start_time = time.monotonic()
        self.live.start()

    def stop(self):
        """Stop the HUD and print final state"""
        if self.live:
            # Print final state before stopping
            self.console.print(self.generate_layout())
            self.live.stop()