from __future__ import annotations

import ast
import inspect

from orchestra_runtime import governance_kernel as legacy_kernel
from orchestra_runtime.domain.governance import kernel as domain_kernel


def test_legacy_governance_contract_symbols_are_domain_symbols() -> None:
    assert legacy_kernel.GovernanceDecision is domain_kernel.GovernanceDecision
    assert legacy_kernel.TransitionDisposition is domain_kernel.TransitionDisposition
    assert legacy_kernel.ArbiterReasonCode is domain_kernel.ArbiterReasonCode
    assert legacy_kernel.GovernanceDecisionRecord is domain_kernel.GovernanceDecisionRecord
    assert legacy_kernel.ArbiterKernelResult is domain_kernel.ArbiterKernelResult


def test_domain_governance_contracts_preserve_normalization_and_digest() -> None:
    record = domain_kernel.GovernanceDecisionRecord(
        reviewer=" arbiter ",
        project_context=" unit-1 ",
        decision="APPROVED",
        reason=" validated ",
        risks=(" none ",),
        evidence_refs=(" evidence:1 ",),
    )
    assert record.reviewer == "arbiter"
    assert record.project_context == "unit-1"
    assert record.decision is domain_kernel.GovernanceDecision.APPROVED
    assert record.reason == "validated"

    result = domain_kernel.ArbiterKernelResult(
        disposition=domain_kernel.TransitionDisposition.AUTO_CONTINUE,
        reason_codes=(domain_kernel.ArbiterReasonCode.CONTINUATION_READY,),
        input_digest="abc",
    )
    assert result.to_dict()["disposition"] == "AUTO_CONTINUE"
    assert len(result.digest) == 64
    result.assert_claimed_disposition("AUTO_CONTINUE")


def test_domain_governance_kernel_contracts_have_only_inward_runtime_dependencies() -> None:
    tree = ast.parse(inspect.getsource(domain_kernel))
    forbidden_stdlib = {
        "os",
        "pathlib",
        "socket",
        "sqlite3",
        "subprocess",
        "shutil",
        "tempfile",
    }
    forbidden_runtime = {
        "orchestra_runtime.application",
        "orchestra_runtime.infrastructure",
        "orchestra_runtime.entrypoints",
        "orchestra_runtime.machine_contracts",
        "orchestra_runtime.governance_kernel",
        "orchestra_runtime.evidence",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_stdlib
                assert not any(alias.name.startswith(prefix) for prefix in forbidden_runtime)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level == 0:
                assert module.split(".", 1)[0] not in forbidden_stdlib
                assert not any(module.startswith(prefix) for prefix in forbidden_runtime)
            else:
                assert module.startswith("shared.")
