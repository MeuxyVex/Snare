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
