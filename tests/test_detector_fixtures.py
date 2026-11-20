from pathlib import Path

from pydantic import TypeAdapter

from snare.models import Event, Finding

FIXTURE = Path(__file__).parent / "fixtures" / "detectors" / "v1"


def read_timeline(name: str) -> list[Event]:
    return [
        Event.model_validate_json(line)
        for line in (FIXTURE / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def test_fixture_timelines_share_an_ordered_baseline() -> None:
    baseline = read_timeline("baseline")
    observed = read_timeline("observed")

    assert baseline
    assert len(observed) > len(baseline)
    assert observed[: len(baseline)] == baseline
    for events in (baseline, observed):
        assert all(a.t_ns < b.t_ns for a, b in zip(events, events[1:], strict=False))


def test_fixture_findings_reference_observed_events() -> None:
    baseline = read_timeline("baseline")
    observed = read_timeline("observed")
    findings = TypeAdapter(list[Finding]).validate_json(
        (FIXTURE / "expected-findings.json").read_bytes()
    )

    assert findings
    assert len({finding.id for finding in findings}) == len(findings)
    for finding in findings:
        assert finding.evidence
        for reference in finding.evidence:
            assert reference.startswith("timeline#")
            index = int(reference.removeprefix("timeline#"))
            assert len(baseline) <= index < len(observed)
            assert finding.first_seen == observed[index].wall_time
