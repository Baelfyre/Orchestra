#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Temporary self-retiring v1.11.0 release-candidate materializer."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "release/v1.11.0-adaptive-assurance-20260911"
BASE = "8c75fb53cbcdc5f05a74f8377f097c336e5ccce6"
VERSION = "1.11.0"
TAG = "v1.11.0"
V110_RELEASE = "756a358f96363f0c377b049adcd87b1991d5aef6"
V110_TREE = "42c0c8929c4dcfa5b17ff2feb293710d2468ca51"
V110_RELEASE_ID = "383668751"
HELPERS = [
    ROOT / "tools/_v1_11_0_release_materializer.py",
    ROOT / ".github/workflows/_v1-11-0-release-materialize.yml",
    ROOT / "tools/_v1_11_0_release_repair.py",
    ROOT / ".github/workflows/_v1-11-0-release-repair.yml",
]


def run(*args: str) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True)


def out(*args: str) -> str:
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one replacement in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def prepend(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if block.strip() in text:
        return
    path.write_text(block + text, encoding="utf-8")


def bump_json_version(path: Path, *, container: str | None = None) -> None:
    payload = load_json(path)
    target = payload if container is None else payload[container]
    if target.get("version") != "1.10.0":
        raise RuntimeError(f"unexpected version in {path}: {target.get('version')}")
    target["version"] = VERSION
    dump_json(path, payload)


def main() -> None:
    if out("git", "branch", "--show-current") != BRANCH:
        raise RuntimeError("unexpected branch")
    if out("git", "merge-base", BASE, "HEAD") != BASE:
        raise RuntimeError("release branch no longer descends from expected AQ14 canonical base")
    run("git", "config", "user.name", "JEO")
    run("git", "config", "user.email", "192281269+Baelfyre@users.noreply.github.com")

    # Canonical package/version surfaces.
    bump_json_version(ROOT / "plugin.json")
    bump_json_version(ROOT / ".claude-plugin/plugin.json")
    bump_json_version(ROOT / ".codex-plugin/plugin.json")
    adapter_packages = sorted((ROOT / "adapters").glob("*/package.json"))
    for path in adapter_packages:
        bump_json_version(path)
    surface_count = len(adapter_packages) + 3
    if surface_count < 3:
        raise RuntimeError(f"canonical version-surface discovery is invalid: {surface_count}")

    marketplace = load_json(ROOT / ".claude-plugin/marketplace.json")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1 or plugins[0].get("version") != "1.10.0":
        raise RuntimeError("unexpected Claude marketplace version surface")
    plugins[0]["version"] = VERSION
    dump_json(ROOT / ".claude-plugin/marketplace.json", marketplace)

    host_update = load_json(ROOT / "machine/hosts/update-contract.v1.json")
    if host_update.get("package_version") != "1.10.0":
        raise RuntimeError("unexpected host-update contract package version")
    host_update["package_version"] = VERSION
    dump_json(ROOT / "machine/hosts/update-contract.v1.json", host_update)

    replace_once(
        ROOT / "adapters/jetbrains/plugin.xml",
        "<version>1.10.0</version>",
        "<version>1.11.0</version>",
    )
    replace_once(
        ROOT / "tests/runtime/test_release_version_surfaces.py",
        'EXPECTED_VERSION = "1.10.0"',
        'EXPECTED_VERSION = "1.11.0"',
    )
    replace_once(
        ROOT / "tests/runtime/test_host_updates.py",
        'CURRENT_VERSION = "1.10.0"',
        'CURRENT_VERSION = "1.11.0"',
    )
    replace_once(
        ROOT / "tests/runtime/test_host_updates.py",
        'latest_version="v1.11.0"',
        'latest_version="v1.12.0"',
    )
    replace_once(
        ROOT / "tests/runtime/test_host_updates.py",
        'assert available.latest_version == "1.11.0"',
        'assert available.latest_version == "1.12.0"',
    )

    readme_index = load_json(ROOT / "README.json")
    repo = readme_index["repository"]
    if repo.get("package_version") != "1.10.0" or repo.get("current_public_release") != "v1.10.0":
        raise RuntimeError("README.json public/package baseline drift")
    repo["package_version"] = VERSION
    repo["next_release_plan"] = "V1.11.0_ADAPTIVE_ASSURANCE_GOVERNANCE_HARDENING_CANDIDATE"
    repo["next_release_plan_status"] = "PREPARED_NOT_PUBLISHED"
    repo["release_candidate"] = {
        "version": VERSION,
        "status": "PREPARED_NOT_PUBLISHED",
        "theme": "ADAPTIVE_ASSURANCE_AND_PROTECTED_GOVERNANCE_HARDENING",
        "source_baseline": BASE,
        "previous_public_release": "v1.10.0",
        "previous_public_release_commit": V110_RELEASE,
        "post_v1_10_commit_count_at_freeze": 30,
        "adaptive_assurance": "AQ1_THROUGH_AQ14_COMPLETE_CANONICAL_VERIFIED",
        "prai": "POST_RUN_ASSURANCE_COMPLETE_CANONICAL_VERIFIED",
        "covenant": "COMPLETE_CANONICAL_VERIFIED",
        "protected_governance": "ESCALATION_HUMAN_ONLY_WHITELIST_AND_TREE_ATTESTED_PROMOTION_CANONICAL",
        "tenant_administration_reference": "AQ7_RUNTIME_ADAPTER_PARITY_INCLUDED",
        "aq15": "UNREGISTERED_NOT_INCLUDED",
        "ar_refoundation": "AR3_THROUGH_AR9_DEFERRED_UNTIL_AFTER_V1_11_0",
        "publication": "PREPARED_NOT_PUBLISHED",
        "support_link": "https://buymeacoffee.com/baelfyre",
    }
    dump_json(ROOT / "README.json", readme_index)

    changelog_block = """## v1.11.0 Adaptive Assurance and Governance Hardening - release candidate - prepared\n\n- Packages all 30 canonical commits after the immutable v1.10.0 release commit `756a358f96363f0c377b049adcd87b1991d5aef6` through AQ14 canonical `8c75fb53cbcdc5f05a74f8377f097c336e5ccce6`.\n- Delivers the complete ADAPT-QA AQ1-AQ14 assurance sequence: normative doctrine, risk profiling, specialist assurance contracts, manifests/receipts, repository QA compliance, gate-coverage truthfulness, runtime/adapter parity, high-risk assurance packs, deep assurance, defect-escape RCA, remediation-effectiveness pilot, adversarial self-test, staged non-production evaluation, and final effectiveness qualification.\n- Includes PRAI post-run assurance, Protected Governance Escalation, Covenant cross-governance synthesis, human-only whitelist authority, exact-scope phase separation, and tree-attested promotion assurance.\n- Includes the AQ7 tenant-administration reference slice with domain/application/persistence/HTTP-shaped adapter parity as bounded architecture evidence.\n- Preserves evidence-only/non-authorizing semantics: assurance PASS does not grant provider, telemetry, production, deployment, policy, whitelist, AQ15, or CritiQual CUD10 authority.\n- Keeps AQ15 unregistered and excludes AR-3 through AR-9 implementation from this release; architecture refoundation resumes only after v1.11.0 publication and reconciliation.\n- Aligns all canonical package/version surfaces and the host-update contract to `1.11.0`.\n- Candidate status is `PREPARED_NOT_PUBLISHED`; publication is separately authorized by the maintainer and occurs only after governed exact-head qualification and signed canonical promotion.\n\n"""
    prepend(ROOT / "CHANGELOG.md", changelog_block)

    context_old = (
        "v1.10.0 Universal Adaptive Integration and Conductor Routing is published and verified at signed canonical commit "
        "`756a358f96363f0c377b049adcd87b1991d5aef6`, tree `42c0c8929c4dcfa5b17ff2feb293710d2468ca51`, "
        "tag `v1.10.0`, and GitHub Release `383668751`. Post-publication documentation normalization is active. UAI-0 through "
        "UAI-10 and the Conductor routing reconciliation are complete. GitHub Copilot `/conductor` is `SUPPORTED_VERIFIED` from maintainer "
        "evidence, while Auto-mode provider/model identity remains unresolved and unadmitted."
    )
    context_new = (
        "v1.11.0 Adaptive Assurance and Governance Hardening is the active release candidate over the immutable published v1.10.0 baseline "
        "at `756a358f96363f0c377b049adcd87b1991d5aef6`. The candidate freezes all 30 post-v1.10.0 canonical commits through AQ14 at "
        "`8c75fb53cbcdc5f05a74f8377f097c336e5ccce6`, including AQ1-AQ14, PRAI, Covenant, protected-governance escalation, human-only "
        "whitelist authority, and tree-attested promotion assurance. AQ15 is unregistered and AR-3 through AR-9 remain deferred until after v1.11.0 publication."
    )
    replace_once(ROOT / "PROJECT_CONTEXT.md", context_old, context_new)
    replace_once(
        ROOT / "PROJECT_CONTEXT.md",
        "All 11 release/version surfaces and `machine/hosts/update-contract.v1.json#/package_version` are normalized to published v1.10.0; post-publication documentation normalization does not change machine authority.",
        "All canonical release/version surfaces and `machine/hosts/update-contract.v1.json#/package_version` are normalized to the v1.11.0 candidate; the current public release remains immutable v1.10.0 until publication completes.",
    )

    state = ROOT / "PROJECT_STATE.md"
    replace_once(state, "- **Target Release:** `POST_PUBLICATION_DOCUMENTATION_NORMALIZATION`", "- **Target Release:** `v1.11.0`")
    replace_once(state, "- **Release-Candidate Metadata:** `1.10.0` (`PUBLISHED_VERIFIED_COMPLETE`)", "- **Release-Candidate Metadata:** `1.11.0` (`PREPARED_NOT_PUBLISHED`)")
    replace_once(state, "- **Control Plane State:** `V1_10_0_CANDIDATE`", "- **Control Plane State:** `V1_11_0_CANDIDATE`")
    state_block = """## v1.11.0 Adaptive Assurance and Governance Hardening Candidate\n\nThe v1.11.0 candidate freezes the complete post-v1.10.0 delta: 30 canonical commits after release commit `756a358f96363f0c377b049adcd87b1991d5aef6` through AQ14 canonical `8c75fb53cbcdc5f05a74f8377f097c336e5ccce6`. The release centers the full AQ1-AQ14 assurance stack, PRAI post-run assurance, Covenant cross-governance synthesis, Protected Governance Escalation, human-only whitelist authority, and tree-attested promotion assurance. AQ7 also contributes the bounded tenant-administration domain/application/persistence/HTTP adapter-parity reference slice.\n\nAll canonical package/version surfaces and the host-update contract are aligned to `1.11.0`. The current public release remains immutable `v1.10.0` until publication. AQ15 is unregistered and not included. AR-3 through AR-9 are intentionally deferred until after v1.11.0 publication and Padayon reconciliation.\n\nThe candidate is `PREPARED_NOT_PUBLISHED`. The maintainer has explicitly authorized v1.11.0 publication, but tag and GitHub Release creation remain downstream of exact-head source qualification, signed identical-tree materialization, canonical promotion, and post-merge verification.\n\n"""
    state_text = state.read_text(encoding="utf-8")
    marker = "## v1.10.0 Universal Adaptive Integration and Conductor Routing Publication\n"
    if state_block.strip() not in state_text:
        if marker not in state_text:
            raise RuntimeError("PROJECT_STATE v1.10 section marker missing")
        state.write_text(state_text.replace(marker, state_block + marker, 1), encoding="utf-8")

    candidate_doc = ROOT / "docs/releases/v1.11.0-adaptive-assurance-governance-release-candidate.md"
    candidate_doc.write_text("""# Orchestra v1.11.0 — Adaptive Assurance and Governance Hardening\n\n## Candidate status\n\n`PREPARED_NOT_PUBLISHED`\n\n## Release scope\n\nThis minor release packages the complete 30-commit canonical delta after v1.10.0 (`756a358f96363f0c377b049adcd87b1991d5aef6`) through AQ14 canonical (`8c75fb53cbcdc5f05a74f8377f097c336e5ccce6`). It is additive and governance/assurance focused; it does not activate providers, telemetry, deployment, production mutation, protected-policy mutation, or new post-AQ14 authority.\n\n## AQ series summary\n\n| Phase | Purpose | Terminal state |\n| --- | --- | --- |\n| AQ1 | Normative adaptive-assurance doctrine and evidence vocabulary | Complete / canonical verified |\n| AQ2 | Deterministic adaptive risk profiling and minimum assurance topology | Complete / canonical verified |\n| AQ3 | Specialist assurance contracts, Conductor receipts, Overseer sufficiency, Arbiter progression checks | Complete / canonical verified |\n| AQ4 | Candidate-bound assurance manifests and evidence receipts | Complete / canonical verified |\n| AQ5 | Independent repository QA-compliance evaluation | Complete / canonical verified |\n| AQ6 | Gate-coverage truthfulness: changed behavior must be reached by declared assurance | Complete / canonical verified |\n| AQ7 | Runtime and adapter parity via bounded tenant-administration reference slice | Complete / canonical verified |\n| AQ8 | High-risk security, provenance, concurrency, state-machine, and evidence-integrity assurance packs | Complete / canonical verified |\n| AQ9 | Deep assurance expansion using mutation, property, metamorphic, and bounded-fuzz evidence | Complete / canonical verified |\n| AQ10 | Deterministic defect-escape root-cause analysis and prevention recommendations | Complete / canonical verified |\n| AQ11 | Controlled remediation-effectiveness pilot over known escape classes | Complete / canonical verified |\n| AQ12 | Adversarial self-test for scope drift, escalation, evidence tampering, forged transitions, bypass, and determinism drift | Complete / canonical verified |\n| AQ13 | Staged non-production SHADOW → CANARY → LIMITED → EXPANDED evaluation | Complete / canonical verified |\n| AQ14 | Final deterministic effectiveness qualification over the canonical AQ9-AQ13 evidence chain | Complete / canonical verified |\n\nAQ15 is not a defined phase. It remains unregistered and is not part of v1.11.0.\n\n## Additional post-v1.10.0 changes\n\n- PRAI post-run assurance with candidate/source/tree binding, adaptive audit depth, contradiction and stale-evidence rejection, and non-authorizing evidence semantics.\n- Protected Governance Escalation that freezes a candidate and terminates the autonomous run when progress would require changing the governance blocking that same candidate.\n- Covenant evidence-only cross-governance synthesis with Steward/Governor judgment guidance and COV-01 through COV-18 conflict coverage.\n- Human-only whitelist mutation authority; AI may analyze and recommend, but cannot approve or mutate protected whitelist policy in the same autonomous run.\n- Tree-attested promotion assurance allowing exact qualified-tree evidence reuse only through independently verified signed identical-tree carriers.\n- Exact-scope AQ8/AQ9 and reusable AQ10-AQ14 phase separation while partial/mixed/unknown scopes continue to fail closed.\n- Expanded protected workflows: PRAI, AQ5 QA Compliance, AQ6 Gate Coverage Truthfulness, governance, Required Analysis, Cross-platform Validation, validate, and Cosmic Ray confidence.\n\n## Boundaries retained\n\n- AQ/PRAI/Covenant evidence does not itself grant lifecycle, release, deployment, production, provider, telemetry, whitelist, or protected-policy authority.\n- CritiQual CUD10 remains outside this release's authority.\n- AR-3 through AR-9 are intentionally deferred until after v1.11.0 publication and reconciliation.\n- No AQ15 implementation is included or implied.\n\n## Publication path\n\nThe maintainer explicitly authorized publication of v1.11.0. Publication still requires exact-head source qualification, signed identical-tree materialization, canonical promotion, post-merge verification, immutable `v1.11.0` tag/release creation, and independent readback.\n""", encoding="utf-8")

    readiness = ROOT / "docs/validation/V1_11_0_RELEASE_READINESS_EVIDENCE.md"
    readiness.write_text("""# v1.11.0 Release Readiness Evidence\n\n## Evidence identity\n\n```text\ncandidate_version=1.11.0\ncandidate_status=PREPARED_NOT_PUBLISHED\nprevious_public_release=v1.10.0\nprevious_release_commit=756a358f96363f0c377b049adcd87b1991d5aef6\nprevious_release_tree=42c0c8929c4dcfa5b17ff2feb293710d2468ca51\npost_v1_10_freeze_base=8c75fb53cbcdc5f05a74f8377f097c336e5ccce6\npost_v1_10_commit_count=30\naq_campaign=AQ1_THROUGH_AQ14_COMPLETE_CANONICAL_VERIFIED\naq15=UNREGISTERED_NOT_INCLUDED\nar3_ar9=DEFERRED_UNTIL_AFTER_V1_11_0\ntag_created=false\ngithub_release_published=false\n```\n\nThe exact v1.11.0 release SHA/tree/parent/signature and validation run identities are recorded after governed canonical promotion.\n\n## Required qualification\n\nThe candidate must pass the repository's complete revision-specific protected assurance matrix on the exact source head. If the qualified source head is unsigned, the exact qualified tree must then be materialized through the signed-identical-tree lane and promoted only after tree-attested assurance succeeds on the carrier. Canonical `main` must subsequently pass post-merge validate, Required Analysis, Governance, Cross-platform Validation, and dynamic CodeQL.\n\nRelease publication is explicitly authorized by the maintainer in the 2026-09-11 release instruction, but publication cannot precede those technical/governance gates.\n\n## Content boundary\n\nThe release includes every canonical change after v1.10.0 through AQ14, including PRAI, Covenant, protected-governance escalation, whitelist authority hardening, tree-attested promotion assurance, AQ1-AQ14, and the AQ7 tenant-administration parity reference. No AQ15 phase exists in the registered framework. AR-3 through AR-9 remain deferred for the next development cycle.\n""", encoding="utf-8")

    releases_index = ROOT / "docs/reference/releases/README.md"
    index_text = releases_index.read_text(encoding="utf-8")
    candidate_lines = (
        "\nCandidate in qualification: `v1.11.0` Adaptive Assurance and Governance Hardening.\n\n"
        "- [v1.11.0 candidate qualification record](../../releases/v1.11.0-adaptive-assurance-governance-release-candidate.md)\n"
        "- [v1.11.0 release-readiness evidence](../../validation/V1_11_0_RELEASE_READINESS_EVIDENCE.md)\n"
    )
    anchor = "The current public release is [Orchestra v1.10.0](v1.10.0.md).\n"
    if candidate_lines.strip() not in index_text:
        if anchor not in index_text:
            raise RuntimeError("release index baseline drift")
        releases_index.write_text(index_text.replace(anchor, anchor + candidate_lines, 1), encoding="utf-8")

    run("git", "add", "-A")
    run("git", "commit", "-m", "release: prepare v1.11.0 adaptive assurance candidate")

    # Self-retire transport helpers before validation; they are not release content.
    for helper in HELPERS:
        if helper.exists():
            helper.unlink()
    run("git", "add", "-A")
    run("git", "commit", "-m", "chore(release): retire v1.11.0 preparation transport")

    # Focused release checks before the protected CI matrix runs on the PR.
    run("python", "scripts/check_for_updates.py", "--json")
    run("python", "scripts/governance_check.py", "--strict")
    run("python", "tests/behavior/run_tests.py")
    run("python", "-m", "pytest", "tests/runtime", "-q")
    run("git", "diff", "--check", BASE)

    # Ensure all canonical package surfaces agree.
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_for_updates  # type: ignore
    surfaces = check_for_updates.load_version_surfaces(ROOT)
    current = check_for_updates.check_surface_consistency(surfaces)
    if current != VERSION or len(surfaces) != surface_count:
        raise RuntimeError(f"version surface mismatch: {current}, {len(surfaces)} surfaces; expected {surface_count}")
    if load_json(ROOT / "machine/hosts/update-contract.v1.json").get("package_version") != VERSION:
        raise RuntimeError("host-update version mismatch")

    changed = out("git", "diff", "--name-only", BASE, "HEAD").splitlines()
    forbidden = [p for p in changed if p.startswith(".github/workflows/_") or p == "tools/_v1_11_0_release_materializer.py"]
    if forbidden:
        raise RuntimeError(f"temporary helper residue: {forbidden}")

    print("V1_11_0_RELEASE_PREPARATION=PASS")
    print(f"V1_11_0_VERSION_SURFACES={surface_count}_OF_{surface_count}")
    print("V1_11_0_CHANGED_FILES=" + json.dumps(changed))
    run("git", "push", "origin", f"HEAD:{BRANCH}")


if __name__ == "__main__":
    main()
