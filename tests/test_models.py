import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from pydantic import ValidationError
from typer.testing import CliRunner

from snare.cli import app
from snare.models import Event, Finding, Marker, Run

PROJECT = Path(__file__).resolve().parents[1]
TIME = "2026-11-10T18:02:16Z"


@pytest.fixture
def finding_payload() -> dict[str, object]:
    readme = (PROJECT / "README.md").read_text(encoding="utf-8")
    section = readme.split("## Example finding (JSON)", 1)[1]
    payload = json.loads(section.split("```json", 1)[1].split("```", 1)[0])
    assert isinstance(payload, dict)
    return dict(payload)


def test_finding_round_trip(finding_payload: dict[str, object]) -> None:
    finding = Finding.model_validate(finding_payload)
    assert Finding.model_validate_json(finding.model_dump_json()) == finding


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("confidence", 1.01),
        ("type", "undotted"),
        ("evidence", ["../outside.bin"]),
        ("evidence", ["C:/outside.bin"]),
    ],
)
def test_invalid_finding(
    finding_payload: dict[str, object], field: str, value: object
) -> None:
    finding_payload[field] = value
    with pytest.raises(ValidationError, match=field):
        Finding.model_validate(finding_payload)


def test_marker_and_event_round_trip() -> None:
    marker = Marker.model_validate(
        {"t_ns": 10, "wall_time": TIME, "text": "Demo started"}
    )
    assert Marker.model_validate_json(marker.model_dump_json()) == marker

    event = marker.to_event()
    assert event.source == "analyst"
    assert event.data == {"text": "Demo started"}
    assert Event.model_validate_json(event.model_dump_json()) == event


def test_run_round_trip() -> None:
    run = Run.model_validate(
        {
            "run_id": "20261110-180216-baseline-a1b2c3d4",
            "profile": "demo",
            "mode": "baseline",
            "network": "cut",
            "started_at": TIME,
            "snare_version": "0.1.0",
        }
    )
    assert Run.model_validate_json(run.model_dump_json()) == run


def test_exported_schemas(tmp_path: Path, finding_payload: dict[str, object]) -> None:
    result = CliRunner().invoke(
        app, ["schema", "export", "--output-dir", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output

    event = Marker.model_validate(
        {"t_ns": 10, "wall_time": TIME, "text": "Ready"}
    ).to_event()
    for name, payload in (
        ("finding", finding_payload),
        ("event", event.model_dump(mode="json")),
    ):
        filename = f"{name}.schema.json"
        generated = (tmp_path / filename).read_text(encoding="utf-8")
        assert generated == (PROJECT / "schemas" / filename).read_text(encoding="utf-8")
        schema = json.loads(generated)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)
