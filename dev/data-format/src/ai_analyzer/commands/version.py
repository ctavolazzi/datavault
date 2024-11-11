import click
import logging
import platform
import sys
from datetime import datetime

logger = logging.getLogger('datavault')

@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed version information')
def version(verbose: bool):
    """Show version information"""
    logger.info("Executing version command")

    click.echo(click.style("\n🤖 Datavault Version Information", fg='bright_blue', bold=True))

    version_info = "0.1.0"
    logger.info(f"Version: {version_info}")
    click.echo(f"\nVersion: {version_info}")

    if verbose:
        logger.debug("Showing verbose version information")

        # System information
        click.echo(click.style("\nSystem Information:", fg='bright_blue'))
        sys_info = {
            "Python": platform.python_version(),
            "Platform": platform.platform(),
            "Installation": sys.prefix
        }
        for key, value in sys_info.items():
            logger.debug(f"{key}: {value}")
            click.echo(f"  {key}: {value}")

        # Build information
        click.echo(click.style("\nBuild Information:", fg='bright_blue'))
        build_info = {
            "Build Date": datetime.now().strftime('%Y-%m-%d'),
            "Build Type": "Development"
        }
        for key, value in build_info.items():
            logger.debug(f"{key}: {value}")
            click.echo(f"  {key}: {value}")

    logger.info("Version command completed")