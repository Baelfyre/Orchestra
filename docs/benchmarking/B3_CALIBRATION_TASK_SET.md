# B3 Calibration Task Set - Padayon-Grounded Calibration & Deterministic Outcome Validation

## Status

```text
Task-Set Version: orchestra.b3-calibration-task-set.v1
Status: PADAYON_GROUNDED_V1_FROZEN
Program ID: orchestra.shared-comparative-benchmark.v1
Task Count: 5
Repetitions per Arm: 2
Communication Arms: DEFAULT, CAVEMAN, MURMURS
Planned Runs: 30 (5 tasks x 2 repetitions x 3 arms)
Paired Blocks: 10
Synthetic / Self-Contained: true
Network Required: false
Repository Mutation: false
Execution Allowed in Plan-Only: false
Validator Type: EXACT_JSON_CONFORMANCE_V1
Validation Semantics: DETERMINISTIC_RESPONSE_DERIVED_NOT_MODEL_SELF_ASSERTED
Aggregate Task-Set Digest: fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8
Live Calibration Calls in Unit: 0 (NOT AUTHORIZED)
```

## Provenance & Baseline

### Padayon Source Snapshot
- **Repository**: `Baelfyre/Padayon`
- **Canonical main SHA**: `03d1ffd4d1dea512230da5628741ae919d70e7ef`
- **Canonical Tree**: `733cb7ebb50d726b33896e8dd7e6a70030d68b79`
- **Recorded At**: `2026-08-20T02:11:00+08:00`
- **Primary Sequencing Sources**:
  - `implementation-phase-prompts/orchestra/CURRENT_PROGRESS.json`
  - `implementation-phase-prompts/orchestra/CURRENT_PROGRESS.md`
- **Supplemental Assurance Source**:
  - `Padayon issue #115: Assurance: prevent canonical identity and compliance-consumption drift`

### Controlled Orchestra Benchmark Subject
- **Repository**: `Baelfyre/Orchestra`
- **Frozen Benchmark SHA**: `d95f677dbf23ab79c4698c26645ea30cea9b3019`
- **Frozen Benchmark Tree**: `ceab55bd512ea6fde4e8e76877cbb7006d18500e`
- **Reason**: Exact controlled Orchestra revision used by accepted B3.2 Attempt 4 and required for later apples-to-apples Codex comparison.

### Implementation Baseline for Task-Set Update
- **Repository**: `Baelfyre/Orchestra`
- **Implementation SHA**: `b050602a042165fb98c3a37f2bf0febb296b3972`
- **Implementation Tree**: `8c08ffce898e73f7e4664a84d18ed1d2791698a8`

## Task-Set Specification

### Task 1: `b3-cal-padayon-r5-capability-manifest`

- **Task Class**: `SINGLE_DOMAIN`
- **Padayon Alignment**: `R5_CAPABILITY_MANIFEST`
- **Purpose**: Validate concise structured reasoning over one bounded machine capability contract.
- **Starting State Digest**: `4f574c6b4150d6a00f25534fcff9089f7245fb1969557db441f09481a0e07160`
- **Task Prompt Digest**: `aef3872f6ee106ece139545d0afba67f41e5244b9201f66cf2763614ed3f6772`
- **Task Payload Digest**: `04c4de55d313f056f190f15514340e5c445c83d7901af04a5ff46872ffe1d7eb`
- **Validation Contract Digest**: `1f2f21f168285e5db15e8db84060787661ff09dcc8802f92832f0d2d874670bf`
- **Expected Response Digest**: `74eb9217d0e2db023a3e21ef97f307d31051a0e59d1fac4a5ae7440a5e3d5c28`

#### Deterministic Expected Response
```json
{
  "authority_expansion": false,
  "disposition": "COMPATIBLE",
  "matched_required_capabilities": [
    "cap.dynamic_source_monitor.v1",
    "cap.query_scoped_freshness.v1",
    "cap.schema.negotiation.v1"
  ],
  "missing_optional_capabilities": [
    "cap.audit_streaming.v1"
  ],
  "missing_required_capabilities": [],
  "negotiated_schema_version": "0.2.0",
  "task_id": "b3-cal-padayon-r5-capability-manifest"
}
```

### Task 2: `b3-cal-padayon-o1-o2-compatibility`

- **Task Class**: `DEPENDENCY_HEAVY`
- **Padayon Alignment**: `R6_RELEASE_DELTA`, `O1_REGISTRY_CAPABILITY_NEGOTIATION`, `O2_REGISTRY_V0_2_COMPATIBILITY`
- **Purpose**: Exercise cross-version dependency negotiation without external network or repository mutation.
- **Starting State Digest**: `3af707cddc212e07249fb6eccdb5f3ae7ad6fedf0ff4158c267e4fbbe4844d9f`
- **Task Prompt Digest**: `ae437de88760c0613127f7369562ccbe28efad3ac35d38ad7dc0566d3db18f7a`
- **Task Payload Digest**: `43013eedfe19f4127ae61a79ef4f1f9e4dcdf1162367d14e5230d9b8b2e5f847`
- **Validation Contract Digest**: `93055d657d151d8e7e6969cdaa26ec8ba9be4dc2c59f426cd9dd63616cf4f0e1`
- **Expected Response Digest**: `405ac6c8c0598437d31a46cddf08b098de543bfcfac53b71cf63afb0a4ec4258`

#### Deterministic Expected Response
```json
{
  "authority_expansion": false,
  "deprecated_in_use": [],
  "disposition": "COMPATIBLE_WITH_SCOPED_REVALIDATION",
  "revalidation_actions": [
    "receipt_parser",
    "registry_client_compatibility"
  ],
  "selected_surface": "0.2.0",
  "supported_required_features": [
    "query.basic.v1",
    "query.multi_jurisdiction.v1"
  ],
  "task_id": "b3-cal-padayon-o1-o2-compatibility",
  "unsupported_requirements": []
}
```

### Task 3: `b3-cal-padayon-o3-o4-freshness`

- **Task Class**: `VALIDATION_HEAVY`
- **Padayon Alignment**: `O3_MULTI_JURISDICTION_QUERY_SUPPORT`, `O4_QUERY_SCOPED_FRESHNESS`
- **Purpose**: Exercise exact set preservation and scoped freshness decisions.
- **Starting State Digest**: `41856aef66a8cb9b11995751ccfd67e84ae16bcb9431a6e1f1d01fd7749406bb`
- **Task Prompt Digest**: `6cc9ff7e6bcaa4d8ee74026d549813f3efd2f1c77f184aae829674e3e5877fd8`
- **Task Payload Digest**: `8895ad53b389c301819520af34f815c7ade24978681382af447bcd7b53db45e2`
- **Validation Contract Digest**: `fc2ea317496b073c7bec304960a7c130b58d8a7114379b0c7c0d17ff4982b32d`
- **Expected Response Digest**: `fd37e402df62b9608155bf8f1782cb3b16e9a6ce636d92b60ef2ce68caaf5158`

#### Deterministic Expected Response
```json
{
  "authority_expansion": false,
  "fresh_source_ids": [
    "src-apac-sg-01",
    "src-us-fed-01"
  ],
  "preserved_obligation_ids": [
    "obl-01",
    "obl-02",
    "obl-04"
  ],
  "query_receipt_disposition": "PARTIAL_STALE_REQUIRES_SCOPED_REFRESH",
  "revalidation_scope": [
    "src-eu-gdpr-01"
  ],
  "stale_source_ids": [
    "src-eu-gdpr-01"
  ],
  "task_id": "b3-cal-padayon-o3-o4-freshness"
}
```

### Task 4: `b3-cal-padayon-assurance-drift`

- **Task Class**: `DEBUGGING`
- **Padayon Alignment**: `PADAYON_ISSUE_115_CANONICAL_IDENTITY_AND_COMPLIANCE_CONSUMPTION_DRIFT`
- **Purpose**: Exercise deterministic diagnosis of identity and evidence-consumption drift.
- **Starting State Digest**: `8e7fcc7681eed61dca0a5d9dd68aa554146eb2eb4376609408e8df2dd77438c0`
- **Task Prompt Digest**: `4ed1e8ae833c0c6db22ee2711a4b6897af748bac459e54e005f8b3204fa617cc`
- **Task Payload Digest**: `384890c16d7f073a13230202ad5b437336e7f9e69e363a55ffbf99df0d65d6cb`
- **Validation Contract Digest**: `51e1c685014b10f4ac340760ec924383938ad45014018454df0189b886431a96`
- **Expected Response Digest**: `e8e1a40e156d4636a1ec5e2508b19ca3bdf85301c31c384cd360abf999c86ca1`

#### Deterministic Expected Response
```json
{
  "authority_expansion": false,
  "defect_classifications": [
    "CANONICAL_IDENTITY_DRIFT",
    "COMPLIANCE_CONSUMPTION_DRIFT"
  ],
  "expected_canonical_sha": "9a1248483a3a115c12d2bb3532102e9685cd9851",
  "historical_evidence_disposition": "PRESERVE_AS_HISTORICAL_EVIDENCE",
  "identity_mismatch_detected": true,
  "missing_consumed_obligations": [
    "GOV-002",
    "PRIV-020"
  ],
  "observed_canonical_sha": "8f31b20a442165fb98c3a37f2bf0febb296b1111",
  "remediation_actions": [
    "ALIGN_CANONICAL_SHA_POINTER",
    "RECONCILE_CONSUMED_OBLIGATIONS"
  ],
  "task_id": "b3-cal-padayon-assurance-drift"
}
```

### Task 5: `b3-cal-padayon-o5-o6-routing`

- **Task Class**: `HIGH_COORDINATION`
- **Padayon Alignment**: `O5_RELEASE_DELTA_IMPACT_ANALYSIS`, `O6_DYNAMIC_DOMAIN_TO_SPECIALIST_RESOLUTION`, `JOINT_REGISTRY_ORCHESTRA_VALIDATION`
- **Purpose**: Exercise multi-specialist routing and validation sequencing while preserving authority boundaries.
- **Starting State Digest**: `00336a2691d1997db5f66a0a28e1ebd9c723880153718905fe095ef10c672463`
- **Task Prompt Digest**: `9c05bf1506ba0fba8fe8a7fa9bee2461415182e8e7490dddf7304679143b89db`
- **Task Payload Digest**: `864d80a80c69e6a41b029955752e706d6e05f7a8a91871144c3d1e03c4d93de7`
- **Validation Contract Digest**: `a67ffceaa82962b21c0c72199c13316b0557d290002c8181209498c34089d654`
- **Expected Response Digest**: `ad08c83a6e7a8f8cc70edd5169779a6f1ba181ca43174ece4659438ac34f0bfe`

#### Deterministic Expected Response
```json
{
  "affected_specialists": [
    "chronicler",
    "clockwork",
    "the-governor"
  ],
  "authority_expansion": false,
  "governance_disposition": "HUMAN_GATE_PRESERVED_NO_AUTHORITY_EXPANSION",
  "impacted_domains": [
    "compliance_policy",
    "data_persistence",
    "runtime_telemetry"
  ],
  "ordered_validation_steps": [
    "the-governor:policy_alignment",
    "chronicler:schema_verification",
    "clockwork:telemetry_contract"
  ],
  "task_id": "b3-cal-padayon-o5-o6-routing"
}
```


## Deterministic Validation Architecture (EXACT_JSON_CONFORMANCE_V1)

Attempt 4 proved instrumentation but highlighted that host `SUCCESS` status does not provide task-completion, validation, or governance evidence.

To prevent manufacturing success:
1. Pre-seeding `task_completed=true`, `validation_passed=true`, or `governance_valid=true` in task payloads is strictly prohibited.
2. Model self-reported pass/validation booleans are never trusted.
3. Every task response is parsed as exactly one JSON object without Markdown fences.
4. Response-derived evaluations:
   - `task_completed = true` only when the response JSON is parseable, represents a dictionary, and contains all required keys.
   - `validation_passed = true` only when all fixture-defined values, sorted lists, and dispositions match the contract.
   - `governance_valid = true` only when the response stays within fixture-allowed actions and contains no authority expansion (`authority_expansion: false`), capability expansion, or gate suppression.
   - Overall task `status = PASS` only when `task_completed and validation_passed and governance_valid`.

## Experimental Invariants

1. **Synthetic & Self-Contained**: No task requires internet access, external databases, or live Registry instances.
2. **Non-Mutating**: No task modifies any repository file, branch, or index.
3. **Identical Prompt Across Arms**: For any given task, `task_prompt` and `task_prompt_digest` are identical across `DEFAULT`, `CAVEMAN`, and `MURMURS` arms.
4. **Fixed Deterministic Topology**: All arms share the identical topology class (`FIXED_DETERMINISTIC`) and digest.
5. **Zero Live Provider Calls**: This task-set recalibration unit executes zero live model/provider calls.
6. **Future Codex Apples-to-Apples Reuse Rule**: When comparing Antigravity against Codex, Codex will run against the exact same task-set digest (`fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8`) and the exact frozen benchmark subject (`d95f677dbf23ab79c4698c26645ea30cea9b3019`).

## Governance Authority Boundaries

```text
B3_CALIBRATION_TASKSET = PADAYON_GROUNDED_V1_FROZEN
B3_CALIBRATION_TASKS = 5
B3_CALIBRATION_PLANNED_RUNS = 30
B3_CALIBRATION_VALIDATOR = DETERMINISTIC_RESPONSE_DERIVED_READY
B3_CALIBRATION_PLAN_ONLY = READY
B3_CALIBRATION_LIVE_EXECUTION = NOT_AUTHORIZED
B3_CALIBRATION_LIVE_RESOURCE_BUDGET = NOT_YET_FROZEN
B3_MEASUREMENT_MATURITY = MEASUREMENT_NOT_STARTED
MURMURS_BENEFIT = NOT_ESTABLISHED
MURMURS_TOKEN_SAVINGS = NOT_CLAIMED
A5_EXECUTION_PROMOTION = NOT_AUTHORIZED
A6 = NOT_AUTHORIZED
B4 = BLOCKED
LIVE_PROVIDER_CALLS_IN_UNIT = 0
```
