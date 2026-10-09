# Third-Party Provenance and Acknowledgements

Orchestra has been built and refined with help from external tools, implementation references, protocol specifications, and research repositories. This ledger records those relationships without implying affiliation, endorsement, copied source, runtime dependency, or authority.

The canonical machine-readable record is [`machine/provenance/third-party.v1.json`](../machine/provenance/third-party.v1.json). It carries the detailed reviewed revision, license status, purpose, learned or incorporated patterns, affected Orchestra surfaces, evidence, and incorporation boundaries for each entry.

## Classification model

- **TEST_TOOL_DEPENDENCY**: development, CI, validation, or release-confidence tool. Not Orchestra runtime code.
- **REFERENCE_ONLY**: patterns or guidance were independently incorporated or retained, with no runtime dependency or copied source unless explicitly stated.
- **PROTOCOL_STANDARD_REFERENCE**: protocol/specification used to implement an interoperability surface.
- **HISTORICAL_RESEARCH_REFERENCE**: reviewed during historical architecture or product research but not promoted as an incorporated implementation dependency.
- **EVALUATED_OR_PLANNED_REFERENCE**: active or deferred research input for future work. It is not part of the current runtime.
- **INTEGRATED_RUNTIME_DEPENDENCY**: third-party component required at runtime.
- **VENDORED_OR_COPIED_CODE**: third-party source copied, adapted, or vendored into Orchestra and subject to explicit license/notice obligations.

Unknown historical facts stay unknown. An unrecovered commit pin is recorded as unrecovered rather than reconstructed from memory.

## Validation and test tooling

### mutmut 3.6.0

`boxed/mutmut` | BSD-3-Clause | **TEST_TOOL_DEPENDENCY**

Used for bounded mutation testing during release-confidence hardening. Orchestra preserves tool incompatibility as evidence rather than turning incomplete mutation execution into a score. No runtime dependency or source incorporation.

### Hypothesis 6.163.0

`HypothesisWorks/hypothesis` | MPL-2.0 | **TEST_TOOL_DEPENDENCY**

Used for property-based testing of machine-contract, governance, evidence, state, and policy invariants. No runtime dependency or source incorporation.

### Cosmic Ray 8.7.0

`sixty-north/cosmic-ray` | MIT | **TEST_TOOL_DEPENDENCY**

Used as the bounded mutation-confidence runner after the mutmut instrumentation incompatibility. Scores are accepted only from complete, baseline-passing, machine-evidenced sessions. No runtime dependency or source incorporation.

## Incorporated reference patterns

### Strix

`usestrix/strix` | Apache-2.0 | **REFERENCE_ONLY**

Reviewed commit: `09872744f5a9d3ffad750478f823e656ac1a7c88`

A static, read-only adversarial-security review informed declared authority scope, lifecycle-gated completion, run-scoped capabilities, validated specialist delegation, and adversarial validation thinking. Offensive tooling and source were not imported.

Historical Orchestra evidence: commit `7a6e63702a469f4d72261dffa19800c9f75b60dd`.

### Spec-Kitty

`Priivacy-ai/spec-kitty` | MIT | **REFERENCE_ONLY**

Reviewed version: `v3.2.6`
Reviewed commit: `8466727ebbbc01fcaf43575657c9b1b9553784d9`

Independently adapted concepts include work packages, runtime envelopes, correlation identifiers, retrospectives, and worktree/status projection. Direct runtime dependency and wholesale copying of upstream schemas or state machines were rejected.

Historical Orchestra evidence: commit `7a3cd1aef86e4edb5194cd68f52d5e26cc2c66fc`.

### Bryl Minimal Design

`bryllim/bryl-minimal-design` | MIT | **REFERENCE_ONLY**

Used as a UI/design reference for restrained hierarchy, typography, halftone texture, accessibility-aware interaction, restrained motion, and semantic presentation guidance.

Historical Orchestra evidence: commit `0ac68ab2627313522a23ddfca76387ee9c925063`.

The exact historical upstream revision was not recoverable during the v1.6 audit, so no revision is guessed.

### Ponytail

`DietrichGebert/ponytail` | MIT | **REFERENCE_ONLY**

Reviewed upstream checkpoint: `2ed6c52c9d7e5e56942508591085fd45dea277d3` (`4.9.0`)

Retained principles include questioning speculative work, inspecting before editing, reusing existing/native code, choosing the smallest correct diff, focused testing, and frontend lifecycle cleanup. Orchestra governance remains authoritative.

Historical Orchestra evidence: commit `5d18580b7003f3f820cdc78d6e033c4c344e8c24`.

A maintainer fork, `Baelfyre/ponytail`, was also compared at `14a0d79548d4de8fc2de95c1b94bb0de63a739d3`; its core `SKILL.md` matched the reviewed upstream checkpoint.

### Caveman

`JuliusBrussee/caveman` | mixed/current upstream license text | **REFERENCE_ONLY**

Used as a communication-behavior reference for concise, focused output, reduced redundant summarization, and lower filler while preserving required explanation.

Historical Orchestra evidence: commit `556bfe7cd67feedac5d05ec1c98948b862370f5c`.

No Caveman source is bundled, copied, installed, or required. The exact historical upstream revision was not recovered, and this audit does not retroactively assert a single historical SPDX license.

### TrueSheet

`lodev09/react-native-true-sheet` | MIT | **REFERENCE_ONLY**

Reviewed commit: `23e119c026e2040d960725bd260e6cd4bf680b95`

Used to enrich mobile UI specialist knowledge around controlled sheet behavior, lifecycle, navigation, accessibility, native/web divergence, testing, and architecture. No source or wholesale material was copied and no runtime dependency was introduced.

Detailed canonical mapping: [`machine/knowledge/truesheet-specialist-reference.v1.json`](../machine/knowledge/truesheet-specialist-reference.v1.json).

## Protocol reference

### Model Context Protocol

`modelcontextprotocol/modelcontextprotocol` | MIT | **PROTOCOL_STANDARD_REFERENCE**

Protocol revision: `2026-07-28`
Official tagged commit: `d9fb94d3df5112ad1a52278685841486480b138d`

Orchestra's v1.6 MCP implementation uses this specification for its bounded stdio transport and exposes only the declared tool surface. MCP remains transport, not authority, and is not recorded as an Orchestra runtime package dependency.

See [`docs/developer/MCP_STDIO_TRANSPORT.md`](developer/MCP_STDIO_TRANSPORT.md).

## Historical research references

### OpenHero

`CristianOlivera1/openhero` | MIT | **HISTORICAL_RESEARCH_REFERENCE**

Reviewed commit: `16ffaa7e6dc39eb390011d81c420353b5d1dbaff`

A read-only audit compared progressive UI behavior, optimistic reconciliation, fallback-backed loading, layered archive validation, and unsafe substring allowlisting. The audit did not promote OpenHero source or a runtime dependency.

Historical Orchestra evidence: commit `6e35d10bfed2f0d9655f0bc9a200178deb07afc5`.

### phionyx-research

`halvrenofviryel/phionyx-research` | current upstream license AGPL-3.0 | **HISTORICAL_RESEARCH_REFERENCE**

Historical governance/evidence research covered runtime evidence layers, auditable evidence-chain thinking, deterministic gate verdicts, and replay-oriented records. The exact historical revision was not recovered. No source incorporation is asserted.

### AI SAFE2 Framework

`CyberStrategyInstitute/ai-safe2-framework` | upstream describes MIT + CC-BY-SA; GitHub metadata `NOASSERTION` | **HISTORICAL_RESEARCH_REFERENCE**

Used for comparative research into agentic-AI governance, GRC, security, non-human identities, swarm governance, and assurance concepts. It was research input, not a runtime dependency or authority source. The exact historical reviewed revision was not recovered.

### orchestra-hq/orchestra-skills

`orchestra-hq/orchestra-skills` | current upstream license MIT | **HISTORICAL_RESEARCH_REFERENCE**

Used as a comparative reference for external agent-skill packaging and integration patterns. It is unrelated to Orchestra runtime authority and is not an installed dependency. The exact historical reviewed revision was not recovered.

## Deferred and planned research

### Sakana AI Fugu

`SakanaAI/fugu` | upstream GitHub license metadata currently unasserted | **EVALUATED_OR_PLANNED_REFERENCE**

Issue [#340](https://github.com/Baelfyre/Orchestra/issues/340) records Fugu as the primary research reference for the future Adaptive Governed Orchestration enhancement. Candidate ideas include worker/model selection, task decomposition, coordination topology, selective context access, bounded test-time compute, and offline policy optimization.

No Fugu code or runtime authority is part of v1.6.0. Phase A0 explicitly requires a pinned revision and license/provenance review before any implementation is frozen.

## Source-use and authority boundary

For the references above:

- a citation or learned pattern does not grant runtime or governance authority;
- source copying, vendoring, or adaptation must be explicitly recorded;
- runtime dependencies must be explicitly classified;
- licenses and reviewed revisions must be recorded when trustworthy;
- unknown historical facts remain unknown;
- future research must not be represented as already incorporated.

The current registry records zero vendored/copied third-party source items and zero new re-foundation runtime dependencies.

## Machine-readable counterpart

Canonical semantic provenance:

`machine/provenance/third-party.v1.json`

Validation schema:

`machine/schemas/third-party-provenance.schema.json`

The Markdown and JSON are not required to be literal duplicates. They are required to be semantically consistent. The JSON is intentionally more detailed so an automated reviewer can reconstruct why an upstream was consulted, what Orchestra learned or incorporated, what surfaces were affected, what evidence supports the attribution, and what was explicitly not incorporated.
