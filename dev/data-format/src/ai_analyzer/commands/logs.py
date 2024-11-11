import click
from pathlib import Path
from datetime import datetime
import re

class LogEntry:
    def __init__(self, line: str):
        self.original = line.strip()
        self.parse()

    def parse(self):
        # Updated regex pattern to match our log format
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\s*\] (.+)'
        match = re.match(pattern, self.original)

        if match:
            self.timestamp = match.group(1)
            self.level = match.group(2).strip()
            self.message = match.group(3)
            self.valid = True
        else:
            # Try alternate format
            alt_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - \w+ - (\w+) - (.+)'
            alt_match = re.match(alt_pattern, self.original)
            if alt_match:
                self.timestamp = alt_match.group(1)[:19]  # Remove milliseconds
                self.level = alt_match.group(2)
                self.message = alt_match.group(3)
                self.valid = True
            else:
                self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.level = "UNKNOWN"
                self.message = self.original
                self.valid = False

    def colorize(self) -> str:
        """Return a colorized version of the log entry"""
        level_colors = {
            'DEBUG': 'bright_black',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red'
        }

        # Format timestamp and level with fixed width
        timestamp = f"{self.timestamp:<19}"
        level_str = f"[{self.level:^7}]"

        return (
            click.style(timestamp, fg='blue') + " " +
            click.style(level_str, fg=level_colors.get(self.level, 'white')) + " " +
            click.style(self.message, fg='white')
        )

@click.command()
@click.option('--tail', '-n', default=10, help='Number of lines to show')
@click.option('--level', '-l',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
              help='Filter by log level')
@click.option('--search', '-s', help='Search for specific text in logs')
@click.option('--invalid', is_flag=True, help='Show invalid log entries')
def logs_command(tail: int, level: str, search: str, invalid: bool):
    """View logs with style 📊"""
    click.echo(click.style("\n📋 Datavault Logs", fg='bright_blue', bold=True))

    log_file = Path.home() / ".datavault" / "logs" / "datavault.log"

    if not log_file.exists():
        click.echo(click.style("\n❌ No logs found!", fg='red'))
        return

    try:
        # Read and parse all lines
        with open(log_file, 'r', encoding='utf-8') as f:
            log_entries = [LogEntry(line) for line in f if line.strip()]

        if not log_entries:
            click.echo(click.style("\n📭 Log file is empty", fg='yellow'))
            return

        # Filter invalid entries unless specifically requested
        if not invalid:
            log_entries = [entry for entry in log_entries if entry.valid]

        # Apply filters
        if level:
            log_entries = [entry for entry in log_entries if entry.level == level]

        if search:
            log_entries = [entry for entry in log_entries
                         if search.lower() in entry.message.lower()]

        # Get the last N entries
        log_entries = log_entries[-tail:]

        # Display summary
        click.echo(click.style("\n📊 Log Summary:", fg='bright_blue'))
        click.echo(f"  • Total entries shown: {click.style(str(len(log_entries)), fg='green')}")
        if level:
            click.echo(f"  • Filtered by level: {click.style(level, fg='yellow')}")
        if search:
            click.echo(f"  • Search term: {click.style(search, fg='cyan')}")

        # Display logs
        if log_entries:
            click.echo(click.style("\n📝 Log Entries:", fg='bright_blue'))
            click.echo("─" * 100)

            # Header
            click.echo(
                click.style("Timestamp".ljust(20), fg='blue') +
                click.style("Level".center(9), fg='green') +
                click.style("Message", fg='white')
            )
            click.echo("─" * 100)

            # Log entries
            for entry in log_entries:
                click.echo(entry.colorize())

            click.echo("─" * 100)
        else:
            click.echo(click.style("\n🔍 No matching log entries found", fg='yellow'))

        click.echo()  # Add final newline

    except Exception as e:
        click.echo(click.style(f"\n❌ Error reading logs: {str(e)}", fg='red'))
        raise  # Re-raise for debugging