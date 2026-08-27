# UIX-9C V2 Resource Ceiling Proposal

Status: `PROPOSAL_ONLY_HUMAN_SCIENTIFIC_POLICY_REVIEW_REQUIRED`

This proposal resolves the arithmetic conflict between six required valid
observations and one permitted invalid-infrastructure replacement. It does
not alter the active frozen V2 plan or authorize a live call.

## Proposed new-campaign limits

```text
MAX_VALID_EXPERIMENTAL_SESSIONS=6
MAX_EXPERIMENTAL_MODEL_CALLS=7
MAX_EXPERIMENTAL_PROVIDER_CALLS=7
MAX_INVALID_INFRASTRUCTURE_REPLACEMENTS=1
MAX_VALID_OBSERVATIONS_COUNTED=6
MAX_MODEL_CALLS_PER_RUN=1
MAX_NONEXPERIMENTAL_AVAILABILITY_PROBES=0
MAX_TOTAL_PROVIDER_INTERACTIONS=7
TOKEN_OR_COMPUTE_CEILING=MAX_TOTAL_TOKENS_120000_MAX_PER_RUN_20000
PER_RUN_TIMEOUT_SECONDS=900
TOTAL_CAMPAIGN_TIMEOUT_SECONDS=7200
MAX_EXTERNAL_REPO_MUTATIONS=0
```

The seventh experimental model/provider call is permitted only as the single
replacement for one explicitly classified `HOST_CRASH` or frozen provider
outage invalid-infrastructure run. It can never create a seventh valid
observation. A valid unfavorable output is retained and is never retried for
outcome. A resource ceiling is a stop condition and cannot be extended after
an output is observed.

The new-campaign availability-probe limit is zero because the prior
nonexperimental availability probe is historical evidence and no new probe is
needed for this proposal. Historical counters remain separate and unchanged:

```text
HISTORICAL_EXPERIMENTAL_MODEL_CALLS=6
HISTORICAL_EXPERIMENTAL_PROVIDER_CALLS=6
HISTORICAL_NONEXPERIMENTAL_AVAILABILITY_PROBES=1
HISTORICAL_TOTAL_PROVIDER_INTERACTIONS=7
HISTORICAL_INVALID_INFRASTRUCTURE_RETRIES=0
```

New-campaign authorization counters remain zero until a fresh approved
envelope is consumed.

## Required freeze before UIX-9C

Before any live call, the human authorization record must explicitly freeze
the proposed limits, exact execution order
`A1,B1,B2,A2,A3,B3`, arm treatment identities, task/fixture/validator/
guidance/evaluator digests, provider `openai-codex`, model `gpt-5.6-luna`,
`reasoning_effort=xhigh`, and the model revision. The model revision is
currently:

```text
MODEL_REVISION=UNRESOLVED_PENDING_LIVE_AUTHORIZATION
```

No substitution is permitted. The authorization record must also preserve the
retry, outage, invalid-run, evidence-retention, and external-mutation
boundaries from the V2 protocol.

If a human elects to permit a new availability probe, that is a different
proposal and the total provider-interaction ceiling must be explicitly
recomputed and frozen before live execution. It must not be inferred during a
run.

## Current authority

```text
LIVE_MODEL_CALLS_AUTHORIZED=false
PROVIDER_CALLS_AUTHORIZED=false
UIX_9C_EXECUTION_AUTHORIZED=false
MAX_NEW_LIVE_CALLS=0
```

The next gate is a fresh human UIX-9C authorization decision. No experimental
result, benefit claim, harm claim, or directional model-behavior claim is
established by this proposal.
