# UIEF Reference, Provenance, and Responsive Erratum

Status: `CURRENT_MAIN_SUCCESSOR_PENDING_QUALIFICATION`

Program: `ORCHESTRA_UIEF_V1`

Baseline:

```text
MAIN=63bbe70f29fa5e2d72ffb34a3f071a7d3fc725e4
TREE=2b95a4509acaf1d9044dd9278dc3e71b97b0b47e
OEE=COMPLETE_CANONICAL_VERIFIED
AWF_N1_N6=COMPLETE_CANONICAL_VERIFIED
SOURCE_EVIDENCE_PR_799=c80d8ad5b7b3fb6d686a26f44d364b9db6b934bf
```

## Purpose

This erratum repairs reference-integrity and responsive-intent defects in the canonical UIEF-1 reference profile and UIEF-4 Cloak fidelity handoff without changing specialist authority or rewriting historical UIX/CUIR evidence.

The correction is upstream of UIEF-5. Clockwork must consume a coherent, traceable Cloak handoff rather than choose between contradictory visible-design instructions or infer provenance that does not exist.

## Findings

The pre-erratum UIEF reference files cited repository-local paths for a workspace split-pane pattern, project-native command palette, Anthropic artifact-canvas guidance, observed sidecar-drawer output, composition specifications, an icon, design tokens, a Cloak handoff specification, and a Clockwork boundary document.

Repository and path-history checks established that those cited paths were not present as canonical source artifacts. The corresponding provider/project-native provenance identifiers were present only in UIEF reference files and fixtures, not in authoritative source records. They therefore cannot serve as provenance.

The CUIR-3 canonical catalog at `machine/knowledge/cloak-ui-reference-cuir3.v1.json` also contains no `workspace split pane` normalized pattern. The real relevant normalized patterns are:

- `cuir3.destination_state_navigation`
- `cuir3.selection_and_disclosure_state`

The first explicitly preserves destination state as navigation changes between expanded, collapsed, and compact presentations. The second preserves explicit, reversible disclosure state.

The UIEF-4 handoff also contained contradictory responsive instructions:

- macro composition required an accordion-stack collapse below 1024px;
- tablet behavior required drawer-toggle navigation;
- mobile behavior required drawer-overlay navigation.

Cloak owns that visible-layer decision. The detailed breakpoint behavior and real CUIR navigation evidence support drawer-based navigation below 1024px, so the macro summary is corrected to match those accepted breakpoint transformations.

## Correction

The canonical reference candidate now:

1. binds UIEF-1 and UIEF-4 to existing repository sources only;
2. uses the canonical CUIR-3 catalog for normalized pattern evidence;
3. omits project-native and provider-specific evidence when no traceable source exists;
4. keeps consuming-project component, icon, token, and accent-color identities explicit as unresolved inputs instead of inventing placeholder paths;
5. binds composition and Clockwork-boundary guidance to the existing UIEF plan;
6. aligns the responsive macro summary with tablet/mobile drawer behavior;
7. preserves the existing authority boundaries: no implementation, architecture-translation, release, deployment, or policy authority is granted.

## Historical OEE replay preservation

OEE-7 was designed to replay the real UIEF-5 usage-exhaustion incident. Before this erratum it read the live UIEF-4 handoff and expected the historical contradiction to remain present.

That coupling would make a legitimate UIEF repair invalidate OEE historical evidence.

The pre-erratum handoff is therefore frozen at:

`tests/fixtures/oee/uief5-responsive-contradiction-20260905.json`

The OEE-7 replay reads that historical fixture instead of the evolving live handoff. This preserves the historical blocker and OEE efficiency proof while allowing the current UIEF contract to be corrected.

## Regression policy

The candidate adds deterministic checks that require:

- every repository-local reference in the canonical UIEF profile/handoff to resolve to a real file;
- every selected CUIR normalized pattern identifier to exist in the canonical CUIR-3 catalog;
- the Orchestra reference fixture not to invent project-native or provider-specific sources;
- the live responsive macro summary to agree with tablet/mobile drawer behavior;
- the historical OEE replay fixture to retain the original contradiction.

Synthetic invalid fixtures may still contain deliberately malformed data when required to exercise validation failures. They are not provenance authorities.

## UIEF-5 re-entry

This erratum does not make PR #791 canonical and does not authorize UIEF-5 implementation by itself.

UIEF-5 may be requalified only after this upstream correction is canonical and the Clockwork translation candidate is rebased or reconstructed against the corrected source identity. The known UIEF-5 validator weakness also remains to be hardened before promotion.

## Authority

This erratum:

- does not create a new specialist;
- does not transfer Cloak design authority;
- does not expand Conductor, Clockwork, Ponytail, Overseer, or Arbiter authority;
- does not authorize release or deployment;
- does not alter CUIR historical evidence;
- does not rewrite historical OEE evidence.

Canonical completion may be claimed only after exact-head qualification, signed materialization where required, canonical merge, and independent `main` readback.
