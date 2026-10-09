# License & Attribution Compliance

Artificer must handle external source code with strict adherence to licensing and intellectual property rules to prevent copyleft contamination or copyright violations in Orchestra.

## 1. Intake Licensing Evaluation

Every intake audit must evaluate the target repository's licensing state using the following rules:

### Detected License
- Check the root `LICENSE`, `COPYING`, or `README` files to discover the declared license.
- Categorize according to the **License Compatibility Matrix** below.

### Missing or Ambiguous License
- If no license is declared, or if the repository contains mixed/conflicting licensing terms:
  - Treat the source as **UNLICENSED (Proprietary)** by default.
  - Limit intake to **REFERENCE_ONLY** (concept-only).
  - Mandatory Governor escalation is required.

> [!NOTE]
> In Phase 4, Governor escalation is formally recorded via the `GOVERNANCE_DECISION_SCHEMA.json` contract.

---

## 2. License Compatibility Matrix

Only licenses compatible with Orchestra's MIT license may be considered for code adaptation or reuse.

| License Type | Permitted Actions | Governor Review Required? | Copyleft Implications |
|---|---|---|---|
| **MIT** | Concept adaptation, code adaptation, direct reuse | No, standard attribution. | None. Compatible with MIT. |
| **BSD (2/3-Clause)** | Concept adaptation, code adaptation, direct reuse | Yes, verify copyright notices. | None. Compatible with MIT. |
| **Apache 2.0** | Concept adaptation, code adaptation, direct reuse | Yes, check patent clauses. | Weak copyleft. Compatible with MIT. |
| **GPL (v2/v3)** | Concept-only adaptation | Yes, direct code reuse blocked. | Strong copyleft. Incompatible. |
| **AGPL / LGPL** | Concept-only adaptation | Yes, direct code reuse blocked. | Network/Library copyleft. Incompatible. |
| **Proprietary / Unlicensed** | Concept-only adaptation (reference-only) | Yes, direct code reuse blocked. | Strong proprietary rights. Incompatible. |

---

## 3. Scope of Adaptation

### Concept-Only Adaptation
- Extract only architectural ideas, design patterns, or interface flows.
- Write the implementation completely from scratch without using any source expressions.

### Copied or Derived Code
- Any direct copying or adaptation of actual code lines:
  - Restricted to compatible licenses (MIT/BSD).
  - Triggers **Attribution Requirements**.
  - Must be reviewed and approved by The Governor via a documented Governance Decision.

### Dependency Integration
- If the pattern suggests adding an external package/library as a new dependency:
  - Check the package's dependencies (transitive deps) for copyleft licenses.
  - Add to the project's dependency manifest only after Governor clearance.

---

## 4. Asset & Dataset Provenance
- If the repository includes assets (images, fonts, icons) or datasets (test fixtures, mock data):
  - Do NOT copy them without verifying their individual license terms (Creative Commons, SIL, etc.).
  - Document their provenance in the Phase 4 `AUDIT_REPORT_SCHEMA.json` Source Audit.

---

## 5. Attribution Requirements

For any adapted or reused code:

1. **Attribution Header**: Keep original copyright notices intact.
2. **File Preamble**: Include a header comment linking to the original source:
   ```python
   # Derived/adapted from: [Canonical URL]
   # Commit SHA: [Reviewed Commit SHA]
   # Original License: [License Type]
   # Copyright (c) [Year] [Original Author]
   ```
3. **Credit File**: Update any repository-level credit or third-party notice files if applicable.

---

## 6. Mandatory Governor Escalation Path

The auditor must escalate to **The Governor** immediately if:
- The target repository lacks a clear license or has ambiguous terms.
- A proposed pattern involves copying or adapting code from copyleft licenses (GPL/AGPL/LGPL).
- Discovered code contains no license headers but resides in a public repository.
- A new third-party dependency is recommended.
- The size of copied/derived code exceeds 50 lines.
- Any patent or trademark notices are present in the target repository.
