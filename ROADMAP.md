# Snare — Roadmap

> This file is the **single source of truth for what to build next**.
> It is written so that any developer or AI coding agent can open it, find the next task, and complete it without extra context.
> Read [README.md](README.md) first for the vision and the three core principles.

---

## 0. How to use this file (instructions for AI agents)

1. **Read** `README.md`, then this file entirely, before writing any code.
2. **Pick the next task**: the first task (in document order) whose status is `[ ]` and whose **Depends on** tasks are all `[x]`.
3. **Mark it in progress** (`[~]`) before starting.
4. **Do only that task.** One task = one branch = one pull request. Do not start unrelated work.
5. **Meet every acceptance criterion.** If one cannot be met, stop, leave the task `[~]`, and write the blocker under the task in a `Blocker:` line.
6. **Mark it done** (`[x]`) and add a one-line `Done:` note (date + PR/commit) under the task.
7. If you discover missing work, **add a new task** in the right phase with the next free ID. Never renumber existing tasks.
8. Architecture decisions that change section 2 must be recorded as an ADR in `docs/adr/` (see task P0.5) and reflected here.

Status legend: `[ ]` todo · `[~]` in progress · `[x]` done · `[-]` dropped (explain why)

---

## 1. Hard rules (never break these)

**Safety**
- Never execute, open, unpack or emulate a sample on the **host**. Samples run only inside the guest VM.
- Never commit samples, memory dumps, PCAPs, license keys or credentials. `samples/`, `runs/`, `*.dmp`, `*.raw`, `*.elf`, `*.pcap*`, `*.vmem` must stay in `.gitignore`.
- Samples at rest are stored as password-protected zips (password `infected`, industry convention).
- The guest must never reach the host's LAN. Every network mode must be enforced by host firewall rules, not by guest configuration.

**Scope**
- Snare is defensive. The only cheats in this repository are the minimal **test cheats in `demo/`**, which target **only the bundled demo game**.
- No code whose purpose is to bypass a real game's anti-cheat, evade antivirus, or make cheats harder to detect.

**Stealth (principle 1)**
- Nothing Snare-specific may run inside the guest during an analysis run: no agent, no driver, no service, no injected DLL. The only guest-side Snare program is the calibration checker (P1.3), and it must never be present in analysis snapshots.

**Quality**
- Every module has unit tests. Every detector has at least one integration test against the demo game (once P2.1 exists).
- Code must pass `ruff`, `mypy --strict` (Python) and `cargo clippy -D warnings` (Rust) in CI.

---

## 2. Fixed technical decisions

| Topic | Decision |
|---|---|
| Host OS | Linux (Ubuntu 24.04 LTS or Debian 12) |
| First hypervisor | KVM + QEMU + libvirt |
| Introspection hypervisor | Chosen in P5.2 (memflow on KVM, LibVMI/KVM-VMI, or DRAKVUF on Xen) |
| Guest | Windows 10 22H2 / Windows 11, x64 |
| Main language | Python 3.11+ (orchestration, analysis logic, reports, API, MCP) |
| Performance core | Rust crate `snare-core`, exposed to Python with PyO3 + maturin (from P5.1) |
| Python tooling | `uv` (env + deps), `ruff`, `mypy --strict`, `pytest` |
| CLI | Typer — entry point `snare` |
| API / Web | FastAPI + Jinja2 templates; noVNC for the desktop |
| Data models | pydantic v2; JSON Schema files in `schemas/` generated from the models |
| Game profiles | YAML, validated against `schemas/profile.schema.json` |
| Storage | One directory per run on disk + SQLite index (`runs/index.sqlite`) |
| Disassembly | Capstone (Python bindings); Ghidra headless for deep analysis (P6.2) |
| Memory forensics | Volatility 3 and MemProcFS, called as **external tools** (license isolation) |
| Network | dumpcap on the host bridge, Zeek, Suricata (ET Open rules), mitmproxy |
| License | Apache-2.0 |

### Source layout (target)

```
snare/
├── src/snare/
│   ├── cli.py
│   ├── config.py
│   ├── models/          # pydantic: Finding, Event, Run, Profile
│   ├── orchestrator/    # libvirt, snapshots, runs
│   ├── acquisition/     # memory dumps, volatility / memprocfs wrappers
│   ├── introspection/   # live VMI backends (phase 5)
│   ├── network/         # capture, zeek, suricata, tls
│   ├── detectors/       # one file per detector
│   ├── profiles/        # profile loading, symbol resolution, behaviour rules
│   ├── timeline/
│   ├── report/          # html, json, yara export
│   ├── web/             # FastAPI app, noVNC proxy
│   └── mcp/             # MCP server
├── core/                # Rust crate snare-core (phase 5)
├── schemas/
├── stealth/             # libvirt XML templates, calibration checker
├── demo/                # demo game + test cheats + expected findings
├── docs/                # lab setup, ADRs, user guide
└── tests/
```

### Run directory layout (contract between all components)

```
runs/<run_id>/
├── metadata.json        # run id, profile, sample hash, mode, timings, snare version
├── timeline.jsonl       # one Event per line, ordered by host monotonic time
├── findings.json        # list of Finding objects
├── markers.jsonl        # analyst markers
├── memory/              # full dumps: <t_ms>_<reason>.elf
├── extracted/           # dumped modules / regions: <pid>_<base>.bin
├── volatility/          # raw plugin outputs (json)
├── network/
│   ├── capture.pcapng
│   ├── zeek/
│   └── suricata/eve.json
└── report/index.html
```

`run_id` format: `YYYYMMDD-HHMMSS-<mode>-<8 hex>` (e.g. `20261110-180210-cheat-a1b2c3d4`).

---

## 3. Glossary

- **Baseline run**: the game alone, started from the clean snapshot.
- **Cheat run**: the game plus the cheat, from the same snapshot.
- **Diff**: anything present in the cheat run and absent from the baseline.
- **Finding**: one detected fact (a hook, an injected region, a driver…), see `schemas/finding.schema.json`.
- **Event**: one timestamped timeline entry (any source).
- **Game profile**: YAML description of a game's important functions and data.
- **Marker**: an analyst-created timeline event ("key entered").

---

## Phase 0 — Repository foundation

### [x] P0.1 Project scaffold
- **Depends on:** —
- **Goal:** A clean, installable, tested Python project.
- **Deliverables:** `pyproject.toml` (uv), `src/snare/__init__.py`, `src/snare/cli.py` with `snare --version`, `tests/test_cli.py`, `.gitignore` (with the patterns from section 1), `LICENSE` (Apache-2.0), `CONTRIBUTING.md`, `.github/workflows/ci.yml` (ruff, mypy, pytest).
- **Acceptance:** `uv run snare --version` prints the version; CI is green on an empty change.
- **Done:** 2026-11-20, local validation on Python 3.12 accepted by the project owner. GitHub Actions can run after manual upload.

### [x] P0.2 Agent instructions file
- **Depends on:** P0.1
- **Goal:** Give coding agents permanent project rules.
- **Deliverables:** `CLAUDE.md` and `AGENTS.md` (same content) summarising section 1, section 2, the run directory contract, and "follow ROADMAP.md".
- **Acceptance:** Files exist and reference this roadmap; no rule contradicts section 1.
- **Done:** 2026-11-20, integrated and verified locally in AGENTS.md and CLAUDE.md.

### [x] P0.3 Core data models and schemas
- **Depends on:** P0.1
- **Goal:** Stable contracts used by every component.
- **Deliverables:** `src/snare/models/` with pydantic models `Run`, `Event`, `Finding`, `Marker`; `schemas/finding.schema.json`, `schemas/event.schema.json` generated by `snare schema export`; unit tests.
- **Finding fields (minimum):** `id`, `type` (dotted, e.g. `hook.inline`, `memory.private_exec`, `driver.vulnerable`, `access.cross_process`, `network.suspicious_upload`), `severity` (`info|low|medium|high|critical`), `target`, `destination`, `behaviour` (nullable), `first_seen`, `evidence` (list of run-relative paths or `timeline#<n>`), `source` (detector name), `confidence` (0–1).
- **Event fields (minimum):** `t_ns` (host monotonic), `wall_time`, `source` (`memory|kernel|process|network|analyst|orchestrator`), `kind`, `data` (object).
- **Acceptance:** Round-trip tests (model → JSON → model); exported schemas validate the README example finding.
- **Done:** 2026-11-20, commit d91f28c. Verified locally on Python 3.11, 3.12, and 3.13.

### [x] P0.4 Configuration
- **Depends on:** P0.1
- **Goal:** One config file for the host lab.
- **Deliverables:** `snare.example.toml`; `src/snare/config.py` (pydantic-settings). Keys: `libvirt.uri`, `vm.name`, `vm.clean_snapshot`, `paths.runs`, `paths.samples`, `network.default_mode`, `network.bridge`, `tools.volatility`, `tools.memprocfs`, `tools.zeek`, `tools.suricata`.
- **Acceptance:** `snare config check` validates the file and reports missing tools on PATH.
- **Done:** 2026-11-20, commit 72238ab. Verified the example configuration and missing-tool reporting locally.

### [x] P0.5 ADR process
- **Depends on:** P0.1
- **Goal:** Trace architecture decisions.
- **Deliverables:** `docs/adr/0000-template.md`, `docs/adr/0001-python-plus-rust-core.md`, `docs/adr/0002-external-forensics-tools.md`.
- **Acceptance:** ADRs follow the template (context, decision, consequences).
- **Done:** 2026-11-20, commit 54d4868. Verified the ADR structure and roadmap links.

---

## Phase 1 — Analysis lab

### [x] P1.1 Lab setup guide
- **Depends on:** P0.1
- **Goal:** Anyone can reproduce the lab.
- **Deliverables:** `docs/lab-setup.md`: BIOS (VT-x, VT-d), kernel params (`intel_iommu=on iommu=pt`), KVM/libvirt install, VFIO GPU passthrough (bind the spare GPU to `vfio-pci`), Windows guest install, creating snapshot `clean`, verification commands.
- **Acceptance:** Every step has a verification command and its expected output.
- **Done:** 2026-11-20, commit 8914852. Verified guide structure; hardware bring-up remains to be run on a Linux lab host.

### [ ] P1.2 Stealth VM template v0
- **Depends on:** P1.1
- **Goal:** Principle 1 — a guest that looks like real hardware.
- **Deliverables:** `stealth/libvirt/guest.xml.j2` + `snare vm render-xml`. Must include: `<kvm><hidden state='on'/></kvm>`, Hyper-V enlightenments with a custom `vendor_id`, `cpu mode='host-passthrough'` with the `hypervisor` feature disabled, `<sysinfo type='smbios'>` populated from a real-looking hardware profile (`stealth/profiles/*.yaml`), realistic disk model and serial, NIC with a real vendor OUI, no virtio-serial / guest-agent channel, no QXL/virtio-gpu when passthrough is enabled, RAM ≥ 16 GB, ≥ 6 vCPUs.
- **Acceptance:** Rendered XML validates with `virt-xml-validate`; guest boots; the hardware profile values appear in `msinfo32`.

### [ ] P1.3 Calibration checker (detection test suite)
- **Depends on:** P1.2
- **Goal:** Measure how detectable the guest is.
- **Deliverables:** `stealth/checker/` — a small Windows console program (C or Rust) that runs common VM/sandbox checks and outputs JSON: CPUID hypervisor bit and vendor leaf, SMBIOS strings, disk/NIC/GPU device names, MAC OUI, known VM registry keys, files and drivers, process names, RDTSC/CPUID timing ratio, uptime, user-activity artifacts. `snare stealth report <checker.json>` prints a pass/fail table.
- **Acceptance:** Runs on the guest; report lists every check with its result. **The checker is used only in a separate calibration snapshot, never in `clean`.**

### [ ] P1.4 Orchestrator v0
- **Depends on:** P0.3, P0.4, P1.2
- **Goal:** Drive the VM lifecycle.
- **Deliverables:** `src/snare/orchestrator/vm.py` (libvirt-python): `revert(snapshot)`, `start()`, `pause()`, `resume()`, `stop()`, `state()`. CLI: `snare vm revert|start|stop|status`. Every action writes an `orchestrator` Event.
- **Acceptance:** Tests with a mocked libvirt connection; manual test log in the PR showing revert → start → stop.

### [ ] P1.5 Sample delivery without a guest agent
- **Depends on:** P1.4
- **Goal:** Put the game launcher/cheat into the guest without any Snare component inside.
- **Deliverables:** `snare` builds a per-run ISO (`pycdlib`) with the sample and attaches it as a virtual CD-ROM before start; the analyst runs it through the desktop (P4.1) or an autorun scheduled task baked into the snapshot (documented, optional).
- **Acceptance:** The ISO appears in the guest; it is detached and deleted at the end of the run.

### [ ] P1.6 Network modes and host-side capture
- **Depends on:** P1.4
- **Goal:** Isolated, controllable guest networking, captured outside the guest.
- **Deliverables:** `src/snare/network/modes.py` with three modes:
  - `cut`: isolated libvirt network, no route out;
  - `sim`: isolated network + INetSim (fake DNS/HTTP/HTTPS);
  - `vpn`: guest traffic routed through a dedicated network namespace with a WireGuard tunnel.
  For all modes: nftables rules dropping any traffic to RFC1918 ranges and the host (except the simulated services). `src/snare/network/capture.py`: `dumpcap` on the guest bridge for the whole run → `network/capture.pcapng`.
- **Acceptance:** Integration test script proving: in `cut` mode a ping to 1.1.1.1 fails; in every mode the host LAN is unreachable; the PCAP is written and readable by `tshark`.

### [x] P1.7 Offline guest definition
- **Depends on:** P1.1
- **Goal:** Generate a standard libvirt VM definition for the offline lab smoke test.
- **Deliverables:** `snare vm render-xml`, tests, and usage in the lab guide.
- **Acceptance:** The command renders libvirt domain XML for a local qcow2 disk and an optional read-only installer ISO. Automated checks cover local display, boot order, and absence of guest networking and host shares.
- **Done:** 2026-11-20, commit f843dd0. Both XML variants passed the libvirt 10.0 schema. Boot verification requires the lab host.

---

## Phase 2 — MVP analysis

### [ ] P2.1 Demo game and test cheats (ground truth)
- **Depends on:** P0.1
- **Goal:** Known targets to validate every detector.
- **Deliverables:** `demo/game/` — a minimal Windows C++ game (D3D11 window, a few moving "players", functions `Weapon::Fire`, `Player::UpdateMovement`, a global `EntityList`), built with PDB. `demo/cheats/` — test programs that target **only this demo game**:
  - `internal_hook.dll`: inline hook on `Weapon::Fire`;
  - `present_hook.dll`: vtable hook on `IDXGISwapChain::Present` drawing boxes;
  - `external_reader.exe`: reads `EntityList` with `ReadProcessMemory`;
  - `manual_map_loader.exe`: manually maps a small DLL into the game.
  `demo/expected/*.json`: expected findings per cheat. `demo/profile.yaml`: game profile.
- **Acceptance:** Everything builds from `demo/build.ps1`; each cheat visibly works on the demo game only (it looks for the demo's window/process name and exits otherwise).

### [ ] P2.2 Run command and run directory
- **Depends on:** P1.4, P1.5, P1.6, P0.3
- **Goal:** One command produces one complete run directory.
- **Deliverables:** `snare run --profile <yaml> [--sample <file>] --mode baseline|cheat --network cut|sim|vpn --duration <s>`; creates the run directory (section 2 contract), writes `metadata.json`, the timeline and the index entry; `snare runs list`.
- **Acceptance:** A baseline run of the demo game produces a valid run directory; the index lists it.

### [ ] P2.3 Memory acquisition v0
- **Depends on:** P2.2
- **Goal:** Full guest memory snapshots from the host.
- **Deliverables:** `src/snare/acquisition/dump.py`: pause → `virsh dump --memory-only --format elf` (or QMP `dump-guest-memory`) → resume. Triggers: interval (`--dump-every`), end of run, CLI/API on demand (`snare dump <run_id>`). Each dump emits an Event.
- **Acceptance:** Dumps are readable by Volatility 3 (`windows.info`); the guest is paused less than 5 s per dump of 16 GB (document the measured value).

### [ ] P2.4 Volatility wrapper
- **Depends on:** P2.3
- **Goal:** Normalised forensic data from each dump.
- **Deliverables:** `src/snare/acquisition/volatility.py` running plugins `windows.pslist`, `windows.dlllist`, `windows.vadinfo`, `windows.malfind`, `windows.modules`, `windows.driverscan`, `windows.handles`, `windows.threads` with `-r json`, saved in `volatility/` and parsed into typed models.
- **Acceptance:** Parsers tested against recorded JSON fixtures in `tests/fixtures/`.

### [ ] P2.5 Differential engine
- **Depends on:** P2.4
- **Goal:** Only show what the cheat changed.
- **Deliverables:** `src/snare/detectors/diff.py`: compare a cheat run with a baseline run (same profile) and emit Findings for: new processes; new modules in the game process; private executable regions in the game process (`memory.private_exec`); new kernel modules (`driver.new`); handles to the game process opened by foreign processes with `PROCESS_VM_READ`/`PROCESS_VM_WRITE` (`access.cross_process`). CLI: `snare analyze <cheat_run> --baseline <baseline_run>`.
- **Acceptance:** On the demo, `manual_map_loader` yields a `memory.private_exec` finding and `external_reader` yields an `access.cross_process` finding, matching `demo/expected/`.

### [ ] P2.6 Hook detector v0
- **Depends on:** P2.4
- **Goal:** Detect inline, vtable and IAT hooks.
- **Deliverables:** `src/snare/detectors/hooks.py`:
  - extract the in-memory image of the game module and key system DLLs (`dxgi.dll`, `d3d11.dll`, `kernel32.dll`, `ntdll.dll`) from the dump;
  - load the matching on-disk PE (copied from the clean snapshot image, cached in `cache/pe/`), apply relocations for the in-memory base, compare executable sections byte by byte;
  - decode patched sites with Capstone and resolve the jump/call destination to a module or region;
  - IAT: every entry must point into its exporting module;
  - vtables: check `IDXGISwapChain` vtable entries point into `dxgi.dll` (locate via the profile or a known pattern).
  Emits `hook.inline`, `hook.iat`, `hook.vtable`.
- **Acceptance:** `internal_hook.dll` → `hook.inline` on `Weapon::Fire`; `present_hook.dll` → `hook.vtable` on `Present`; zero hook findings on a baseline run.

### [ ] P2.7 Report v0
- **Depends on:** P2.5, P2.6
- **Goal:** A readable result for developers.
- **Deliverables:** `src/snare/report/html.py` (Jinja2): summary, findings table grouped by type and severity, evidence links, run metadata. `findings.json` written alongside. `snare report <run_id>`.
- **Acceptance:** The demo report renders offline (no external assets) and lists all expected findings.

### [ ] P2.8 End-to-end demo test
- **Depends on:** P2.1, P2.7
- **Goal:** Lock the MVP behaviour.
- **Deliverables:** `tests/e2e/test_demo.py` (marked `lab`, skipped in CI without a lab) running baseline + each test cheat and comparing findings with `demo/expected/`.
- **Acceptance:** All four cheats detected; no unexpected high-severity findings in baseline.

### [x] P2.9 Synthetic detector fixtures
- **Depends on:** P0.3
- **Goal:** Give defensive detector tests reproducible input and expected findings without executing sample binaries.
- **Deliverables:** Versioned baseline and observed event fixtures, expected findings, and contract tests under `tests/`.
- **Acceptance:** The fixtures validate against the event and finding contracts. Expected findings reference existing events in the observed fixture. Both timelines are ordered by monotonic time.
- **Done:** 2026-11-20, commit 01b5a29. Verified with the local Python test suite.

### [~] P2.10 Offline timeline comparison
- **Depends on:** P0.3, P2.9
- **Goal:** Compare normalized event timelines without a VM or sample binaries.
- **Deliverables:** `snare timeline diff`, contract tests, and an example in the detector fixture guide.
- **Acceptance:** Comparing the synthetic timelines emits the additional observed events in order. Identical timelines produce no output and invalid inputs yield an actionable error.

---

## Phase 3 — Game-aware analysis

### [ ] P3.1 Symbol resolution
- **Depends on:** P2.6
- **Goal:** Addresses become names.
- **Deliverables:** `src/snare/profiles/symbols.py`: load the game's PDB (profile `symbols`), fetch Windows PDBs from the Microsoft symbol server (cached), resolve `module+rva` → `symbol+offset`. All findings get resolved names when available.
- **Acceptance:** Demo findings show `Weapon::Fire` and `CDXGISwapChain::Present` instead of raw addresses.

### [ ] P3.2 Profile engine and behaviour rules
- **Depends on:** P0.3, P3.1
- **Goal:** Translate findings into cheat behaviour.
- **Deliverables:** `schemas/profile.schema.json`; profile loader; address expressions (`Module.exe+0x1234 -> 0x1C8` pointer chains, or symbol names) resolved against a dump; rule engine (`when` conditions on finding type/target/tags, `means` strings mapped to a controlled vocabulary in `src/snare/profiles/behaviours.py` — `esp`, `wallhack`, `aimbot`, `silent_aim`, `trigger_bot`, `speed_hack`, `fly_hack`, `no_recoil`, `radar`, `overlay`, `memory_patch`, `injection`, `driver_abuse`, `stealer`, `rat`, `miner`); findings gain a `behaviour` field (nullable) populated by the engine.
- **Acceptance:** Demo rules fire: `hook(Weapon::Fire)` → `aim manipulation`, `read(EntityList) by foreign code` → `esp`; a malformed profile fails loading with a line/column error.

### [ ] P3.3 Memory watches via post-hoc diff
- **Depends on:** P3.2, P2.3
- **Goal:** Catch reads/writes of profile data between two dumps, even without VMI.
- **Deliverables:** `src/snare/detectors/data_access.py`: resolve every profile `data` address in both dumps, hash the surrounding region, compare; cross-reference with any process holding a handle to the game with `VM_READ`/`VM_WRITE` at the second dump; emit `access.data_read`/`access.data_write` with the foreign process name. Dump cadence raised automatically when a profile declares `watch: hot` items.
- **Acceptance:** `external_reader.exe` yields `access.data_read` on `EntityList`.

### [ ] P3.4 Timeline
- **Depends on:** P2.4, P2.5, P1.6
- **Goal:** One ordered stream of everything that happened.
- **Deliverables:** `src/snare/timeline/build.py`: merge `orchestrator`, `process` (from Volatility pslist deltas), `memory` (dumps, new regions, hook sites), `network` (from PCAP: TCP/UDP flows, DNS queries, TLS handshakes) and `analyst` events into `timeline.jsonl`, sorted by `t_ns` (host monotonic). Guest-time events are translated with the clock offset recorded at snapshot start.
- **Acceptance:** The demo cheat run's timeline contains, in order: VM revert → start → game pid seen → cheat loader pid → first `access.cross_process` → `hook.inline`.

### [ ] P3.5 Analyst markers
- **Depends on:** P3.4
- **Goal:** Humans annotate the timeline live.
- **Deliverables:** `POST /api/runs/<id>/marker` + CLI `snare marker add <run_id> "<text>"`; markers persisted to `markers.jsonl` and merged into the timeline with `source=analyst`.
- **Acceptance:** A marker added mid-run appears in the timeline and the report, at the right position.

### [ ] P3.6 YARA and IOC export
- **Depends on:** P2.6, P2.5
- **Goal:** Produce reusable indicators from one run.
- **Deliverables:** `src/snare/report/indicators.py`: dump each injected/manually-mapped region to `extracted/`, generate a YARA rule per region (hash + two most distinctive 32-byte sequences chosen by entropy), a `iocs.json` with network IOCs (domains, IPs, JA3/JA4 hashes) and file IOCs (SHA-256 of samples dropped on disk). `snare export <run_id> --yara --iocs`.
- **Acceptance:** YARA rules compile with `yara -c`; running them against the extracted region matches, against a baseline dump does not.

### [ ] P3.7 JSON findings schema freeze v1
- **Depends on:** P3.1, P3.2, P3.6
- **Goal:** External consumers (CI, studio tooling, MCP) can rely on the contract.
- **Deliverables:** Bump `schemas/finding.schema.json` to `$id: .../v1`; document every `type` slug in `docs/findings.md`; add `snare schema diff` to detect breaking changes between versions; CHANGELOG entry.
- **Acceptance:** `snare schema diff v1 v1` returns clean; a hand-crafted broken schema fails the check.

---

## Phase 4 — Interactive desktop and deep network

### [ ] P4.1 noVNC / SPICE desktop
- **Depends on:** P1.4, P2.2
- **Goal:** Analyst drives the guest from the browser without breaking stealth.
- **Deliverables:** `src/snare/web/desktop.py`: proxy the libvirt SPICE/VNC socket over websockets to a noVNC frontend at `/runs/<id>/desktop`; connection auth via a per-run token; keyboard/mouse enabled; file transfer disabled (would need a guest agent, forbidden by section 1).
- **Acceptance:** Analyst can log into a loader interactively; no new device appears in the guest device tree while the desktop is open.

### [ ] P4.2 Zeek integration
- **Depends on:** P1.6
- **Goal:** Structured protocol logs out of every PCAP.
- **Deliverables:** `src/snare/network/zeek.py`: run Zeek offline against `network/capture.pcapng`, parse `conn.log`, `dns.log`, `http.log`, `ssl.log`, `files.log` into Events (`source=network`); emit findings for suspicious uploads (`network.suspicious_upload`: outbound bytes > 1 MB to a non-CDN destination within 60 s of process start).
- **Acceptance:** Sample PCAPs in `tests/fixtures/network/` produce the recorded Events; the upload rule matches the staged fixture, not the baseline browsing fixture.

### [ ] P4.3 Suricata integration
- **Depends on:** P4.2
- **Goal:** Signature-based detection on the captured traffic.
- **Deliverables:** `src/snare/network/suricata.py`: run Suricata offline with ET Open rules (vendored path configurable); parse `eve.json` alerts into Events; findings `network.suricata_alert` with signature id and classification.
- **Acceptance:** A canned PCAP containing a benign EICAR-over-HTTP flow triggers at least one alert in the Event stream.

### [ ] P4.4 TLS fingerprints and decryption
- **Depends on:** P4.2
- **Goal:** Identify and, where possible, read encrypted traffic.
- **Deliverables:** JA3/JA4 computed from `ssl.log` and attached to flow Events; mitmproxy transparent proxy mode wired as an optional mode (`--mitm`) that installs the mitmproxy CA into the clean snapshot once (documented, baked at snapshot build time, not at run time); recovery of TLS session keys from guest memory dumps using `volatility windows.sslkey` (community plugin) when the key material is still resident, written to `network/sslkeys.log` and auto-attached to Wireshark.
- **Acceptance:** With `--mitm`, a known HTTPS GET from the demo shows a decrypted record in the PCAP viewer; without `--mitm`, JA3/JA4 are still populated.

### [ ] P4.5 Network IOCs in the report
- **Depends on:** P4.2, P4.3, P4.4, P2.7
- **Goal:** Network findings land in the HTML report next to memory findings.
- **Deliverables:** Report section "Network": flow table, DNS queries, HTTP(S) targets with JA3/JA4, Suricata alerts, suspicious uploads; each row links to the right offset in the PCAP via `rawshark` filter.
- **Acceptance:** The demo report's network section is non-empty for a cheat run, empty for a cut-mode baseline.

---

## Phase 5 — Agentless introspection

### [ ] P5.1 Rust core `snare-core`
- **Depends on:** P0.3
- **Goal:** Performance-critical paths out of Python without losing the Python front.
- **Deliverables:** `core/` Cargo crate exposed via PyO3 + maturin; initial API: `pe::load`, `pe::diff_executable_sections`, `disasm::decode_at`, `pattern::scan`, `hash::blake3`. Wheels built in CI for Linux x86_64.
- **Acceptance:** `snare.core.pe_diff(a, b)` matches the Python reference on a fixture; benchmark shows ≥10× speed-up on a 4 MB module diff.

### [ ] P5.2 VMI backend decision (ADR 0003)
- **Depends on:** P1.4, P2.3
- **Goal:** Choose the live introspection backend.
- **Deliverables:** `docs/adr/0003-vmi-backend.md` comparing `memflow` (KVM, Rust, no guest kernel symbols required), `LibVMI/KVM-VMI` (KVM patch, mature) and `DRAKVUF on Xen` (requires Xen, richest events). Decision criterion: can run on the lab host described in `docs/lab-setup.md` without re-building a custom kernel; event richness; Rust bindings quality.
- **Acceptance:** ADR merged; the chosen backend has a one-page bring-up guide under `docs/vmi/`.

### [ ] P5.3 Live VMI backend v0
- **Depends on:** P5.2, P5.1
- **Goal:** Stream guest kernel events to the timeline, agentless.
- **Deliverables:** `src/snare/introspection/vmi.py` driving the chosen backend from the Rust core; events: process create/exit, module load, thread create (with start address), handle open with `PROCESS_VM_READ/WRITE`, driver load (`IoCreateDriver`/`MmLoadSystemImage`), file create, registry writes to `Run`/`Services`. Each event enters the timeline as `source=kernel`.
- **Acceptance:** A cheat loader launching the demo cheat produces, live, the same process/driver events that the post-hoc Volatility diff produces; latency budget: ≤ 50 ms per event in the median.

### [ ] P5.4 EPT memory watches
- **Depends on:** P5.3
- **Goal:** Catch accesses to game data without touching the guest.
- **Deliverables:** For each profile `data` region flagged `watch: hot`, set an EPT read/write trap on the containing page(s); on hit, record attacker RIP, process, thread, resolved module+symbol into a `memory.data_watch_hit` Event; coalesce bursts (same RIP within 1 s) into one Event with a counter.
- **Acceptance:** `external_reader.exe` reading `EntityList` fires watch hits attributed to its own RIP; the game's own writer does not fire because its RIP is inside the game module.

### [ ] P5.5 Kernel driver analysis
- **Depends on:** P5.3, P3.6
- **Goal:** Distinguish "signed and known" from "vulnerable BYOVD" from "manually mapped".
- **Deliverables:** `src/snare/detectors/drivers.py`: for every new driver observed in the cheat run, compute SHA-256 and WHQL / Authenticode state from its PE image dumped via VMI; cross-reference `loldrivers.io` snapshot vendored under `data/loldrivers/`; detect manual mapping (`DriverObject->DriverName == NULL` or absent from `PsLoadedModuleList` but present in executable kernel memory) → `driver.manual_map`. Known-bad driver → `driver.vulnerable`.
- **Acceptance:** A staged vulnerable driver load (test fixture signed by an expired cert, declared in `loldrivers`) yields `driver.vulnerable`; a hand-mapped stub yields `driver.manual_map`.

### [ ] P5.6 Live runs
- **Depends on:** P5.3, P5.4, P5.5
- **Goal:** `snare run` can replace most of the Volatility post-hoc diff.
- **Deliverables:** `--live` flag on `snare run`; live Events coexist with periodic dumps (dumps kept for forensic fidelity); detectors in `detectors/live/` consume the live event stream and emit Findings as they happen; the report distinguishes `live` vs `post` provenance on each finding.
- **Acceptance:** On the demo, `snare run --live` produces the same final findings set as the post-hoc path; live findings arrive within 2 s of the triggering guest action (documented measurement in the PR).

---

## Phase 6 — Deep code understanding and AI access

### [ ] P6.1 Capstone-based quick disassembly
- **Depends on:** P5.1
- **Goal:** Short, inline disassembly for every finding's evidence block.
- **Deliverables:** `snare.core.disasm.window(addr, before, after)` returning instructions with resolved call/jump targets using the loaded symbols; HTML report shows a 10-line window at every hook site.
- **Acceptance:** Report windows match `objdump -d` on the fixture binaries.

### [ ] P6.2 Ghidra headless pipeline
- **Depends on:** P6.1
- **Goal:** Deep static analysis on dumped regions and modules, on demand.
- **Deliverables:** `src/snare/analysis/ghidra.py`: wrap `analyzeHeadless` in a container (`ghcr.io/snare/ghidra-headless`) invoked with the dumped region and the matching PDB; export decompiled C for every function touching the hook site; cache results keyed by SHA-256. CLI: `snare decompile <run_id> <finding_id>`.
- **Acceptance:** Decompiling the demo's `internal_hook.dll` region returns readable C for the trampoline; second call hits cache in ≤ 200 ms.

### [ ] P6.3 REST API v1
- **Depends on:** P3.7, P4.5
- **Goal:** Programmatic access to every run artifact.
- **Deliverables:** FastAPI app under `src/snare/web/api.py`; endpoints: `GET /runs`, `GET /runs/{id}`, `GET /runs/{id}/timeline`, `GET /runs/{id}/findings`, `GET /runs/{id}/pcap`, `GET /runs/{id}/dumps/{t_ms}`, `POST /runs/{id}/marker`, `POST /analyze`, `GET /schemas/finding/v1`. OpenAPI published at `/openapi.json`; token auth from `snare.toml`.
- **Acceptance:** `schemathesis run` against `/openapi.json` passes; curl examples in `docs/api.md` execute cleanly.

### [ ] P6.4 MCP server (read-only by default)
- **Depends on:** P6.3, P6.2
- **Goal:** Expose Snare to AI assistants over MCP.
- **Deliverables:** `src/snare/mcp/server.py` exposing tools: `list_runs`, `get_run`, `list_findings`, `read_timeline`, `read_memory(run, addr, size)`, `read_pcap(run, filter)`, `disassemble(run, addr, size)`, `decompile(run, finding_id)`, `search_strings(run, regex)`. Write tools (`add_marker`, `trigger_dump`, `start_run`) gated behind a `--allow-write` flag; every tool call logged to `mcp.jsonl` under the run directory.
- **Acceptance:** A canned Claude transcript in `tests/mcp/test_demo_session.py` resolves the demo's cheat behaviour using only MCP tools; `--allow-write` is required to add a marker.

### [ ] P6.5 Explain engine
- **Depends on:** P6.4, P3.2
- **Goal:** Turn a finding into a paragraph a developer can act on.
- **Deliverables:** `src/snare/report/explain.py`: for a given finding, assemble a prompt pack (finding JSON, nearby timeline window, disassembly window, decompiled C if available, matched profile rule) and render it via a local model backend (`llama-cpp-python`) or the MCP client; output a Markdown block stored at `report/explain/<finding_id>.md`. No telemetry; model path configurable; works fully offline.
- **Acceptance:** On the demo, each expected finding produces an explanation that mentions the function/data name, the hook/access kind and the mapped behaviour.

---

## Phase 7 — Web UI, multi-run and release

### [ ] P7.1 Web UI shell
- **Depends on:** P6.3, P4.1
- **Goal:** One place to run, watch and read analyses.
- **Deliverables:** FastAPI + Jinja2 pages: `/` (runs list with status, mode, duration, findings count), `/runs/{id}` (summary + findings + timeline + report), `/runs/{id}/desktop` (noVNC), `/profiles` (upload/validate), `/samples` (local sample registry with SHA-256, zip-with-password on disk). HTMX for live timeline updates during live runs.
- **Acceptance:** A full session — upload sample, launch cheat run, watch timeline live, open report — works end to end in Firefox and Chromium.

### [ ] P7.2 Run comparison
- **Depends on:** P7.1, P2.5
- **Goal:** Diff two cheat runs (e.g. v1.0 vs v1.1 of the same cheat).
- **Deliverables:** `/compare?left=<run>&right=<run>` showing findings added/removed/unchanged, timeline overlay, network IOC overlap; CLI `snare compare <a> <b>`.
- **Acceptance:** Comparing two runs of the same baseline shows zero differences in findings; comparing baseline vs cheat shows the full cheat finding set as `added`.

### [ ] P7.3 Multi-tenant workspaces (studio mode)
- **Depends on:** P7.1
- **Goal:** Multiple game profiles and sample libraries in one install.
- **Deliverables:** `workspaces/<name>/` holding profiles, samples, runs; workspace switcher in UI and CLI; per-workspace access tokens; no cross-workspace reads.
- **Acceptance:** Two workspaces are fully isolated on disk and in the API; a token scoped to workspace A cannot list workspace B's runs.

### [ ] P7.4 Packaging and release
- **Depends on:** P5.1, P6.3, P7.1
- **Goal:** `uv tool install snare` and `docker run snare` both work.
- **Deliverables:** `pyproject.toml` entry points; `Containerfile` building a rootless OCI image (Python side only; introspection backends run on the host); `snare doctor` prints host readiness (VT-x, IOMMU groups, libvirt reachable, tools on PATH, loldrivers snapshot date); versioning follows SemVer; `CHANGELOG.md` kept per release; GitHub Actions workflow builds wheels + OCI image on tag.
- **Acceptance:** `snare doctor` on a fresh VM lists each check with pass/fail; a tagged release produces a wheel, an sdist and an image, all signed with `cosign`.

### [ ] P7.5 User documentation
- **Depends on:** P7.4
- **Goal:** A developer with no RE background can run the demo end to end.
- **Deliverables:** `docs/` (mkdocs-material): quickstart, lab setup, writing a profile, understanding a report, API/MCP tutorial, FAQ, safety checklist; a 5-minute screencast of the demo flow linked from the README.
- **Acceptance:** A dry run of the quickstart on a fresh machine, timed under 60 min from zero to first report.

---

## Phase 8 — Ongoing stealth, scale and hardening

### [ ] P8.1 Calibration CI
- **Depends on:** P1.3, P7.4
- **Goal:** Catch stealth regressions release by release.
- **Deliverables:** Nightly job on a self-hosted lab runner boots the current `clean+checker` snapshot and runs the P1.3 checker; results posted to `stealth/history/<date>.json`; `docs/stealth.md` renders the last 90 days as a pass/fail matrix; a drop below the previous release fails the job.
- **Acceptance:** A deliberately regressed template (vendor string back to `KVMKVMKVM`) turns the matrix red.

### [ ] P8.2 Stealth profile v1 — SMBIOS, ACPI, disk, NIC
- **Depends on:** P1.2, P8.1
- **Goal:** Close the easy detections.
- **Deliverables:** Real-hardware SMBIOS profiles (`stealth/profiles/dell-xps-8960.yaml`, `stealth/profiles/alienware-r16.yaml`), ACPI tables trimmed of QEMU-specific OEM IDs, disk serials drawn from vendor ranges, NIC OUIs from a curated list (`stealth/ouis.json`), virtio controllers replaced with IDE/AHCI where performance allows; `snare vm render-xml --profile <name>`.
- **Acceptance:** P8.1 matrix moves ≥ 10 checks from fail to pass; game still launches at target FPS (documented).

### [ ] P8.3 Aged user profile generator
- **Depends on:** P1.2
- **Goal:** The guest looks lived-in.
- **Deliverables:** `stealth/aging/age.py` (host-side, mounts the guest disk offline with `guestfs-python`): populate `Documents/`, recent files, browser history (Firefox profile with 30–90 days of plausible history from a seed corpus), installed common apps list, Windows Event Log entries spanning > 30 days of uptime, pagefile size matching RAM; idempotent; records a receipt JSON with every change.
- **Acceptance:** `msinfo32` and common anti-analysis tools (vmaware, Pafish subset) report ≥ 30 days uptime, non-empty user artifacts.

### [ ] P8.4 Performance and scale
- **Depends on:** P5.6, P7.4
- **Goal:** Analyze longer runs without drowning the host.
- **Deliverables:** `tests/bench/` with Locust-like harness driving 1 h synthetic runs; budget targets: dump cost ≤ 5 s per 16 GB, live event handling ≤ 50 ms p50, PCAP processing ≤ 1 min per GB; backpressure on the live event bus (drop with counter instead of OOM); run directories compressed on close (`zstd -T0`).
- **Acceptance:** A 1 h cheat run with an active loader completes without missed events (≥ 99.9 % processed) and lands under 30 GB on disk after compression.

### [ ] P8.5 Security review and hardening
- **Depends on:** P7.4
- **Goal:** The host surface is as small as the guest contains it.
- **Deliverables:** Threat model in `docs/threat-model.md` (STRIDE on each component); API auth via per-token scopes; signed run manifests (`metadata.sig` with `cosign`); `fuzz/` targets for the finding/event parsers and the profile loader (`atheris` / `cargo-fuzz`); `cargo audit` and `pip-audit` in CI; every external tool invocation uses explicit allow-lists for paths and argv.
- **Acceptance:** A one-day fuzzing run on each parser finds no new crashes; `cargo audit` and `pip-audit` clean on main.

### [ ] P8.6 Engine integrations (Unity, Unreal, Godot)
- **Depends on:** P3.2, P3.1
- **Goal:** Game profiles write themselves for common engines.
- **Deliverables:** `src/snare/profiles/engines/`: `unity.py` reads IL2CPP metadata (`global-metadata.dat` + `GameAssembly.dll`) to export class/method/field offsets; `unreal.py` reads UE4/UE5 reflection data (`UObject`/`UFunction` tables) by pattern; `godot.py` reads GDScript/GDExtension exports. Each engine ships a `profile.template.yaml` covering common hot data (local player, entity list, weapon manager).
- **Acceptance:** Running the generator on a reference Unity demo (`demo/unity/`) produces a profile that resolves `LocalPlayer.health` in a dump.

### [ ] P8.7 Community detector plugin API
- **Depends on:** P5.6
- **Goal:** Third parties add detectors without forking.
- **Deliverables:** `src/snare/detectors/plugins.py`: load detectors from entry point `snare.detectors`, each exposing `name`, `version`, `inputs` (which Events/dumps it consumes), `run(ctx) -> Iterable[Finding]`; sandboxed execution (`multiprocessing` with a restricted `sys.path` and no network); `snare detectors list|enable|disable`.
- **Acceptance:** A sample out-of-tree detector plugin (`snare-detector-demo`, in `examples/plugin/`) installs via `uv add`, appears in `snare detectors list` and emits a finding on the demo.

### [ ] P8.8 Long-term signature store
- **Depends on:** P3.6, P7.3
- **Goal:** A studio's catalogue of what hit them, searchable across runs.
- **Deliverables:** `signatures/` table in the workspace SQLite index: YARA rules, byte patterns, network IOCs, each with a source run and a notes field; `/signatures` UI page with search and tag filters; `snare match <run_id>` re-runs the local signature set against a new run.
- **Acceptance:** A YARA rule emitted from run A matches the same region in a replay of run A and in a slightly mutated run A'; the UI lists both hits.

### [ ] P8.9 Reproducible lab image
- **Depends on:** P1.1, P8.3, P8.2
- **Goal:** `make lab` rebuilds a fresh hardened guest from scratch.
- **Deliverables:** `stealth/image/` Packer + Ansible pipeline: unattended Windows install, driver set, aged profile, game install hook, final snapshot named `clean`; checksum of the resulting QCOW2 recorded in `stealth/image/MANIFEST`.
- **Acceptance:** Two independent builds from the same inputs produce QCOW2 files with the same MANIFEST (deterministic within documented non-determinism — timestamps allow-listed).

---

## Appendix A — Cross-cutting checklists

**Every new detector must ship with:**
1. A `Finding.type` slug added to `docs/findings.md`.
2. An entry in the behaviour vocabulary (P3.2) if it maps to a new behaviour.
3. At least one demo cheat in `demo/cheats/` that triggers it, with an entry in `demo/expected/`.
4. A unit test on recorded fixtures and an integration test under `tests/e2e/` (marked `lab`).
5. A paragraph in the report template explaining what the slug means.

**Every change that touches the run directory layout must:**
1. Update section 2 of this file.
2. Bump the `metadata.json` `schema_version` and add a migration under `src/snare/orchestrator/migrations/`.
3. Keep `snare runs list` compatible with the previous version.

**Every change that could reduce stealth must:**
1. Run the P1.3 checker in the PR and attach the before/after JSON.
2. Not regress the P8.1 matrix without an ADR saying why.

---

## Appendix B — Out of scope (by design)

- Any component that must run inside the guest during an analysis run.
- Automated bypass of real game anti-cheats (EAC, BattlEye, Vanguard, Ricochet…).
- Support for console or mobile cheats (phase 9+ if ever).
- A cheat marketplace, sharing hub, or signature exchange across unrelated organisations. Signature sharing stays per-studio by default.

---

*End of roadmap. Next task to pick: the first `[ ]` with all `Depends on` satisfied. Start at P0.1.*

