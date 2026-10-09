# Portable Adaptive Memory change note

This bounded post-v1.6.0 change introduces a storage-agnostic portable-memory contract for validated adaptive-learning candidates.

- Local A1/A2/A3 behavior remains unchanged by default.
- Portable memory is optional and user-selected.
- Supported adapter classes are generic: LOCAL_JSON, GIT_JSON, HTTP_API, and CUSTOM.
- No external repository, database, service, private backend identity, credential, or local user/session identifier is embedded in Orchestra source.
- Portable candidates remain non-authorizing and require explicit privacy review.
- Automatic promotion, policy activation, routing changes, release, deployment, and destructive operations remain unauthorized.

This note is supplemental documentation. The canonical root CHANGELOG.md remains governed by the repository freshness gate.
