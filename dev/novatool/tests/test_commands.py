#!/usr/bin/env python3
import subprocess
import logging
from datetime import datetime
from pathlib import Path
import json
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from dotenv import load_dotenv

# Initialize console with larger width
console = Console(width=70)

# Setup directories and files
TESTS_DIR = Path(__file__).parent
RESULTS_DIR = TESTS_DIR / "test_results"
RESULTS_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = RESULTS_DIR / f"command_tests_{timestamp}.log"
json_file = RESULTS_DIR / f"command_tests_{timestamp}.json"

# Load .env file from the correct location
env_path = Path(__file__).parent.parent.parent / '.env'
print(f"Looking for .env file at: {env_path}")
load_dotenv(env_path)

# Debug: Print available keys (safely)
def debug_env_keys():
    """Safely print which API keys are present"""
    news_api = "✓" if os.getenv("NEWS_API_KEY") else "✗"
    openai_api = "✓" if os.getenv("OPENAI_API_KEY") else "✗"
    console.print("\n[bold]API Keys Status:[/]")
    console.print(f"NEWS_API_KEY: {news_api}")
    console.print(f"OPENAI_API_KEY: {openai_api}")

def print_command_result(result: dict) -> None:
    console.print(f"\n[bold blue]$ nova {result['command']}[/]")
    console.print(f"[{result['status']}]{result['status'].upper()}[/]")

    if result["output"]:
        # Clean up paths and format output
        output = (result["output"]
            .replace("/Users/ctavolazzi/Code/datavault/", "~/")
            .replace("/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/outputs/", "~/novatool/outputs/"))
        console.print(output)

    if result["error"]:
        console.print(f"[red]Error: {result['error']}[/]")

    console.print(f"[dim]Time: {result['duration']:.2f}s[/]")
    console.print("─" * 50)  # Simple separator

def run_command(command: str) -> dict:
    """Run a nova command and return results"""
    start_time = datetime.now()

    result_dict = {
        "command": command,
        "timestamp": datetime.now().isoformat(),
        "status": "unknown",
        "output": "",
        "error": "",
        "duration": 0
    }

    try:
        # Check for API-dependent commands
        if command.startswith(("news", "ai")):
            missing_keys = [k for k in ['NEWS_API_KEY', 'OPENAI_API_KEY'] if not os.getenv(k)]
            if missing_keys:
                result_dict["status"] = "skipped"
                result_dict["output"] = f"Test skipped: Missing required API keys ({', '.join(missing_keys)})"
                result_dict["duration"] = (datetime.now() - start_time).total_seconds()
                print_command_result(result_dict)
                return result_dict

        process = subprocess.run(f"nova {command}",
                               shell=True,
                               capture_output=True,
                               text=True)

        result_dict["output"] = process.stdout.strip()
        result_dict["error"] = process.stderr.strip()

        # Modified success/error logic
        if process.returncode == 0 and not "Error:" in process.stdout and not "Error with mistral:" in process.stdout:
            result_dict["status"] = "success"
        else:
            result_dict["status"] = "error"

    except Exception as e:
        result_dict["status"] = "error"
        result_dict["error"] = str(e)

    result_dict["duration"] = (datetime.now() - start_time).total_seconds()
    print_command_result(result_dict)
    return result_dict

def print_summary(results: list, log_file: Path, json_file: Path) -> None:
    successful = sum(1 for r in results if r["status"] == "success")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = sum(1 for r in results if r["status"] == "error")

    console.print("\n[bold]Test Summary[/]")
    console.print(f"Total:    {len(results)}")
    console.print(f"Success:  [green]{successful}[/]")
    console.print(f"Skipped:  [yellow]{skipped}[/]")
    console.print(f"Failed:   [red]{failed}[/]")

    # Clean path output
    console.print("\n[bold]Results saved to:[/]")
    log_path = str(log_file).replace("/Users/ctavolazzi/Code/datavault/", "~/")
    json_path = str(json_file).replace("/Users/ctavolazzi/Code/datavault/", "~/")
    console.print(f"Log:  {log_path}")
    console.print(f"JSON: {json_path}")

def test_all_commands():
    """Run all test commands and save results"""
    console.print("\n[bold blue]Starting Command Tests[/]")

    debug_env_keys()

    commands = [
        "list",
        "list --path .",
        "list --all --show-size",
        "news --topic technology --limit 3",
        "news --topic science --ai-service ollama",
        "project status",
        "content scan",
        "ai 'What is Python?'"
    ]

    results = [run_command(cmd) for cmd in commands]

    # Save results
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_commands": len(commands),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "error"),
        "results": results
    }

    with open(json_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print_summary(results, log_file, json_file)

if __name__ == "__main__":
    test_all_commands()