# AI Command Test Report

Generated: 2024-11-13 15:48:54

## Summary
- Total Tests: 5
- Successful: 0
- Failed: 5

## Detailed Results

### Basic Question
- Prompt: What is Python?
- Options: {'provider': None, 'model': None, 'system': 'You are a helpful assistant.', 'save': False, 'no_history': False}
- Error: 1
- Traceback:
```
Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 147, in handle_ai
    if total_elapsed > elapsed + 1:  # If initialization took more than 1 second
UnboundLocalError: local variable 'elapsed' referenced before assignment

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/tests/test_ai_commands.py", line 88, in run_ai_command_tests
    response = handle_ai(
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 183, in handle_ai
    raise typer.Exit(1)
click.exceptions.Exit: 1

```

### With Save Flag
- Prompt: What are the benefits of AI?
- Options: {'provider': None, 'model': None, 'system': 'You are a helpful assistant.', 'save': True, 'no_history': False}
- Error: 1
- Traceback:
```
Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 147, in handle_ai
    if total_elapsed > elapsed + 1:  # If initialization took more than 1 second
UnboundLocalError: local variable 'elapsed' referenced before assignment

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/tests/test_ai_commands.py", line 88, in run_ai_command_tests
    response = handle_ai(
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 183, in handle_ai
    raise typer.Exit(1)
click.exceptions.Exit: 1

```

### Custom System Prompt
- Prompt: Tell me a joke
- Options: {'provider': None, 'model': None, 'system': 'You are a funny assistant.', 'save': False, 'no_history': False}
- Error: 1
- Traceback:
```
Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 147, in handle_ai
    if total_elapsed > elapsed + 1:  # If initialization took more than 1 second
UnboundLocalError: local variable 'elapsed' referenced before assignment

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/tests/test_ai_commands.py", line 88, in run_ai_command_tests
    response = handle_ai(
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 183, in handle_ai
    raise typer.Exit(1)
click.exceptions.Exit: 1

```

### OpenAI Provider
- Prompt: What's the meaning of life?
- Options: {'provider': 'openai', 'model': None, 'system': 'You are a helpful assistant.', 'save': False, 'no_history': False}
- Error: 1
- Traceback:
```
Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 147, in handle_ai
    if total_elapsed > elapsed + 1:  # If initialization took more than 1 second
UnboundLocalError: local variable 'elapsed' referenced before assignment

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/tests/test_ai_commands.py", line 88, in run_ai_command_tests
    response = handle_ai(
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 183, in handle_ai
    raise typer.Exit(1)
click.exceptions.Exit: 1

```

### No History
- Prompt: This shouldn't be saved
- Options: {'provider': None, 'model': None, 'system': 'You are a helpful assistant.', 'save': False, 'no_history': True}
- Error: 1
- Traceback:
```
Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 147, in handle_ai
    if total_elapsed > elapsed + 1:  # If initialization took more than 1 second
UnboundLocalError: local variable 'elapsed' referenced before assignment

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/tests/test_ai_commands.py", line 88, in run_ai_command_tests
    response = handle_ai(
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 183, in handle_ai
    raise typer.Exit(1)
click.exceptions.Exit: 1

```

