from __future__ import annotations

import ast
import inspect

import pytest

from orchestra_runtime import preexecution as legacy_preexecution
from orchestra_runtime.domain.governance import preexecution as domain_preexecution


def test_legacy_preexecution_policy_symbols_are_domain_symbols() -> None:
    assert legacy_preexecution.ExecutionAction is domain_preexecution.ExecutionAction
    assert legacy_preexecution.PreExecutionConstraint is domain_preexecution.PreExecutionConstraint
    assert legacy_preexecution.PreExecutionReason is domain_preexecution.PreExecutionReason
    assert legacy_preexecution.ExecutionIntent is domain_preexecution.ExecutionIntent
    assert legacy_preexecution.PreExecutionPolicy is domain_preexecution.PreExecutionPolicy


def test_domain_preexecution_policy_preserves_path_and_authority_semantics() -> None:
    intent = domain_preexecution.ExecutionIntent(
        intent_id=" intent-1 ",
        action="FILE_WRITE",
        requested_paths=("src/app.py",),
        evidence_refs=("evidence:1",),
    )
    assert intent.intent_id == "intent-1"
    assert intent.action is domain_preexecution.ExecutionAction.FILE_WRITE
    assert len(intent.digest) == 64

    policy = domain_preexecution.PreExecutionPolicy(
        policy_id=" policy-1 ",
        allowed_actions=("FILE_WRITE",),
        allowed_paths=("src",),
        prohibited_paths=("src/secrets",),
    )
    assert policy.policy_id == "policy-1"
    assert policy.allowed_paths == ("src",)
    assert policy.prohibited_paths == ("src/secrets",)
    assert policy.production_mutation_authorized is False
    assert len(policy.digest) == 64

    with pytest.raises(ValueError, match="repository-relative"):
        domain_preexecution.ExecutionIntent(
            intent_id="intent-2",
            action="FILE_READ",
            requested_paths=("/etc/passwd",),
        )

    with pytest.raises(ValueError, match="inside prohibited path"):
        domain_preexecution.PreExecutionPolicy(
            policy_id="policy-2",
            allowed_actions=("FILE_READ",),
            allowed_paths=("src/secrets",),
            prohibited_paths=("src",),
        )


def test_domain_preexecution_policy_has_only_inward_runtime_dependencies() -> None:
    tree = ast.parse(inspect.getsource(domain_preexecution))
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
        "orchestra_runtime.host_protocol",
        "orchestra_runtime.preexecution",
        "orchestra_runtime.machine_contracts",
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
