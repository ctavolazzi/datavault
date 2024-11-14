from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
import time
import os
import signal
import psutil

def send_status(status):
    """Send status to demo script"""
    status_file = os.path.join(os.path.dirname(__file__), 'hud_status.txt')
    with open(status_file, 'w') as f:
        f.write(status)

class TelephoneGameMonitor(FileSystemEventHandler):
    def __init__(self, log_path: str):
        self.console = Console()
        self.log_path = log_path
        print(f"[DEBUG] Absolute log path: {os.path.abspath(log_path)}")

        self.config_path = os.path.join(os.path.dirname(__file__), 'hud_config.json')
        self.layout = Layout()
        self.running = True
        self.messages = []

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

        # Load config and setup
        self.load_config()
        self.setup_layout()

        # Create live display
        self.live = Live(
            self.layout,
            console=self.console,
            refresh_per_second=4,
            screen=True,
            auto_refresh=False
        )

        # Setup file observer
        self.observer = Observer()
        self.observer.schedule(self, path=os.path.dirname(log_path), recursive=False)
        self.observer.start()

        send_status("initializing")

    def on_modified(self, event):
        """Handle log file modifications"""
        if event.src_path == self.log_path:
            try:
                with open(self.log_path, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        # Process the latest message
                        latest = json.loads(lines[-1].strip())
                        self.handle_message(latest)
            except Exception as e:
                print(f"Error reading log: {e}")

    def handle_message(self, data):
        """Process incoming messages"""
        event_type = data.get("event")

        if event_type == "startup":
            self.update_status("Starting game...", "yellow")
            self.add_message("Game is starting!")

        elif event_type == "query":
            self.update_status("Processing query...", "yellow")
            self.add_message(f"Query: {data['message']}")

        elif event_type == "response":
            self.update_status("AI Ready", "green")
            self.add_message(f"Round {data['round']}: {data['message']}")

        self.update_display()

    def update_status(self, message, style="white"):
        """Update the status panel"""
        status_text = Text()
        status_text.append("Game Status", style="bright_blue")
        if message != "AI Ready":
            status_text.append("\n" + message, style=style)
            if style == "green":
                status_text.append("\n\n● AI Ready", style="green")
        else:
            status_text.append("\n\n● AI Ready", style="green")

        self.layout["status"].update(Panel(
            status_text,
            border_style="blue",
            padding=(0, 1)
        ))

    def add_message(self, message):
        """Add a message to the history"""
        self.messages.append(message)
        if len(self.messages) > 10:  # Keep last 10 messages
            self.messages.pop(0)

        message_text = Text()
        message_text.append("Message History", style="bright_blue")
        for msg in self.messages:
            wrapped_msg = "\n".join(
                msg[i:i+70] for i in range(0, len(msg), 70)
            )
            message_text.append(f"\n{wrapped_msg}", style="white")

        self.layout["messages"].update(Panel(
            message_text,
            border_style="blue",
            padding=(0, 1)
        ))

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        self.running = False
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()
        if self.live:
            self.live.stop()
        print("\nShutdown complete")
        exit(0)

    def load_config(self):
        """Load HUD configuration from JSON"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
                print(f"[DEBUG] Successfully loaded config from {self.config_path}")
        except Exception as e:
            print(f"[ERROR] Error loading config: {e}")
            self.config = {}

    def setup_layout(self):
        """Setup the layout structure"""
        # Main layout
        self.layout.split(
            Layout(name="title", size=1),
            Layout(name="body"),
            Layout(name="footer", size=2)
        )

        # Split body into two columns
        self.layout["body"].split_row(
            Layout(name="status", ratio=1),
            Layout(name="messages", ratio=2)
        )

        # Title
        self.layout["title"].update(
            Text("🎮 AI Telephone Game Monitor", style="white")
        )

        # Game Status
        status_text = Text()
        status_text.append("Game Status", style="bright_blue")
        status_text.append("\nWaiting for messages...", style="dim")
        status_text.append("\n\n")  # Extra space
        status_text.append("● ", style="green")
        status_text.append("AI Ready", style="green")

        self.layout["status"].update(Panel(
            status_text,
            border_style="blue",
            padding=(0, 1)
        ))

        # Message History
        message_text = Text()
        message_text.append("Message History", style="bright_blue")
        message_text.append("\nWaiting for messages...", style="white")

        self.layout["messages"].update(Panel(
            message_text,
            border_style="blue",
            padding=(0, 1)
        ))

        # Footer
        health_text = Text()
        health_text.append("System Health: ", style="bright_blue")
        health_text.append("█" * 20, style="green")

        self.layout["footer"].update(Panel(
            health_text,
            border_style="blue",
            padding=(0, 1)
        ))

    def get_system_health(self):
        """Get current system health metrics"""
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        return min(100, (cpu + memory) / 2)  # Average of CPU and memory, max 100%

    def update_display(self):
        """Update the display with current system health"""
        health = self.get_system_health()
        bar_length = int((health / 100) * 40)  # 40 characters total width
        health_text = Text()
        health_text.append("System Health: ", style="bright_blue")
        health_text.append("█" * bar_length, style="green")

        self.layout["footer"].update(health_text)
        if self.live:
            self.live.refresh()

    def run(self):
        """Start the HUD display"""
        try:
            send_status("ready")
            with self.live:
                self.live.start()
                while self.running:
                    self.update_display()
                    time.sleep(0.25)
        except Exception as e:
            print(f"\nError: {e}")
            send_status("error")
        finally:
            if self.live:
                self.live.stop()
            send_status("closed")

def main():
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'hud_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)

        watch_path = config['watch_file']
        print(f"[DEBUG] Monitoring file at: {watch_path}")

        monitor = TelephoneGameMonitor(watch_path)
        monitor.run()
    except Exception as e:
        print(f"Error starting HUD: {e}")

if __name__ == "__main__":
    main()
