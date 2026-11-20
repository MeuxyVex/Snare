"""Compare existing JSONL event timelines without connecting to a lab host."""

import json
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from snare.models import Event

app = typer.Typer(help="Inspect offline JSONL timelines.")


def read_events(path: Path) -> Iterator[Event]:
    """Read a timeline and report malformed rows with their file and line."""
    with path.open("rb") as stream:
        previous = -1
        for number, line in enumerate(stream, start=1):
            try:
                event = Event.model_validate_json(line)
            except ValidationError as error:
                issue = error.errors(include_input=False, include_url=False)[0]
                field = ".".join(map(str, issue["loc"]))
                detail = f"{field}: {issue['msg']}" if field else issue["msg"]
                raise ValueError(f"{path}:{number}: {detail}") from error
            if event.t_ns < previous:
                raise ValueError(
                    f"{path}:{number}: t_ns is earlier than the preceding event."
                )
            previous = event.t_ns
            yield event


def _signature(event: Event) -> tuple[str, str, str]:
    return event.source, event.kind, json.dumps(event.data, sort_keys=True)


def additions(baseline: Iterable[Event], observed: Iterable[Event]) -> Iterator[Event]:
    """Yield extra observed occurrences, matching event payloads without timestamps."""
    remaining = Counter(_signature(event) for event in baseline)
    for event in observed:
        signature = _signature(event)
        if remaining[signature]:
            remaining[signature] -= 1
        else:
            yield event


@app.command()
def diff(
    baseline: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    observed: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
) -> None:
    """Emit added events as JSONL, in observed order."""
    try:
        # Validate both inputs before emitting results.
        result = list(additions(read_events(baseline), read_events(observed)))
    except (OSError, ValueError) as error:
        typer.echo(f"Timeline comparison failed: {error}", err=True)
        raise typer.Exit(1) from error
    for event in result:
        typer.echo(event.model_dump_json())
