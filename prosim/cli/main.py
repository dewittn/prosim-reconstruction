"""
PROSIM Command-Line Interface.

Usage:
    prosim new          Start a new game
    prosim load FILE    Load a saved game
    prosim process      Process a week with DECS file
    prosim --help       Show this help message
"""

import click

from prosim import __version__


@click.group()
@click.version_option(version=__version__, prog_name="PROSIM")
def cli() -> None:
    """
    PROSIM - A Production Management Simulation

    A reconstruction of the 1968 PROSIM simulation game for educational use.
    """
    pass


@cli.command()
def new() -> None:
    """Start a new game."""
    click.echo("Starting new game...")
    click.echo("(Not yet implemented - see IMPLEMENTATION_PLAN.md Phase 4)")


@cli.command()
@click.argument("file", type=click.Path(exists=True))
def load(file: str) -> None:
    """Load a saved game from FILE."""
    click.echo(f"Loading game from {file}...")
    click.echo("(Not yet implemented - see IMPLEMENTATION_PLAN.md Phase 4)")


@cli.command()
@click.option("--decs", type=click.Path(exists=True), help="DECS decision file")
@click.option("--state", type=click.Path(exists=True), help="Current game state file")
@click.option("--output", type=click.Path(), help="Output REPT file path")
def process(decs: str | None, state: str | None, output: str | None) -> None:
    """Process a week using a DECS decision file."""
    click.echo("Processing week...")
    if decs:
        click.echo(f"  DECS file: {decs}")
    if state:
        click.echo(f"  State file: {state}")
    if output:
        click.echo(f"  Output: {output}")
    click.echo("(Not yet implemented - see IMPLEMENTATION_PLAN.md Phase 4)")


@cli.command()
def info() -> None:
    """Show information about PROSIM."""
    click.echo(
        """
PROSIM - Production Management Simulation
==========================================

Original Authors (1968-1996):
  - Paul S. Greenlaw
  - Michael P. Hottenstein
  - Chao-Hsien Chu

Reconstruction (2024):
  - Nelson DeWitt

This is a clean-room reconstruction of the original PROSIM simulation
game, rebuilt for educational preservation and modern use.

For more information, see:
  - README.md
  - IMPLEMENTATION_PLAN.md
  - archive/docs/PROSIM_CASE_STUDY.md
"""
    )


if __name__ == "__main__":
    cli()
