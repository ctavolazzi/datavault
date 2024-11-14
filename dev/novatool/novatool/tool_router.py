#!/usr/bin/env python3
import typer
from .commands.news_cmd import get_news_summary
from .commands.content_cmd import handle_content
from .commands.project_cmd import handle_project
from .commands.ai_cmd import handle_ai
from .commands.list_cmd import handle_list

app = typer.Typer()

# Register commands
app.command(name="news")(get_news_summary)
app.command(name="content")(handle_content)
app.command(name="project")(handle_project)
app.command(name="ai")(handle_ai)
app.command(name="list")(handle_list)

if __name__ == "__main__":
    app()