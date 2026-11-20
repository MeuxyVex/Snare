"""Command-line entry point for Snare."""

from typing import Annotated

import typer

from snare import __version__
from snare.schema import app as schema_app


def _show_version(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def root(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version", callback=_show_version, is_eager=True, help="Show the version."
        ),
    ] = False,
) -> None:
    """Snare analysis sandbox."""
    if ctx.invoked_subcommand is None:
        typer.echo("Use snare --help to see available options.")


app = typer.Typer(add_completion=False)
app.callback(invoke_without_command=True)(root)
app.add_typer(schema_app, name="schema")


def main() -> None:
    app()
