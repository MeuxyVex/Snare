# Contributing to Snare

Use [ROADMAP.md](ROADMAP.md) to choose a task with completed dependencies.
Keep each pull request focused on one task and describe how you verified it.

Install [uv](https://docs.astral.sh/uv/) and use Python 3.11 or newer.

```sh
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict
uv run pytest
```

Use synthetic fixtures for tests. Keep samples, guest captures, memory dumps,
license keys, and credentials out of the repository. Follow the
[roadmap's lab safety rules](ROADMAP.md#1-hard-rules-never-break-these)
when working on features that handle samples.
