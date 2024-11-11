import click
from .commands import version, analyze, setup, logs_command
from .utils.logger import setup_logging
from .utils.errors import handle_error

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@handle_error
def cli(debug):
    """Datavault - AI-Powered Data Analysis Tool"""
    logger = setup_logging(debug)
    logger.info("Starting Datavault CLI")

# Register commands
cli.add_command(version)
cli.add_command(analyze)
cli.add_command(setup)
cli.add_command(logs_command, name='logs')

if __name__ == '__main__':
    cli()