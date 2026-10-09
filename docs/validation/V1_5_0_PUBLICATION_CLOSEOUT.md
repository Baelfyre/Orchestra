# v1.5.0 Publication Closeout

## Status

`PUBLISHED_VERIFIED`

Orchestra `v1.5.0: Machine-Verifiable Control Plane and Murmurs` is published and independently verified from the exact signed canonical release boundary below.

```text
repository=Baelfyre/Orchestra
release=v1.5.0
release_id=371314544
release_commit=b0a56cc7af8ad78234754bcb29ed07f6ab54d920
release_tree=4045bde297951b6cafa107ea39c227555e13bd02
release_commit_signature=VERIFIED_VALID
tag=v1.5.0
tag_kind=LIGHTWEIGHT_COMMIT_REF
tag_target=b0a56cc7af8ad78234754bcb29ed07f6ab54d920
release_immutable=true
release_latest=true
publication_workflow_run=31946111993
publication_workflow_result=PASS
```

The GitHub Release is non-draft, non-prerelease, immutable, and bound to lightweight tag `v1.5.0`, which resolves directly to the exact release commit. The fixed release tag is not moved by this post-publication documentation closeout.

## Release Validation Boundary

The published release campaign recorded:

```text
runtime_tests=1058
statement_coverage_percent=98.47
branch_coverage_percent=95.36
critical_module_floors=PASS
governance=PASS
codeql=PASS
native_platforms=PASS
mutmut=COMPLETE
cosmic_ray=COMPLETE
control_plane_stage=LEGACY_RETIRED
```

These measurements are revision-bound release evidence. They do not create authority and must not be reused to authorize a later source head without fresh validation.

## Compliance Registry Boundary

The release remains aligned to the separately governed Compliance Registry publication:

```text
registry_repository=Baelfyre/Orchestra-Compliance-Registry
registry_canonical_main=b1f181cef862f9dcb4df225e90f69ac970f708c3
trusted_registry_release=registry-v0.1.0
trusted_registry_release_target=3821bcb55125b4d8864f28b6423650e6e17ac67b
compatibility=V0_1_COMPATIBLE
```

Registry evidence remains reusable governance input rather than execution, release, deployment, policy, or legal authority.

## Publication Scope

v1.5.0 publishes the machine-verifiable control-plane re-foundation through `LEGACY_RETIRED`, the fail-closed ordinary merge-readiness stabilization, and the additive Murmurs communication budget with `NORMAL` as the default presentation mode.

MCP is not part of v1.5.0. Publication satisfies the previously required sequencing prerequisite only. Any MCP transport or integration work remains subject to a fresh post-release dependency, risk, value, authority, and design review and must not become a source of Orchestra authority.

## Post-Publication Documentation Closeout

This record accompanies the current-facing documentation parity update for:

- `README.md`
- `README.json`
- `CHANGELOG.md`
- `PROJECT_STATE.md`
- `PROJECT_CONTEXT.md`
- `SESSION_HANDOFF.md`
- `docs/project/ROADMAP.md`
- `docs/setup/INSTALLATION.md`
- `docs/setup/COMPATIBILITY.md`

The closeout must pass the repository's current protected pull-request validation at its exact documentation head before it may become canonical. Historical release evidence remains historical and is not rewritten.

## Protected Actions Not Performed

This post-publication closeout does not perform:

- marketplace or package publication;
- installed-integration refresh;
- deployment or production mutation;
- policy activation;
- force push or history rewrite;
- branch deletion;
- destructive cleanup;
- release-tag movement; or
- MCP implementation.

## Continuation

After this documentation closeout is merged and independently verified, master issue #273 may be assessed against its documented exit criteria. Any later implementation lane requires fresh live-state and dependency/risk/value selection; v1.5.0 publication does not automatically authorize the next feature phase.
