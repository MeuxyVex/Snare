from pathlib import Path

import pytest
from typer.testing import CliRunner

from snare.cli import app
from snare.models import Event
from snare.timeline import additions, read_events

RUNNER = CliRunner()
FIXTURE = Path(__file__).parent / "fixtures" / "detectors" / "v1"


def read_timeline(name: str) -> list[Event]:
    return list(read_events(FIXTURE / f"{name}.jsonl"))


def test_diff_emits_only_additions_in_observed_order() -> None:
    baseline = FIXTURE / "baseline.jsonl"
    observed = FIXTURE / "observed.jsonl"
    result = RUNNER.invoke(app, ["timeline", "diff", str(baseline), str(observed)])

    assert result.exit_code == 0, result.output
    actual = [Event.model_validate_json(line) for line in result.stdout.splitlines()]
    expected = read_timeline("observed")[len(read_timeline("baseline")) :]
    assert actual == expected

    identical = RUNNER.invoke(app, ["timeline", "diff", str(observed), str(observed)])
    assert identical.exit_code == 0, identical.output
    assert identical.stdout == ""


def test_event_matching_ignores_timestamps_but_counts_repeats() -> None:
    event = read_timeline("baseline")[0]
    first = event.model_copy(update={"t_ns": 1000})
    repeat = event.model_copy(update={"t_ns": 2000})

    assert list(additions([event], [first, repeat])) == [repeat]


@pytest.mark.parametrize("bad_row", ["not JSON", '{"t_ns": 0}'])
def test_invalid_input_reports_row_without_partial_output(
    tmp_path: Path, bad_row: str
) -> None:
    baseline = FIXTURE / "baseline.jsonl"
    observed = tmp_path / "observed.jsonl"
    observed.write_text(
        read_timeline("observed")[-1].model_dump_json() + f"\n{bad_row}\n",
        encoding="utf-8",
    )

    result = RUNNER.invoke(app, ["timeline", "diff", str(baseline), str(observed)])
    assert result.exit_code == 1
    assert not result.stdout
    assert f"{observed}:2:" in result.stderr


def test_diff_rejects_timestamps_out_of_order(tmp_path: Path) -> None:
    baseline = FIXTURE / "baseline.jsonl"
    observed = tmp_path / "observed.jsonl"
    events = read_timeline("observed")
    observed.write_text(
        "\n".join(event.model_dump_json() for event in reversed(events)),
        encoding="utf-8",
    )

    result = RUNNER.invoke(app, ["timeline", "diff", str(baseline), str(observed)])
    assert result.exit_code == 1
    assert not result.stdout
    assert "t_ns is earlier" in result.stderr
