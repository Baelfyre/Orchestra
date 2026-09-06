# UAI Portable Projection Compiler

The canonical portable projection contract is [portable-projection-contract.v1.json](../../machine/projections/portable-projection-contract.v1.json). It names the Orchestra governance, routing, specialist, host-capability, and integration-strategy sources that may be represented by a host projection.

The compiler validates those source paths and required routing invariants in the tracked projection surfaces, then writes the deterministic parity index at [portable-projection-index.v1.json](../../machine/projections/portable-projection-index.v1.json). The current projections cover the GitHub Copilot repository-instruction template, repository instruction anchor, and custom-agent template.

Run:

```text
python scripts/compile_portable_projections.py --write
python scripts/compile_portable_projections.py --check
```

The index records normalized SHA-256 fingerprints for canonical sources and projection outputs. Missing markers, missing sources, stale generated output, unsupported formats, repository escapes, and `.agents` runtime-copy targets fail closed.

Projection parity does not create execution, routing, specialist-selection, workflow-topology, provider-selection, governance, installation-refresh, automatic-fallback, or learned-routing authority. Host transport selection remains separate from Conductor routing and deterministic AWF workflow topology.
