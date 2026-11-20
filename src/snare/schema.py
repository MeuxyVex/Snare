"""JSON Schema export for analysis artifacts."""

import json
from pathlib import Path
from typing import Annotated

import typer

from snare.models import Event, Finding

app = typer.Typer(help="Manage analysis artifact schemas.")


@app.command()
def export(
    output_dir: Annotated[
        Path, typer.Option(help="Directory for JSON Schema files.")
    ] = Path("schemas"),
) -> None:
    """Export the event and finding JSON schemas."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, model in (("event", Event), ("finding", Finding)):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            **model.model_json_schema(),
        }
        path = output_dir / f"{name}.schema.json"
        path.write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        typer.echo(path)
