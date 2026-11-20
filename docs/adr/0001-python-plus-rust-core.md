# 0001: Python application with a Rust performance core

- Status: Accepted
- Date: 2026-11-20
- Roadmap: [Technical decisions](../../ROADMAP.md#2-fixed-technical-decisions) · P5.1

## Context

Snare needs to coordinate virtual machines, work with analysis artifacts and
produce reports. Python has libraries for the CLI, data validation and web
interfaces. Some future analysis operations may process large memory regions
repeatedly, where throughput and allocation costs matter.

An application written entirely in Python would keep installation and testing
simple. An application written entirely in Rust would give the whole stack
native performance but would also move the CLI, configuration and reporting
away from the Python libraries the roadmap already selects.

## Decision

Use Python 3.11 or later for orchestration, CLI, configuration, analysis logic,
reporting, API and MCP. Introduce the Rust crate `snare-core` in P5.1 for
performance-sensitive operations. Expose it to Python through PyO3 and package
the extension with maturin.

Keep a Python reference for operations such as the executable-section comparison
so tests can verify that the Rust implementation produces the same results.

## Consequences

The initial Python package can be developed and tested independently of the Rust
toolchain. When P5.1 adds the native extension, release builds will need to
produce and test platform-specific wheels. The Python wrapper will need to define
how native errors and data cross the language boundary.

P5.1 will verify the Rust executable-section comparison against the Python
reference and measure throughput on a representative fixture.
