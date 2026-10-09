# Codex C2 Machine-JSON Execution Freeze

## Status

`HISTORICAL_SUPERSEDED_PRE_EXECUTION_BY_C2_PORTABILITY_R1`

> **Portability supersession:** No C2 live model call was made under the original external execution package. The package is unavailable on the current host, and deterministic recovery reproduced 0/5 original prompt digests. The original hashes below remain historical provenance only. Current pre-execution authority is recorded in `docs/benchmarking/CODEX_C2_PORTABILITY_R1_PREEXECUTION.md` and `machine/benchmarking/codex-c2-portability-r1-preexecution.v1.json`; live execution remains locked pending a separate authorization record.

C2 is the second Codex phase in Orchestra's shared comparative benchmark. It changes only the task-prompt representation from the completed C1 natural-language form to deterministic canonical JSON.

C1 evidence is frozen and must not be rewritten, reclassified, or used as a mutable input to C2.

## Research question

Does a deterministic machine-readable JSON representation change exact-response conformance, provider-native token use, reasoning/output behavior, or communication-treatment interaction relative to the frozen natural-language C1 baseline?

C2 does not assume machine-readable prompting is better. It is an empirical representation experiment.

## Frozen identity

| Field | C2 value |
|---|---|
| Program | `orchestra.shared-comparative-benchmark.v1` |
| Experiment | `b3-codex-machine-json-prompt-extension-v1` |
| Current canonical Orchestra main at freeze | `dc119739ef871d77ee91ade4e0d2d9032c804970` |
| Current canonical tree | `6e734f3bf64e23a58bb4066d75a6f59ab93392aa` |
| Executable adapter revision | `0af078f6ad34d5cf406823bbd0e8258496923b60` |
| Executable adapter tree | `90255564c13fcbb132a7e4cf8b98eb106d039e39` |
| Frozen benchmark subject | `d95f677dbf23ab79c4698c26645ea30cea9b3019` |
| Benchmark subject tree | `ceab55bd512ea6fde4e8e76877cbb7006d18500e` |
| Task-set digest | `fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8` |
| Validator | `EXACT_JSON_CONFORMANCE_V1` |
| Codex CLI | `0.148.0` |
| Provider | `openai-codex` |
| Model | `gpt-5.6-sol` |
| Reasoning effort | `medium` |
| Counter | `codex-cli-0.148.0:jsonl-usage:gpt-5.6-sol:medium` |
| Execution autonomy | `CONTROLLED_READ_ONLY` |
| Planned accepted runs | 30 |

The current canonical `main` changed documentation after C1 but retains the exact C1 benchmark-source blobs. C2 therefore reuses the same executable adapter revision rather than silently moving the measured implementation.

Verified blob equivalence at the C2 freeze boundary:

- task set: `b0f4fd6c2ad14d5a38db61851303e58d80577ccf`
- plan fixture: `2448efecf3fc8742bbc516141ac79d2bd2d19a87`
- planner: `6de55d48fd2e37f8106ff64eecb522cde30b7a58`
- Codex executor: `0b5267234d881027224cbb26b400e19e8fe3bf74`

## Prompt representation

C2 uses schema `orchestra.prompt-representation.machine-json.v1`.

Each prompt contains only `schema_version`, `task_id`, `task_class`, deterministic `operation`, frozen `starting_state`, the existing `validation_contract` as `response_contract`, and explicit no-authority-expansion / one-JSON-object constraints.

Canonical serialization is `sort_keys=true,separators=(comma,colon),ensure_ascii=true`.

The C1 natural-language prompt is **not embedded as a JSON string**. The representation is reconstructed from the same structured task semantics and expected-response contract.

## Exact pairing policy

C2 preserves the C1 task, repetition, communication arm, and execution-slot assignment exactly. The only intended experimental factor is task-prompt representation.

C2 request IDs are new because request identity is bound to the C2 experiment ID.

No new arm randomization is performed for C2. This maximizes slot-level pairing to C1, but introduces a documented limitation: C1 occurred before C2, so representation order is not temporally randomized and provider/session drift cannot be fully excluded.

## Resource freeze

C2 intentionally reuses the C1 ceilings unchanged:

| Limit | Frozen value |
|---|---:|
| Per-call total-token ceiling | 45,000 |
| Cumulative accepted-token ceiling | 1,200,000 |
| Automatic retry | OFF |
| Stop on invalid run | ON |
| Stop on provider/model/counter drift | ON |
| Stop on tool event | ON |
| Stop on token-ceiling breach | ON |

Using the same ceilings avoids introducing a different resource envelope into the representation comparison.

A provider or infrastructure failure is preserved as an invalid attempt. Automatic retry is forbidden. Any recovery requires separate adjudication; C2 evidence must never silently replace or delete a failed attempt.

## Execution boundary

C2 remains read-only and self-contained:

- isolated empty Git workspace
- no `AGENTS.md`
- repository mutation prohibited
- no task-required network access
- canonical Codex executor continues to reject disallowed tool events
- Caveman remains pinned to revision `ae405e872270acc57484693612ae038b16c8f6cd`
- Caveman `skills/caveman/SKILL.md` remains pinned to blob `bd22d86b32e4a99e09ff7482a35509faac7a6f65`

## Interpretation limits

C2 remains calibration/research evidence. It does not authorize a claim that machine JSON is intrinsically superior, production routing changes, A5 execution promotion, A6, B4, a release or deployment, or changes to C1 or accepted Antigravity evidence.

C2 results must be analyzed against C1 using within-provider paired representation effects. Any causal explanation for an observed difference requires additional evidence.

## Historical original execution freeze

The original machine-readable execution freeze was an external benchmark artifact. Because that package is unavailable and its prompt identity could not be recovered exactly, the hashes below are preserved as historical provenance only and do not authorize C2R1 execution. Current pre-execution authority is the C2R1 reconciliation record linked above.

Full freeze envelope SHA-256: `0285f97f0f509ddd41bebfe7254aec82d9292f6ae0097cf05776923c8f5bcc7b`.

Validated local launcher SHA-256: `b20010df254a329696441565c2827df5d4c880b198f192da3d2c51662573c142`.

Execution bundle SHA-256: `d2d4fcbc67cea1b8f7b898105e39cf0cc6cd47823dfd104d6b6162eba66a874d`.

The final C2 result publication will add the normal human-readable analysis plus canonical machine-readable result/index record after the evidence is reconciled.
