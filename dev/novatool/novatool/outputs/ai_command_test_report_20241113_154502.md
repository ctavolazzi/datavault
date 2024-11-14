# AI Command Test Report

Generated: 2024-11-13 15:45:06

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
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 213, in ask_ollama
    return format_streamed_response(stream)
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 388, in format_streamed_response
    with Live(
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/live.py", line 166, in __enter__
    self.start(refresh=self._renderable is not None)
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/live.py", line 113, in start
    self.console.set_live(self)
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/console.py", line 836, in set_live
    raise errors.LiveError("Only one live display may be active at once")
rich.errors.LiveError: Only one live display may be active at once

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 133, in handle_ai
    response = ask_ollama(prompt=prompt, model=model, system=system)
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 219, in ask_ollama
    raise typer.Exit(1)
click.exceptions.Exit: 1

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/tests/test_ai_commands.py", line 88, in run_ai_command_tests
    response = handle_ai(
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 174, in handle_ai
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
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 213, in ask_ollama
    return format_streamed_response(stream)
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 388, in format_streamed_response
    with Live(
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/live.py", line 166, in __enter__
    self.start(refresh=self._renderable is not None)
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/live.py", line 113, in start
    self.console.set_live(self)
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/console.py", line 836, in set_live
    raise errors.LiveError("Only one live display may be active at once")
rich.errors.LiveError: Only one live display may be active at once

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 133, in handle_ai
    response = ask_ollama(prompt=prompt, model=model, system=system)
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 219, in ask_ollama
    raise typer.Exit(1)
click.exceptions.Exit: 1

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/tests/test_ai_commands.py", line 88, in run_ai_command_tests
    response = handle_ai(
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 174, in handle_ai
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
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 213, in ask_ollama
    return format_streamed_response(stream)
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 388, in format_streamed_response
    with Live(
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/live.py", line 166, in __enter__
    self.start(refresh=self._renderable is not None)
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/live.py", line 113, in start
    self.console.set_live(self)
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/console.py", line 836, in set_live
    raise errors.LiveError("Only one live display may be active at once")
rich.errors.LiveError: Only one live display may be active at once

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 133, in handle_ai
    response = ask_ollama(prompt=prompt, model=model, system=system)
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 219, in ask_ollama
    raise typer.Exit(1)
click.exceptions.Exit: 1

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/tests/test_ai_commands.py", line 88, in run_ai_command_tests
    response = handle_ai(
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 174, in handle_ai
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
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 253, in ask_openai
    return format_streamed_response(response)
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 388, in format_streamed_response
    with Live(
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/live.py", line 166, in __enter__
    self.start(refresh=self._renderable is not None)
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/live.py", line 113, in start
    self.console.set_live(self)
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/console.py", line 836, in set_live
    raise errors.LiveError("Only one live display may be active at once")
rich.errors.LiveError: Only one live display may be active at once

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 135, in handle_ai
    response = ask_openai(prompt=prompt, model=model, system=system)
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 259, in ask_openai
    raise typer.Exit(1)
click.exceptions.Exit: 1

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/tests/test_ai_commands.py", line 88, in run_ai_command_tests
    response = handle_ai(
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 174, in handle_ai
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
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 213, in ask_ollama
    return format_streamed_response(stream)
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 388, in format_streamed_response
    with Live(
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/live.py", line 166, in __enter__
    self.start(refresh=self._renderable is not None)
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/live.py", line 113, in start
    self.console.set_live(self)
  File "/Users/ctavolazzi/.pyenv/versions/3.10.13/lib/python3.10/site-packages/rich/console.py", line 836, in set_live
    raise errors.LiveError("Only one live display may be active at once")
rich.errors.LiveError: Only one live display may be active at once

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 133, in handle_ai
    response = ask_ollama(prompt=prompt, model=model, system=system)
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 219, in ask_ollama
    raise typer.Exit(1)
click.exceptions.Exit: 1

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/tests/test_ai_commands.py", line 88, in run_ai_command_tests
    response = handle_ai(
  File "/Users/ctavolazzi/Code/datavault/dev/novatool/novatool/commands/ai_cmd.py", line 174, in handle_ai
    raise typer.Exit(1)
click.exceptions.Exit: 1

```

