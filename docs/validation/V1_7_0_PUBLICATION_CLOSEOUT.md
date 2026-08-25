# Orchestra v1.7.0 Publication Closeout

Status: `PUBLISHED_VERIFIED_COMPLETE`

## Canonical release identity

- Tag / release: `v1.7.0`
- GitHub Release id: `376713145`
- Canonical release commit: `e5305ef3e160209a0345bd2c7843c923940e62c5`
- Canonical tree: `7b7a0f6d5dd5376a62125ed1c6b037284e519c69`
- Sole parent: `664079b5fb9e149ea0689ff08bc2d9c039780290`
- Canonical commit signature: GitHub verified / valid
- Tag type: lightweight `commit` ref
- Draft: `false`
- Prerelease: `false`
- Immutable: `true`
- Latest release at closeout: `true`

## Canonical exact-head validation

- Governance Check `32897630179`: PASS
- validate/runtime `32897630178`: PASS
- Required Analysis Compatibility / CodeQL `32897630143`: PASS
- Cross-platform Validation `32897630175`: PASS on Windows, Ubuntu, and macOS
- Cosmic Ray confidence `32897630172`: PASS
- Unresolved review threads: `0`
- Expected-head Squash: PASS

## Signed materialization

- Signed materialized candidate: `da4a78e04e4989b83b14dec18280ac662b3c44c4`
- Signed-materialization run: `32897500629`: PASS
- Artifact digest: `sha256:315014b4adadafe11f8e2b54eca574186d87e7a15024a7b84e5d45e9d55c1699`
- Reviewed tree = signed materialized tree = canonical release tree: exact

## Post-publication verification

The first authorized publication workflow created the immutable release and then failed during its own post-create body-byte verification step. The release was not rolled back or republished. A bounded read-only verification correction then completed successfully:

- Verification run `32898750932`: PASS
- `v1.7.0` tag target: exact canonical release commit
- immutable release identity: PASS
- exact release body: PASS
- latest-release identity: PASS
- previous `v1.6.0` tag preserved at `ba35764a14111518c7da729b5a4c69c6af485a9b`: PASS

## Release boundaries

v1.7.0 does not authorize live UIX-9 provider/model proof, deployment, production mutation, policy activation, installed-integration refresh, scaffold-host promotion, destructive cleanup, force push, or history rewrite. A5 topology and Murmurs benefit were not established and were not promoted to default execution authority.

Release tracking issue #563 is closed completed. The immutable published release remains authoritative for v1.7.0 even when `main` receives later post-release maintenance.
