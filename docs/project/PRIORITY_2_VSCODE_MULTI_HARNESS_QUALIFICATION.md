# Priority 2 VS Code Multi-Harness Provider Qualification

Status: `P2_2B_IMPLEMENTATION_CANDIDATE`

Unit: `P2.2B_VSCODE_MULTI_HARNESS_PROVIDER_QUALIFICATION`

Canonical implementation baseline at admission:

```text
ORCHESTRA_MAIN = 5f8ae790c2e105c3356cb7bb9c8aa00c1e26e418
ORCHESTRA_TREE = c1e7c7f68f213f00347e1b4ed7683601546cd30a
P2_2A = COMPLETE_CANONICAL_VERIFIED
PUBLIC_RELEASE = v1.7.0
```

## Purpose

Use VS Code as a controlled multi-harness observation environment for current provider/model paths without treating the editor, harness, provider, model, or successful response as Orchestra authority.

The unit exists because standalone provider-native tooling may not be available or authenticated on every development machine, while current VS Code supports multiple harnesses and multiple provider/model paths through one session experience.

This unit records and validates evidence. It does not automatically control VS Code, select a model, start an agent, install an extension, mutate credentials, or route production specialist execution.

## Current VS Code architecture used by this unit

Current Microsoft documentation separates:

```text
AGENT_HARNESS
EXECUTION_ENVIRONMENT
AGENT_ROLE
LANGUAGE_MODEL
```

VS Code currently documents Local, Copilot, Claude, Codex, and Cloud session targets. Local, Copilot, Claude, and Codex represent distinct local harness paths. The harness determines provider-specific capabilities and tools, while the language model is a separate session choice.

Relevant upstream documentation:

- https://code.visualstudio.com/docs/agents/concepts/agent-harnesses
- https://code.visualstudio.com/docs/agents/run/agent-harnesses
- https://code.visualstudio.com/features/models
- https://code.visualstudio.com/docs/agents/concepts/agent-host

As of this plan, Microsoft states that Agent Host and Agent Host Protocol are under active development. P2.2B therefore does not create a direct AHP client or depend on unstable AHP behavior for qualification.

## Identity model

P2.2B preserves four separate identities:

```text
HOST != HARNESS
HARNESS != PROVIDER_SOURCE
PROVIDER_SOURCE != PROVIDER
PROVIDER != MODEL
MODEL != AUTHORITY
```

`host_id` is `vscode` for this contract.

`harness_id` identifies the selected VS Code harness:

```text
local
copilot
claude
codex
```

`provider_source_id` records the visible/authenticated source through which the selected model is being supplied to the harness. Examples include:

```text
copilot
anthropic
chatgpt
```

Other current VS Code/BYOK sources may use a normalized source identifier when directly observed and recorded.

`provider_id` records the underlying model provider identity when that identity is evidenced, for example:

```text
anthropic
openai
google
```

`model_id` records the exact model identifier or exact visible model label used for the observation. A model family name must not be silently converted into provider-source evidence.

## Qualification classes

### `STATIC_CONFIGURATION_ONLY`

The path is configured or described but no live model execution was observed.

This class does not establish model reachability, provider availability, provider-native compatibility, or runtime effectiveness.

### `LIVE_HOST_ROUTED_MODEL_OBSERVED`

A live VS Code harness/model path completed the frozen observation fixture, but the evidence does not establish a provider-native harness-to-provider route.

Examples:

```text
Copilot harness + Claude model supplied by Copilot
Copilot harness + Gemini model supplied by Copilot
Claude harness + Claude model supplied by Copilot
Codex harness + OpenAI model supplied by Copilot
Local harness + configured/BYOK model
```

This proves only the observed VS Code path under the recorded configuration.

### `LIVE_PROVIDER_NATIVE_HARNESS_OBSERVED`

A provider-specific VS Code harness completed the frozen fixture using its provider-native source identity.

P2.2B recognizes these initial exact mappings:

```text
Claude harness + Anthropic source + Anthropic provider
Codex harness + ChatGPT source + OpenAI provider
```

This classification is narrower than a general provider certification. It proves the recorded VS Code provider-native harness path only.

In particular:

```text
VS_CODE_CLAUDE_NATIVE_PASS != P2_2A_STANDALONE_CLAUDE_CLI_LIVE_QUALIFICATION
VS_CODE_CODEX_NATIVE_PASS != EVERY_CODEX_HOST_PATH_QUALIFIED
```

A future runtime engine that directly depends on a VS Code/AHP harness requires its own implementation and qualification boundary.

### `LIVE_MODEL_PATH_FAILED`

A live attempt was made and current evidence records failure. Failure is retained as evidence and must not be rewritten as static or passing evidence.

## Frozen fixture

P2.2B includes:

```text
tests/fixtures/vscode-provider-qualification/fixture-v1.json
```

Content SHA-256:

```text
010ab2a84c45bf6aa30e056fdaf5bb1d7fd61e224499fb2055744746a391b569
```

The fixture asks the selected harness/model to read and return a small deterministic challenge without editing repository files.

A passing observation requires the expected fixture values to be visibly returned and the Git worktree to be clean before and after the attempt.

## Observation contract

Machine input:

```text
machine/schemas/vscode-provider-observation.v1.schema.json
```

The observation records:

- VS Code host identity;
- harness identity;
- provider source identity;
- provider identity;
- model identity;
- execution environment;
- exact repository revision;
- exact fixture identity and SHA-256;
- whether a live model execution occurred;
- whether the session target, model, provider source, and fixture result were actually observed;
- repository cleanliness before and after;
- PASS, FAIL, or NOT_RUN result;
- evidence references;
- explicit limitations.

A live PASS fails closed unless all required identities and fixture evidence are present and repository state remained clean.

## Qualification receipt

Machine output:

```text
machine/schemas/provider-qualification-receipt.v1.schema.json
```

Runtime/CLI surfaces:

```text
orchestra_runtime/provider_qualification.py
scripts/qualify_vscode_provider.py
```

Every receipt forces these authority fields to false:

```text
automatic_routing_authorized = false
provider_execution_authority = false
release_authorized = false
```

Therefore:

```text
LIVE_PROVIDER_OBSERVATION != PROVIDER_EXECUTION_AUTHORITY
LIVE_PROVIDER_OBSERVATION != AUTOMATIC_ROUTING_AUTHORITY
LIVE_PROVIDER_OBSERVATION != RELEASE_AUTHORITY
```

## Operator protocol for live evidence

Live VS Code evidence must be collected on a user-controlled machine. Orchestra does not fabricate it from deterministic tests.

### Gate 1: exact repository state

Record:

```text
git rev-parse HEAD
git status --porcelain
```

The intended repository revision must be exact and the worktree must be clean before the observation.

### Gate 2: select the session target

In VS Code, start a new agent session and explicitly select the target harness from the Session Target control.

Record the visibly selected harness.

Do not infer the harness from the model name.

### Gate 3: select and record the model source

Record:

- exact visible model label or identifier;
- provider grouping/source shown by VS Code when available;
- relevant authenticated route such as Copilot, Anthropic, or ChatGPT.

When both provider-native and Copilot-routed models are available, the selected model source determines the evidence classification. Do not infer provider-native status merely because the model is made by Anthropic or OpenAI.

### Gate 4: run the frozen read-only fixture

Ask the selected session to read:

```text
tests/fixtures/vscode-provider-qualification/fixture-v1.json
```

and return the stored marker, sequence, expected sum, and specialist exactly.

Do not ask the harness to modify files, install packages, alter settings, or perform provider setup.

### Gate 5: verify repository state again

Run:

```text
git status --porcelain
```

A passing observation requires clean state after the attempt.

VS Code worktree isolation is not treated as a sandbox proof. Current Microsoft documentation explicitly notes that worktree isolation does not restrict commands, network access, or access outside the worktree. P2.2B therefore records execution environment separately and does not infer sandbox capability from worktree use.

### Gate 6: capture evidence

Evidence refs may identify user-preserved screenshots, session exports, or other bounded records that establish:

- Session Target / harness;
- model;
- provider source when visible;
- fixture result;
- exact repository identity;
- clean repository before and after.

Do not store API keys, OAuth tokens, credentials, raw secrets, or unnecessary full conversation history in the observation record.

### Gate 7: validate the observation

Run:

```text
python scripts/qualify_vscode_provider.py --input <observation.json> --output <receipt.json>
```

The validator emits a non-authorizing receipt or fails closed.

## Security and permission boundary

P2.2B does not claim that a VS Code harness is confined merely because it uses a worktree or a particular approval preset.

Current VS Code documentation notes that worktree sessions use Bypass Approvals because code changes are isolated, while the worktree does not itself restrict commands, network, or access outside the worktree. Those properties are therefore not mapped to Orchestra provider capabilities by this qualification layer.

P2.2B also never enables settings that bypass permission checks and never mutates user settings or provider credentials.

## Relationship to P2.2A

P2.2A implemented a bounded standalone Claude Code CLI provider-native bridge and passed deterministic qualification. It deliberately did not claim live Anthropic/Claude provider E2E.

P2.2B adds a different evidence surface:

```text
P2_2A = STANDALONE_CLAUDE_CODE_ENGINE_IMPLEMENTATION
P2_2B = VS_CODE_MULTI_HARNESS_PROVIDER_OBSERVATION_AND_CLASSIFICATION
```

A VS Code Claude/Anthropic live pass is useful evidence that the user environment can reach a provider-native Anthropic harness path. It is not automatically evidence that Orchestra's P2.2A standalone Claude CLI invocation contract works end-to-end.

## Relationship to future routing

Automatic provider routing remains unimplemented and unauthorized by this unit.

A future routing-policy unit must decide which evidence classes are sufficient for which execution engines. It may not collapse host-routed and provider-native observations into one category merely to satisfy a routing prerequisite.

Potential future steps remain separately bounded:

```text
P2.2B deterministic qualification
  -> user-controlled live VS Code observations
  -> provider/harness evidence adjudication
  -> optional VS Code/AHP execution-engine audit if justified
  -> separately reviewed multi-provider routing policy
  -> only then consider automatic routing/fallback
```

## Relationship to Cloak CUIR

The finalized Cloak UI Reference Corpus plan is independent of provider qualification.

After P2.2B reaches its deterministic qualification and live-evidence checkpoint, `CUIR-0` is the next planned specialist-upgrade lane. If live VS Code evidence requires local user interaction, CUIR may proceed independently while that evidence is pending.

CUIR progress is never provider qualification evidence.

## Explicit exclusions

P2.2B does not:

- install or update VS Code;
- install or refresh extensions;
- modify VS Code settings;
- modify GitHub Copilot, Anthropic, ChatGPT, or provider credentials;
- call provider APIs directly;
- create an AHP client;
- create a VS Code extension runtime;
- claim provider availability from deterministic tests;
- claim standalone Claude CLI live qualification from a VS Code Claude session;
- claim sandboxing from worktree isolation;
- enable automatic routing or fallback;
- mutate the Compliance Registry;
- publish a release;
- deploy or mutate production;
- activate or weaken policy/rulesets;
- delete branches;
- force push or rewrite history.

## Bounded implementation disposition

```text
P2_2B_IMPLEMENTATION_BOUNDARY = OBSERVATION_CONTRACT_AND_NON_AUTHORIZING_QUALIFICATION_ONLY
VS_CODE_DIRECT_CONTROL = NOT_IMPLEMENTED
AHP_INTEGRATION = DEFERRED
LIVE_PROVIDER_EVIDENCE = USER_CONTROLLED_AND_SEPARATE
HOST_ROUTED_AND_PROVIDER_NATIVE_EVIDENCE = DISTINCT
AUTOMATIC_ROUTING = NOT_AUTHORIZED
```
