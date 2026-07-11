# License & Attribution Compliance

Artificer must handle external source code with strict adherence to licensing and intellectual property rules to prevent copyleft contamination or copyright violations in Orchestra.

## License Compatibility Matrix

Only licenses compatible with Orchestra's MIT license may be considered for adaptation or reuse.

| License Type | Permitted Actions | Governor Review Required? |
|---|---|---|
| **MIT** | Concept adaptation, code adaptation, direct reuse | No, standard attribution applies. |
| **BSD (2/3-Clause)** | Concept adaptation, code adaptation, direct reuse | Yes, to verify notice retention. |
| **Apache 2.0** | Concept adaptation, code adaptation, direct reuse | Yes, to verify patent clause implications. |
| **GPL (v2/v3)** | Concept adaptation only (no code copying) | Yes, high risk of copyleft contamination. |
| **AGPL / LGPL** | Concept adaptation only | Yes. LGPL code reuse is blocked. |
| **Proprietary** | None (reference only) | Yes, strict blocks on direct reuse. |

## Attribution Requirements

If any code is classified as `ADAPTED_PATTERN` or `CODE_REUSE_REVIEW_REQUIRED`:

1. **Attribution Header**: Keep original copyright notices intact.
2. **File Preamble**: Include a header comment linking to the original source:
   ```python
   # Derived/adapted from: [Canonical URL]
   # Commit SHA: [Reviewed Commit SHA]
   # Original License: [License Type]
   # Copyright (c) [Year] [Original Author]
   ```
3. **Credit File**: Update any repository-level credit or third-party notice files if applicable.

## Governor Escalation Path

Escalate to **The Governor** immediately if:
- A dependency or pattern uses a dual license or custom license.
- Discovered code lacks any license file or header.
- A proposed pattern requires copying more than 50 lines of code.
- License compatibility is uncertain.
