from __future__ import annotations

import ast
import inspect

from orchestra_runtime import workflow_contracts as legacy_workflow
from orchestra_runtime.domain.orchestration import workflow as domain_workflow


def test_legacy_workflow_receipt_is_domain_symbol() -> None:
    assert legacy_workflow.WORKFLOW_SANITY_SCHEMA_VERSION == domain_workflow.WORKFLOW_SANITY_SCHEMA_VERSION
    assert legacy_workflow.WorkflowSanityReceipt is domain_workflow.WorkflowSanityReceipt


def test_domain_workflow_receipt_preserves_normalization_and_digest() -> None:
    receipt = domain_workflow.WorkflowSanityReceipt(
        command_name=" build ",
        route_id=" route-1 ",
        specialist_id=" ponytail ",
        governance_required=False,
        validation_status=" PASS ",
        validation_rules=(" RULE-1 ",),
        arbiter_disposition=None,
        arbiter_reason_codes=(),
        evidence_refs=(" evidence:1 ",),
        execution_order=(" ROUTING ",),
    )
    assert receipt.command_name == "build"
    assert receipt.route_id == "route-1"
    assert receipt.specialist_id == "ponytail"
    assert receipt.validation_status == "PASS"
    assert receipt.execution_order == ("ROUTING",)
    assert len(receipt.digest) == 64


def test_domain_workflow_contracts_have_only_inward_runtime_dependencies() -> None:
    tree = ast.parse(inspect.getsource(domain_workflow))
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
        "orchestra_runtime.workflow_contracts",
        "orchestra_runtime.machine_contracts",
        "orchestra_runtime.models",
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
