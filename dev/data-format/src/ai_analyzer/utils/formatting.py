import click

def style_success(text): return click.style(text, fg='green', bold=True)
def style_error(text): return click.style(text, fg='red', bold=True)
def style_warning(text): return click.style(text, fg='yellow')
def style_info(text): return click.style(text, fg='cyan')
def style_highlight(text): return click.style(text, fg='magenta', bold=True)