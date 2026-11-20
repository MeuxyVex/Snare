# Synthetic detector fixtures

Use this dataset to test code that consumes normalized Snare events. All events
are fabricated. `observed.jsonl` starts with the same baseline events and adds a
cross-process read handle, an image integrity change and an outbound flow. The
network destination is from the documentation address range.

`expected-findings.json` describes the target results for these inputs. A
`timeline#N` reference in this fixture uses a zero-based index into
`observed.jsonl`. A changed image is represented as a generic integrity finding
because these events provide no evidence about how the change happened.

The current tests verify fixture contracts and evidence references. As detectors
are implemented, their tests can consume the fixture and compare actual results
against the expected findings. Use a new version directory for incompatible
changes to the fixture format.

From the checkout, compare the synthetic timelines without starting a VM:

```sh
uv run snare timeline diff tests/fixtures/detectors/v1/baseline.jsonl tests/fixtures/detectors/v1/observed.jsonl
```

The expected output is three JSONL rows in observed order. The command matches
events on source, kind, and their exact data. Timestamps do not affect
matching, and repeated events are counted. Run-specific data such as PIDs can
differ between real runs. This command reports event differences without
classifying them as findings.
