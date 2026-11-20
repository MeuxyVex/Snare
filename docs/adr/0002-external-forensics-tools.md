# 0002: Keep memory forensics tools external

- Status: Accepted
- Date: 2026-11-20
- Roadmap: [Technical decisions](../../ROADMAP.md#2-fixed-technical-decisions) · P2.4

## Context

Snare needs process, module and memory findings from guest captures. Volatility 3
and MemProcFS already provide memory forensics capabilities and have their own
release cycles and licensing terms. Bundling or importing their implementations
would tie Snare's package to those dependencies. Implementing the same parsing
in Snare would duplicate work and increase maintenance.

## Decision

Keep Volatility 3 and MemProcFS as separately installed tools. Snare will locate
them using the executable names or paths in `snare.toml`. Integrations will invoke
the tools at a process boundary, using explicit argument lists, and translate
their output into Snare's data models. P2.4 starts with the Volatility 3 wrapper
and records its output in the run directory.

Normal development can use synthetic output fixtures to test adapters without
installing the full analysis toolchain.

## Consequences

The Snare Python package can be installed and tested separately. Lab operators
must install compatible tool versions and configure their executable paths.
Adapters will need to handle missing executables, subprocess failures and changes
in tool output. Integration tests will cover supported tool versions as their
adapters are added.

Tools retain their own distribution terms. Any future package that bundles them
will need a separate review of those terms.
