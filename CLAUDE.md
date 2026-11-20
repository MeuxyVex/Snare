# Working on Snare

Read [README.md](README.md) for the project overview and [ROADMAP.md](ROADMAP.md) for the implementation plan. Pick the first open task whose dependencies are complete. Mark it in progress before writing code. Keep one task per branch and pull request. Record any blocker under the task. Mark it done only after meeting its acceptance criteria, and include the date and commit or pull request.

## Lab and test data

- Keep all sample handling inside the isolated guest. Use host firewall rules to prevent the guest from reaching the host LAN. Keep routine tests offline and use synthetic fixtures.
- Keep samples, credentials, license keys, dumps and captures out of Git. Preserve the ignore rules for `samples/`, `runs/`, `*.dmp`, `*.raw`, `*.elf`, `*.pcap*` and `*.vmem`.
- Use host-side observation during analysis. Keep calibration tools out of the clean analysis snapshot.
- Scope tests to software and artifacts owned by the project or explicitly authorized for analysis. Keep contributions focused on detection, containment and reporting.

## Technical decisions

- Develop host features for Ubuntu 24.04 LTS or Debian 12. The initial VM backend is KVM/QEMU with libvirt and a 64-bit Windows guest. The roadmap reserves the live introspection backend decision for P5.2.
- Use Python 3.11+, uv, Typer and Pydantic v2. Generate JSON schemas from the models and validate YAML game profiles. Keep Volatility 3 and MemProcFS as external tools.
- Use FastAPI and Jinja2 for planned web interfaces. The planned performance core uses Rust and PyO3. Document changes to the roadmap's technical decisions in an ADR.
- Run Ruff, strict mypy and pytest. Add unit tests for new modules and detector integration coverage using owned or synthetic fixtures. Run Clippy with warnings denied when the Rust core lands.

## Run storage

Each run lives under `runs/<run_id>/`, and `runs/index.sqlite` indexes the runs. IDs use `YYYYMMDD-HHMMSS-<mode>-<8 hex>`.

- `metadata.json` records run metadata. `timeline.jsonl` stores events ordered by host monotonic time. `markers.jsonl` stores analyst markers. `findings.json` stores the findings list.
- `memory/`, `extracted/`, `volatility/` and `network/` store evidence and tool output. Reports start at `report/index.html`.

Treat the [run directory layout in ROADMAP.md](ROADMAP.md#run-directory-layout-contract-between-all-components) as a contract. If the layout changes, update the roadmap, bump the metadata schema version, add a migration and preserve compatibility for `snare runs list`.
