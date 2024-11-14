import sys
from pathlib import Path
import typer
from datetime import datetime
from rich.console import Console
import json
import traceback
import os

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from novatool.commands.ai_cmd import handle_ai, view_history
from novatool.utils.ai_config import AIService

console = Console()

def run_ai_command_tests():
    """Run a series of tests for the AI command and generate a report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outputs_dir = project_root / "novatool" / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    report_file = outputs_dir / f"ai_command_test_report_{timestamp}.md"
    results = []

    test_cases = [
        {
            "name": "Basic Question",
            "prompt": "What is Python?",
            "provider": None,
            "model": None,
            "system": "You are a helpful assistant.",
            "save": False,
            "no_history": False
        },
        {
            "name": "With Save Flag",
            "prompt": "What are the benefits of AI?",
            "provider": None,
            "model": None,
            "system": "You are a helpful assistant.",
            "save": True,
            "no_history": False
        },
        {
            "name": "Custom System Prompt",
            "prompt": "Tell me a joke",
            "provider": None,
            "model": None,
            "system": "You are a funny assistant.",
            "save": False,
            "no_history": False
        },
        {
            "name": "OpenAI Provider",
            "prompt": "What's the meaning of life?",
            "provider": AIService.OPENAI.value,
            "model": None,
            "system": "You are a helpful assistant.",
            "save": False,
            "no_history": False
        },
        {
            "name": "No History",
            "prompt": "This shouldn't be saved",
            "provider": None,
            "model": None,
            "system": "You are a helpful assistant.",
            "save": False,
            "no_history": True
        }
    ]

    console.print("\n[bold blue]Starting AI Command Tests[/]\n")

    for test in test_cases:
        try:
            console.print(f"[bold]Testing: {test['name']}[/]")

            # Skip OpenAI test if no API key is available
            if test.get('provider') == AIService.OPENAI.value and not os.getenv('OPENAI_API_KEY'):
                console.print("[yellow]Skipping OpenAI test - no API key available[/]\n")
                continue

            start_time = datetime.now()

            response = handle_ai(
                prompt=test['prompt'],
                provider=test['provider'],
                model=test['model'],
                system=test['system'],
                save=test['save'],
                no_history=test['no_history']
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "name": test['name'],
                "prompt": test['prompt'],
                "response": response,
                "duration": duration,
                "success": bool(response),
                "options": {k: v for k, v in test.items() if k not in ['name', 'prompt']}
            }

            results.append(result)
            console.print(f"[green]✓[/] Test completed in {duration:.2f}s\n")

        except Exception as e:
            error_traceback = traceback.format_exc()

            results.append({
                "name": test['name'],
                "prompt": test['prompt'],
                "error": str(e),
                "traceback": error_traceback,
                "success": False,
                "options": {k: v for k, v in test.items() if k not in ['name', 'prompt']}
            })
            console.print(f"[red]✗[/] Test failed in {test['name']}:")
            console.print(f"[red]{error_traceback}[/]\n")

    # Test history viewing
    try:
        console.print("[bold]Testing: View History[/]")
        view_history(limit=3)
        console.print("[green]✓[/] History view test completed\n")
    except Exception as e:
        console.print(f"[red]✗[/] History view test failed: {str(e)}\n")

    # Generate report
    with open(report_file, 'w') as f:
        f.write("# AI Command Test Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Summary
        successes = sum(1 for r in results if r['success'])
        f.write(f"## Summary\n")
        f.write(f"- Total Tests: {len(results)}\n")
        f.write(f"- Successful: {successes}\n")
        f.write(f"- Failed: {len(results) - successes}\n\n")

        # Detailed Results
        f.write("## Detailed Results\n\n")
        for result in results:
            f.write(f"### {result['name']}\n")
            f.write(f"- Prompt: {result['prompt']}\n")
            f.write(f"- Options: {result['options']}\n")
            if result['success']:
                f.write(f"- Duration: {result.get('duration', 0):.2f}s\n")
                f.write(f"- Response: {result['response']}\n")
            else:
                f.write(f"- Error: {result.get('error', 'Unknown error')}\n")
                f.write("- Traceback:\n```\n")
                f.write(result.get('traceback', 'No traceback available'))
                f.write("\n```\n")
            f.write("\n")

    console.print(f"[bold green]Test report generated:[/] {report_file}")

    # Save raw results as JSON for potential further analysis
    with open(outputs_dir / f"ai_command_test_results_{timestamp}.json", 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    typer.run(run_ai_command_tests)