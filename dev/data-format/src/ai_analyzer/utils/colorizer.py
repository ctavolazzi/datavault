import click
from typing import Any, Dict
from datetime import datetime
import json

class LogColorizer:
    """Colorize log output for terminal display"""

    LEVEL_COLORS = {
        'DEBUG': 'blue',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red bold'
    }

    @staticmethod
    def colorize_json(json_obj: Dict[str, Any], indent: int = 2) -> str:
        """Colorize a JSON object for terminal output"""

        def format_value(key: str, value: Any) -> str:
            if isinstance(value, dict):
                return click.style("{\n" +
                    "\n".join(f"{' ' * (indent + 2)}{k}: {format_value(k, v)}"
                             for k, v in value.items()) +
                    f"\n{' ' * indent}}}", fg='white')
            elif isinstance(value, (int, float)):
                return click.style(str(value), fg='cyan')
            elif isinstance(value, bool):
                return click.style(str(value), fg='magenta')
            elif key == 'level':
                return click.style(f'"{value}"', fg=LogColorizer.LEVEL_COLORS.get(value, 'white'))
            elif key == 'timestamp':
                return click.style(f'"{value}"', fg='yellow')
            else:
                return click.style(f'"{value}"', fg='white')

        return "{\n" + "\n".join(
            f"{' ' * indent}{click.style(k, fg='bright_blue')}: {format_value(k, v)}"
            for k, v in json_obj.items()
        ) + "\n}"

    @staticmethod
    def format_log_entry(entry: Dict[str, Any]) -> str:
        """Format a single log entry with colors"""
        timestamp = click.style(entry['timestamp'], fg='yellow')
        level = click.style(f"[{entry['level']}]".ljust(8),
                          fg=LogColorizer.LEVEL_COLORS.get(entry['level'], 'white'))
        message = click.style(entry['message'], fg='white')

        # Format context if present
        context = entry.get('context', {})
        context_str = click.style(
            f"({context.get('module', '')}.{context.get('function', '')})",
            fg='bright_black'
        )

        # Format metrics if present
        metrics_str = ""
        if 'metrics' in entry:
            metrics = entry['metrics']
            if 'execution' in metrics:
                duration = metrics['execution'].get('duration_seconds', 'N/A')
                metrics_str = click.style(
                    f" [⏱️ {duration}s]",
                    fg='bright_magenta'
                )

        return f"{timestamp} {level} {message} {context_str}{metrics_str}"