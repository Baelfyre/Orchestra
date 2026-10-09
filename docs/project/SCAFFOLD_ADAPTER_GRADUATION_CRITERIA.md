# Scaffold Adapter Graduation Criteria

## Purpose

This document defines what it means for a scaffold-only adapter to graduate into a higher support tier. It exists to keep Orchestra honest about host support, prevent packaging scaffolds from being described as finished integrations, and provide a repeatable review path before documentation or marketplace surfaces claim broader support.

## Current Scaffold-only Adapters

The following hosts currently have runtime adapter contracts and/or packaging scaffolds, but are not yet documented as fully supported host integrations:

- VS Code
- VSCodium
- Cursor
- Windsurf
- JetBrains
- Zed
- Neovim

## Graduation Status Levels

### `scaffold-only`
- Runtime adapter and/or packaging surface exists.
- Host integration is intentionally incomplete.
- Documentation must not imply finished installation, full host validation, or marketplace readiness.

### `experimental`
- Core runtime contract works in a narrow, documented path.
- Installation and execution paths still require manual validation and may change without compatibility guarantees.
- Marketplace claims remain out of scope.

### `functional`
- The adapter works end to end in at least one maintained install path.
- Validation is reproducible and documented.
- Known limitations are still allowed, but they must be explicit.

### `supported`
- The adapter has a maintained install path, clear host instructions, documented compatibility expectations, and repeatable validation.
- Repository documentation may describe the host as supported for the documented path.
- Support claims must stay scoped to what the validation evidence proves.

### `marketplace-ready`
- Packaging, metadata, validation, and release handling are complete enough for host-native marketplace or distribution submission.
- Marketplace documentation, upgrade path, ownership, and release expectations are defined.
- Marketplace-ready does not bypass the requirements for `supported`; it builds on top of them.

## Minimum Graduation Requirements

A scaffold-only adapter must not graduate past `scaffold-only` until all of the following are true:

1. A runtime adapter contract exists and passes PRAP validation.
2. Manifest, package, and adapter metadata match the runtime protocol metadata for the host.
3. Host-specific install and run instructions exist.
4. At least one smoke test or documented manual validation path exists.
5. Documentation does not overclaim support, marketplace availability, or automatic host discovery.
6. The compatibility matrix is updated to reflect the exact support level.
7. README or setup documentation reflects the same support level as the compatibility matrix.

## Validation Requirements

A graduation review should include, at minimum:

- PRAP validation for the runtime adapter contract.
- Packaging and metadata validation for the relevant scaffold or plugin surface.
- One reproducible host validation path.
  - This may be a smoke test, scripted validation, or a documented manual verification path when automation is not yet practical.
- Evidence that documented commands, adapter entrypoints, and compatibility notes match actual behavior.
- Negative confirmation that the repository is not claiming broader support than the validation proves.

## Packaging and Marketplace Readiness Requirements

A host must not be described as `marketplace-ready` unless:

- Host-native packaging files are present and maintained.
- Package metadata, manifest metadata, and runtime protocol metadata are aligned.
- Installation, upgrade, and removal paths are documented.
- Release ownership is clear.
- Submission constraints for the target host are known and reflected in docs.
- The repository does not rely on placeholder marketplace language.

## Documentation Requirements

Before a support-level promotion is documented:

- `docs/setup/COMPATIBILITY.md` must reflect the exact support level.
- Any host-specific setup or install guide must match the validated path.
- README, setup docs, and project docs must avoid stronger claims than the validated path supports.
- If limitations remain, they must be documented where the support claim appears.

## Support and Maintenance Requirements

Before a host is described as `supported` or `marketplace-ready`, the project should define:

- Who owns break/fix response for that host.
- Which validation path is expected to stay green.
- Which compatibility boundaries are intentionally supported.
- What changes in host packaging or runtime behavior should block release claims until revalidated.

## Graduation Review Checklist

Use this checklist for each promotion decision:

- [ ] Target host and desired status level are named explicitly.
- [ ] Runtime adapter contract exists and passes PRAP validation.
- [ ] Manifest/package metadata matches runtime protocol metadata.
- [ ] Host-specific install and run instructions exist.
- [ ] Smoke test or documented manual validation path exists.
- [ ] Compatibility matrix reflects the target status level.
- [ ] README or setup docs reflect the same status level.
- [ ] Marketplace claims are absent unless marketplace readiness is validated.
- [ ] Known limitations are documented.
- [ ] Support ownership and maintenance expectations are defined.

## Recommended Graduation Order

Orchestra should graduate scaffold adapters in this order:

1. VS Code / VSCodium
2. Cursor
3. Windsurf
4. JetBrains
5. Zed
6. Neovim

This order favors the shared VS Code-family packaging surface first, then nearby editor variants, before moving into more host-specific packaging and validation paths.

## Non-goals

This document does not:

- Change runtime behavior.
- Upgrade any adapter by itself.
- Promise marketplace publication dates.
- Replace PRAP, packaging validation, or compatibility documentation.
- Treat a packaging scaffold as evidence of real support without validation.
