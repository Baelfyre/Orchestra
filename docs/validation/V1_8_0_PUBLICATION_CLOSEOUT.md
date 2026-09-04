# Orchestra v1.8.0 Publication Closeout

Status: `PUBLISHED_VERIFIED_COMPLETE`

## Canonical release identity

- Tag / release: `v1.8.0`
- GitHub Release id: `RE_kwDOS_4UtM4WyusI`
- Canonical release commit: `dad1f153f1be6522a8a7964258a2122a8d057596`
- Canonical release tree: `4effcd97e15f843c8c0d9d45217870ee9d6480ff`
- Sole parent: `b601c2d853ad0dcdc68b8dc652578f19ef663c79`
- Canonical commit signature: GitHub verified / valid (RSA key B5690EEEBB952194)
- Tag type: lightweight `commit` ref
- Draft: `false`
- Prerelease: `false`
- Immutable: `true`
- Latest release at closeout: `true`

## Canonical exact-head validation

- Source Qualification PR: #770 (`release/v1.8.0-governance-runtime-traceability-20260904`)
  - Governance Check `33818301776`: PASS
  - validate / runtime `33818301771`: PASS
  - Required Analysis Compatibility / CodeQL `33818301794` / `33818355067`: PASS
  - Cross-platform Validation `33818301751`: PASS on Windows, Ubuntu, and macOS
  - bounded-pilot `33818301782`: PASS
  - Unresolved review threads: `0`
- Canonical Integration PR: #772 (`materialize/v1.8.0-release-20260904`)
  - Governance Check `33819113908`: PASS
  - validate / runtime `33819113935`: PASS
  - Required Analysis Compatibility / CodeQL `33819113974` / `33819112138`: PASS
  - Cross-platform Validation `33819114267`: PASS on Windows, Ubuntu, and macOS
  - bounded-pilot `33819113940`: PASS
  - Unresolved review threads: `0`
  - Expected-head Squash: PASS

## Signed materialization

- Signed materialized candidate: `0ccde647ae41e078b7ec7c3453fc67d7f7703f31`
- Signed-materialization PR: #771: PASS
- Reviewed tree = signed materialized tree = canonical release tree: `4effcd97e15f843c8c0d9d45217870ee9d6480ff` (exact match)

## Post-publication verification

- Lightweight tag `v1.8.0` target: exact canonical release commit `dad1f153f1be6522a8a7964258a2122a8d057596`
- Immutable release identity: `true`
- Exact release body match: verified identical to `docs/releases/v1.8.0-governance-hardening-runtime-refoundation-traceability-release-candidate.md`
- Latest release identity: `true` (`v1.8.0`)
- Previous release preservation: `v1.7.0` preserved at `e5305ef3e160209a0345bd2c7843c923940e62c5`, `v1.6.0` preserved at `ba35764a14111518c7da729b5a4c69c6af485a9b`

## Release boundaries

v1.8.0 does not authorize AR-3 or AR-4 implementation, runtime redesign, new OR-GOV phases, provider promotion, policy activation, deployment, production mutation, marketplace publication beyond repository distribution, scaffold-host promotion, destructive testing, force push, or history rewrite. The MigrationRiskContract unknown-production gap remains explicitly documented.

The published release remains authoritative for v1.8.0 even as `main` receives later post-release maintenance.
