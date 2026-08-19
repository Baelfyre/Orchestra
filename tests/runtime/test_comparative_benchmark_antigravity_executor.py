from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_PATH = ROOT / "scripts" / "antigravity_benchmark_executor.py"
RUNNER_PATH = ROOT / "scripts" / "comparative_benchmark_runner.py"
SCHEMA_DIR = ROOT / "machine" / "schemas"

SPEC_EXEC = importlib.util.spec_from_file_location("antigravity_benchmark_executor", EXECUTOR_PATH)
assert SPEC_EXEC is not None and SPEC_EXEC.loader is not None
executor = importlib.util.module_from_spec(SPEC_EXEC)
SPEC_EXEC.loader.exec_module(executor)

SPEC_RUNNER = importlib.util.spec_from_file_location("comparative_benchmark_runner", RUNNER_PATH)
assert SPEC_RUNNER is not None and SPEC_RUNNER.loader is not None
runner = importlib.util.module_from_spec(SPEC_RUNNER)
SPEC_RUNNER.loader.exec_module(runner)

DIGEST = "1" * 64

VALID_CAVEMAN_SKILL_MD = (
    "---\n"
    "name: caveman\n"
    "description: >\n"
    "  Ultra-compressed communication mode. Cuts output tokens 65% (measured) by speaking like caveman\n"
    "  while keeping full technical accuracy. Supports intensity levels: lite, full (default), ultra,\n"
    "  wenyan-lite, wenyan-full, wenyan-ultra.\n"
    "  Use when user says \"caveman mode\", \"talk like caveman\", \"use caveman\", \"less tokens\",\n"
    "  \"be brief\", or invokes /caveman. Also auto-triggers when token efficiency is requested.\n"
    "---\n\n"
    "Respond terse like smart caveman. All technical substance stay. Only fluff die.\n\n"
    "## Persistence\n\n"
    "ACTIVE EVERY RESPONSE. No revert after many turns. No filler drift. Still active if unsure. Off only: \"stop caveman\" / \"normal mode\".\n\n"
    "Default: **full**. Switch: `/caveman lite|full|ultra|wenyan-lite|wenyan-full|wenyan-ultra|off`.\n\n"
    "## Rules\n\n"
    "Drop: articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries (sure/certainly/of course/happy to), hedging. Fragments OK. Short synonyms (big not extensive, fix not \"implement a solution for\"). No tool-call narration, no decorative tables/emoji, no dumping long raw error logs unless asked \u2014 quote shortest decisive line. Standard well-known tech acronyms OK (DB/API/HTTP); never invent new abbreviations (cfg/impl/req/res/fn) \u2014 tokenizer split them same as full word: zero token saved, reader still decode. Full word cheaper AND clearer. No causal arrows (\u2192) either \u2014 own token, save nothing. Technical terms exact. Code blocks unchanged. Errors quoted exact.\n\n"
    "Never drop not/never/no/only/except \u2014 flip meaning worse than any token saved. Numbers, units exact.\n\n"
    "Never ADD word to sound caveman. Compression only \u2014 style never grow output. No inserted pronoun or copula to fake broken grammar: \"when it not\" cost one token more than \"when not\" and say same thing. Keep correct verb form when correct form cost same \u2014 \"sees\" one token, \"see\" one token, so mangle buy nothing and read worse. Same rule as abbreviations and arrows: if caveman phrasing not shorter than plain phrasing, use plain.\n\n"
    "Tool calls: fire direct. No preamble, plan, or progress note before or between calls. After result: next call direct or final answer \u2014 never announce next call. Text before call only to clarify, warn security/irreversible, or resolve ambiguity.\n\n"
    "Preserve user's dominant language exactly \u2014 reply in the language user writes, never switch regardless of example text or multilingual context elsewhere. Compress the style, not the language. Every emitted line in that language \u2014 openings, pre-tool status lines, all \u2014 not just final reply. ALWAYS keep technical terms, code, API names, CLI commands, commit-type keywords (feat/fix/...), and exact error strings verbatim \u2014 unless user explicitly ask for translation.\n\n"
    "'Drop articles' = article languages only. Where small markers carry case/role (particles, postpositions), keep them \u2014 grammar, not filler; compress politeness/filler instead.\n\n"
    "No self-reference. Never name or announce the style. No \"caveman mode on\", \"me caveman think\", no third-person caveman tags. Output caveman-only \u2014 never normal answer plus \"Caveman:\" recap. Exception: user explicitly ask what the mode is.\n\n"
    "Pattern: `[thing] [action] [reason]. [next step].`\n\n"
    "Not: \"Sure! I'd be happy to help you with that. The issue you're experiencing is likely caused by...\"\n"
    "Yes: \"Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:\"\n\n"
    "## Intensity\n\n"
    "| Level | What change |\n"
    "|-------|------------|\n"
    "| **lite** | No filler/hedging. Keep articles + full sentences. Professional but tight |\n"
    "| **full** | Drop articles, fragments OK, short synonyms. Classic caveman. No tool-call narration, no decorative tables/emoji, no long raw error-log dumps unless asked. Standard acronyms OK; no invented abbreviations |\n"
    "| **ultra** | Strip conjunctions when cause-then-effect stay unambiguous. One word when one word enough. State each fact once. NO prose abbreviations (cfg/impl/req/res/fn/auth), NO arrows (X \u2192 Y) \u2014 measured zero token saving under tokenizer, cost decode clarity. Code symbols, function names, API names, error strings: never touch |\n"
    "| **wenyan-lite** | Semi-classical. Drop filler/hedging but keep grammar structure, classical register |\n"
    "| **wenyan-full** | Maximum classical terseness. Fully \u6587\u8a00\u6587. 80-90% character reduction \u2014 chars, not tokens. Classical sentence patterns, verbs precede objects, subjects often omitted, classical particles (\u4e4b/\u4e43/\u70ba/\u5176) |\n"
    "| **wenyan-ultra** | Extreme abbreviation while keeping classical Chinese feel. Maximum compression, ultra terse |\n\n"
    "Example \u2014 \"Why React component re-render?\"\n"
    "- lite: \"Your component re-renders because you create a new object reference each render. Wrap it in `useMemo`.\"\n"
    "- full: \"New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`.\"\n"
    "- ultra: \"Inline obj prop, new ref, re-render. `useMemo`.\"\n"
    "- wenyan-lite: \"\u7d44\u4ef6\u983b\u91cd\u7e6a\uff0c\u4ee5\u6bcf\u7e6a\u65b0\u751f\u5c0d\u8c61\u53c3\u7167\u6545\u3002\u4ee5 useMemo \u5305\u4e4b\u3002\"\n"
    "- wenyan-full: \"\u6bcf\u7e6a\u65b0\u751f\u5c0d\u8c61\u53c3\u7167\uff0c\u6545\u91cd\u7e6a\uff1b\u4ee5 useMemo \u5305\u4e4b\u5247\u514d\u3002\"\n"
    "- wenyan-ultra: \"\u6bb0\u53c3\u7167\u5247\u91cd\u7e6a\u3002useMemo \u5305\u4e4b\u3002\"\n\n".replace("\u6bb0", "\u65b0") +
    "Example \u2014 \"Explain database connection pooling.\"\n"
    "- lite: \"Connection pooling reuses open connections instead of creating new ones per request. Avoids repeated handshake overhead.\"\n"
    "- full: \"Pool reuse open DB connections. No new connection per request. Skip handshake overhead.\"\n"
    "- ultra: \"Pool reuse open DB connections. No per-request handshake.\"\n"
    "- wenyan-full: \"\u6c60\u84c4\u5df2\u958b\u4e4b\u9023\uff0c\u4e0d\u9010\u8acb\u800c\u65b0\u958b\uff0c\u7701\u63e1\u624b\u4e4b\u8cbb\u3002\"\n"
    "- wenyan-ultra: \"\u6c60\u84c4\u9023\uff0c\u514d\u9010\u8acb\u65b0\u958b\uff0c\u7701\u63e1\u624b\u3002\"\n\n"
    "Classical chars = wenyan modes only. Never swap a word to a classical char to shrink at non-wenyan levels.\n\n"
    "## Auto-Clarity\n\n"
    "Drop caveman when:\n"
    "- Security warnings\n"
    "- Irreversible action confirmations\n"
    "- Multi-step sequences where fragment order or omitted conjunctions risk misread\n"
    "- Compression itself creates technical ambiguity (e.g., `\"migrate table drop column backup first\"` \u2014 order unclear without articles/conjunctions)\n"
    "- User asks to clarify or repeats question\n\n"
    "Resume caveman after clear part done.\n\n"
    "Example shows FORMAT only \u2014 write warning in session language, not example's.\n\n"
    "Example \u2014 destructive op:\n"
    "> **Warning:** This will permanently delete all rows in the `users` table and cannot be undone.\n"
    "> ```sql\n"
    "> DROP TABLE users;\n"
    "> ```\n"
    "> Caveman resume. Verify backup exist first.\n\n"
    "## Boundaries\n\n"
    "Persisted outside chat: write normal prose \u2014 code, comments, commits, docs, issue/PR/MR/defect/ticket/bug-report text, memory files, third-party messages (/caveman-compress exempt). \"Open a defect\" or \"file a bug\" mean the same as \"open issue\": body go to other humans, so body normal English. \"stop caveman\" or \"normal mode\": revert. Level persist until changed or session end."
)


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _validate_result_schema(value: dict[str, Any]) -> None:
    schema = _load_schema("comparative-benchmark-executor-result.schema.json")
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(value)


def _base_request(request_id: str = "req-001", communication_mode: str = "DEFAULT", **task_payload_kwargs: Any) -> dict[str, Any]:
    return {
        "schema_version": "orchestra.comparative-benchmark-executor-request.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "fixture-b3-calibration",
        "experiment_kind": "MURMURS_ISOLATED",
        "stage": "CALIBRATION",
        "request_id": request_id,
        "task_id": "task-01",
        "task_class": "SINGLE_DOMAIN",
        "repetition_index": 1,
        "execution_order_index": 1,
        "arm": {
            "arm_id": communication_mode.lower(),
            "topology_candidate_id": "fixed-topology",
            "topology_class": "FIXED_DETERMINISTIC",
            "topology_digest": DIGEST,
            "communication_mode": communication_mode,
        },
        "control_identity": {
            "orchestra_revision": "06ede6bde3aa7682194950ba9130ba52e4fb0ea5",
            "repository_revision": "test-repo-rev",
            "starting_state_digest": DIGEST,
            "task_prompt_digest": DIGEST,
            "system_instruction_digest": DIGEST,
            "provider": "antigravity",
            "model": "gemini-3.7-flash-high",
            "model_revision": None,
            "reasoning_setting": "default",
            "temperature": 0.0,
            "tool_access_digest": DIGEST,
            "specialist_set_digest": DIGEST,
            "required_specialist_set_digest": DIGEST,
            "authority_digest": DIGEST,
            "governance_digest": DIGEST,
            "validation_contract_digest": DIGEST,
            "environment_digest": DIGEST,
            "retry_policy_digest": DIGEST,
            "resource_budget_digest": DIGEST,
        },
        "task_payload": dict(task_payload_kwargs),
        "task_payload_digest": DIGEST,
        "a5_evaluation": None,
        "murmurs_evaluation": {"same_counter_identity_for_token_delta": True},
        "interaction_evaluation": None,
    }


def _mock_host_envelope(
    status: str = "SUCCESS",
    input_tokens: int = 1500,
    output_tokens: int = 400,
    thinking_tokens: int = 120,
    cache_read_tokens: int = 300,
    total_tokens: int = 2320,
    model: str = "gemini-3.7-flash-high",
    cli_version: str = "1.1.15",
    task_completed: bool = True,
    validation_passed: bool = True,
    governance_valid: bool = True,
    response: str | None = "Sample structured response payload",
) -> dict[str, Any]:
    envelope: dict[str, Any] = {
        "status": status,
        "model": model,
        "cli_version": cli_version,
        "useG1Credits": False,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "thinking_tokens": thinking_tokens,
            "cache_read_tokens": cache_read_tokens,
            "total_tokens": total_tokens,
        },
        "task_completed": task_completed,
        "validation_passed": validation_passed,
        "governance_valid": governance_valid,
    }
    if response is not None:
        envelope["response"] = response
    return envelope


def _create_mock_settings(tmp_path: Path, use_g1_credits: Any = False) -> Path:
    settings_file = tmp_path / "settings.json"
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if use_g1_credits is not None:
        data["useG1Credits"] = use_g1_credits
    settings_file.write_text(json.dumps(data), encoding="utf-8")
    return settings_file


def test_01_valid_antigravity_usage_maps_to_host_reported_tokens() -> None:
    req = _base_request(raw_host_output=_mock_host_envelope(input_tokens=1000, output_tokens=250))
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["tokens"]["source"] == "HOST_REPORTED"
    assert res["tokens"]["counter_id"] == "antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high"
    assert res["tokens"]["input_tokens"] == 1000
    assert res["tokens"]["output_tokens"] == 250


def test_02_thinking_tokens_maps_to_reasoning_tokens() -> None:
    req = _base_request(raw_host_output=_mock_host_envelope(thinking_tokens=180))
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["tokens"]["reasoning_tokens"] == 180


def test_03_cache_read_tokens_maps_to_cached_input_tokens() -> None:
    req = _base_request(raw_host_output=_mock_host_envelope(cache_read_tokens=450))
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["tokens"]["cached_input_tokens"] == 450


def test_04_total_tokens_remains_raw_evidence_only() -> None:
    envelope = _mock_host_envelope(total_tokens=9999)
    req = _base_request(raw_host_output=envelope)
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["raw_evidence"]["total_tokens"] == 9999
    assert res["raw_evidence"]["outer_envelope"]["usage"]["total_tokens"] == 9999
    assert res["tokens"]["fresh_billable_tokens"] is None


def test_05_fresh_billable_tokens_remains_null() -> None:
    req = _base_request(raw_host_output=_mock_host_envelope(input_tokens=500, output_tokens=100))
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["tokens"]["fresh_billable_tokens"] is None


def test_06_provider_cost_remains_unavailable() -> None:
    req = _base_request(raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["cost"]["source"] == "UNAVAILABLE"
    assert res["cost"]["amount"] is None
    assert res["cost"]["currency"] is None


def test_07_missing_usage_becomes_invalid_run_measurement_capture_failure() -> None:
    envelope = _mock_host_envelope()
    del envelope["usage"]
    req = _base_request(raw_host_output=envelope)
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert res["tokens"]["source"] == "UNAVAILABLE"


def test_08_missing_input_or_output_counters_becomes_invalid_run() -> None:
    envelope_no_input = _mock_host_envelope()
    del envelope_no_input["usage"]["input_tokens"]
    req1 = _base_request(raw_host_output=envelope_no_input)
    res1 = executor.execute_request(req1)
    _validate_result_schema(res1)
    assert res1["outcome"]["status"] == "INVALID_RUN"
    assert res1["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    envelope_no_output = _mock_host_envelope()
    del envelope_no_output["usage"]["output_tokens"]
    req2 = _base_request(raw_host_output=envelope_no_output)
    res2 = executor.execute_request(req2)
    _validate_result_schema(res2)
    assert res2["outcome"]["status"] == "INVALID_RUN"
    assert res2["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_09_malformed_outer_json_becomes_invalid_run() -> None:
    req = _base_request(raw_host_output="NOT_VALID_JSON_<<<>>>")
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_10_antigravity_success_does_not_automatically_set_task_outcome_pass() -> None:
    envelope_val_fail = _mock_host_envelope(
        status="SUCCESS",
        task_completed=True,
        validation_passed=False,
        governance_valid=True,
    )
    req = _base_request(raw_host_output=envelope_val_fail)
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "FAIL"
    assert res["outcome"]["invalid_reason"] is None
    assert res["outcome"]["validation_passed"] is False
    assert res["tokens"]["source"] == "HOST_REPORTED"

    envelope_inc = _mock_host_envelope(
        status="SUCCESS",
        task_completed=False,
        validation_passed=True,
        governance_valid=True,
    )
    res2 = executor.execute_request(_base_request(raw_host_output=envelope_inc))
    _validate_result_schema(res2)
    assert res2["outcome"]["status"] == "FAIL"
    assert res2["outcome"]["task_completed"] is False


def test_11_host_success_without_independent_evidence_cannot_produce_pass() -> None:
    bare_envelope = {
        "status": "SUCCESS",
        "usage": {
            "input_tokens": 1200,
            "output_tokens": 350,
            "thinking_tokens": 50,
            "cache_read_tokens": 100,
            "total_tokens": 1700,
        },
        "response": "Completed the request successfully.",
    }
    req = _base_request(raw_host_output=bare_envelope)
    req["task_payload"].pop("task_completed", None)
    req["task_payload"].pop("validation_passed", None)
    req["task_payload"].pop("governance_valid", None)

    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "FAIL"
    assert res["outcome"]["invalid_reason"] is None
    assert res["outcome"]["task_completed"] is False
    assert res["outcome"]["validation_passed"] is False
    assert res["outcome"]["governance_valid"] is False
    assert res["tokens"]["source"] == "HOST_REPORTED"
    assert res["tokens"]["input_tokens"] == 1200
    assert res["tokens"]["output_tokens"] == 350


def test_12_counter_identity_is_deterministic() -> None:
    cid1 = executor.compute_counter_id()
    cid2 = executor.compute_counter_id("1.1.15", "gemini-3.7-flash-high", "json-usage")
    assert cid1 == "antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high"
    assert cid1 == cid2 == executor.DEFAULT_COUNTER_ID


def test_13_changed_cli_or_model_identity_changes_counter_identity() -> None:
    base_cid = executor.DEFAULT_COUNTER_ID

    cid_cli_change = executor.compute_counter_id(cli_version="1.2.0")
    assert cid_cli_change != base_cid
    assert cid_cli_change == "antigravity-cli-1.2.0:json-usage:gemini-3.7-flash-high"

    cid_model_change = executor.compute_counter_id(model="gemini-2.5-pro")
    assert cid_model_change != base_cid
    assert cid_model_change == "antigravity-cli-1.1.15:json-usage:gemini-2.5-pro"

    envelope_drift = _mock_host_envelope(cli_version="1.2.0")
    res = executor.execute_request(_base_request(raw_host_output=envelope_drift))
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_14_no_live_antigravity_invocation_occurs_during_tests() -> None:
    called = []

    def fake_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        called.append(cmd)
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req, runner_fn=fake_runner)
    assert len(called) == 0
    assert res["outcome"]["status"] == "PASS"


def test_15_corrupted_starting_state_fails_closed() -> None:
    req = _base_request(corrupted_starting_state=True, raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req)
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"

    req2 = _base_request(raw_host_output=_mock_host_envelope())
    req2["control_identity"]["starting_state_digest"] = ""
    res2 = executor.execute_request(req2)
    _validate_result_schema(res2)
    assert res2["outcome"]["status"] == "INVALID_RUN"
    assert res2["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"


def test_16_model_mismatch_fails_closed() -> None:
    req = _base_request(raw_host_output=_mock_host_envelope())
    req["control_identity"]["model"] = "unpinned-model-variant"
    res = executor.execute_request(req)
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    envelope_wrong_model = _mock_host_envelope(model="unpinned-model-variant")
    req2 = _base_request(raw_host_output=envelope_wrong_model)
    res2 = executor.execute_request(req2)
    _validate_result_schema(res2)
    assert res2["outcome"]["status"] == "INVALID_RUN"
    assert res2["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_17_live_argv_construction_and_no_stdin_prompt(tmp_path: Path) -> None:
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    captured_calls: list[dict[str, Any]] = []

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        captured_calls.append({"cmd": cmd, "prompt": prompt})
        envelope = _mock_host_envelope(
            task_completed=True,
            validation_passed=True,
            governance_valid=True,
        )
        return (0, json.dumps(envelope), "")

    test_prompt = "Refactor the authentication middleware."
    req = _base_request(prompt=test_prompt)
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert len(captured_calls) == 1
    call_info = captured_calls[0]
    cmd = call_info["cmd"]

    expected_cmd = [
        "agy",
        "--model",
        "gemini-3.7-flash-high",
        "-p",
        test_prompt,
        "--output-format",
        "json",
    ]
    assert cmd == expected_cmd
    assert "-p" in cmd
    assert cmd[cmd.index("-p") + 1] == test_prompt
    assert "--no-use-g1-credits" not in cmd
    assert res["outcome"]["status"] == "PASS"


def test_18_preflight_accepts_exact_cli_version_1_1_15(tmp_path: Path) -> None:
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        assert cmd == ["agy", "--version"]
        return (0, "antigravity-cli 1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sample prompt")
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is True
    assert res["outcome"]["status"] == "PASS"
    assert res["raw_evidence"]["cli_version"] == "1.1.15"


def test_19_preflight_fails_closed_on_different_cli_version(tmp_path: Path) -> None:
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.2.0\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sample prompt")
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is False
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert "1.2.0" in str(res["raw_evidence"]["detail"])


def test_20_preflight_accepts_explicit_use_g1_credits_false(tmp_path: Path) -> None:
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sample prompt")
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is True
    assert res["outcome"]["status"] == "PASS"


def test_21_preflight_fails_closed_on_use_g1_credits_true(tmp_path: Path) -> None:
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=True)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sample prompt")
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is False
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert "useG1Credits" in str(res["raw_evidence"]["detail"])


def test_22_preflight_fails_closed_on_malformed_or_missing_settings(tmp_path: Path) -> None:
    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    missing_settings = tmp_path / "non_existent_settings.json"
    req1 = _base_request(prompt="Sample prompt")
    res1 = executor.execute_request(
        req1,
        expected_cli_version="1.1.15",
        settings_path=missing_settings,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res1)
    assert res1["outcome"]["status"] == "INVALID_RUN"
    assert res1["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    malformed_settings = tmp_path / "bad_settings.json"
    malformed_settings.write_text("{not-valid-json", encoding="utf-8")
    req2 = _base_request(prompt="Sample prompt")
    res2 = executor.execute_request(
        req2,
        expected_cli_version="1.1.15",
        settings_path=malformed_settings,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res2)
    assert res2["outcome"]["status"] == "INVALID_RUN"
    assert res2["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    non_object_settings = tmp_path / "list_settings.json"
    non_object_settings.write_text("[1, 2, 3]", encoding="utf-8")
    req3 = _base_request(prompt="Sample prompt")
    res3 = executor.execute_request(
        req3,
        expected_cli_version="1.1.15",
        settings_path=non_object_settings,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res3)
    assert res3["outcome"]["status"] == "INVALID_RUN"
    assert res3["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_23_provenance_semantics_explicitly_preserved() -> None:
    envelope = _mock_host_envelope()
    del envelope["model"]
    del envelope["cli_version"]

    req = _base_request(raw_host_output=envelope)
    res = executor.execute_request(req)
    _validate_result_schema(res)

    raw_ev = res["raw_evidence"]
    assert raw_ev["expected_cli_version"] == "1.1.15"
    assert raw_ev["expected_cli_version_provenance"]["source"] == "DEFAULT_QUALIFIED_HOST"
    assert raw_ev["observed_cli_version"] == "1.1.15"
    assert raw_ev["cli_version_provenance"]["source"] == "HOST_REPORTED_JSON_USAGE"
    assert raw_ev["cli_version_provenance"]["value"] == "1.1.15"
    assert raw_ev["model_provenance"]["source"] == "PINNED_COMMAND_ARGUMENT"
    assert raw_ev["model_provenance"]["value"] == "gemini-3.7-flash-high"
    assert raw_ev["usage_provenance"]["source"] == "HOST_REPORTED_JSON_USAGE"
    assert raw_ev["counter_id_provenance"]["provenance"] == "ORCHESTRA_ASSIGNED_MEASUREMENT_SURFACE"
    assert raw_ev["counter_id_provenance"]["vendor_assigned_claim"] is False
    assert raw_ev["counter_id_provenance"]["identifier"] == "antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high"


def test_24_response_bytes_captured_from_response_field() -> None:
    response_text = "Here is the refactored code and summary."
    envelope = _mock_host_envelope(response=response_text)
    envelope.pop("content", None)

    req = _base_request(raw_host_output=envelope)
    res = executor.execute_request(req)
    _validate_result_schema(res)

    expected_bytes = len(response_text.encode("utf-8"))
    assert res["communication"]["user_visible_bytes"] == expected_bytes
    assert res["communication"]["user_visible_bytes"] > 0


def test_25_runner_integration_with_antigravity_executor(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "schema_version": "orchestra.comparative-benchmark-manifest.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "fixture-b3-1-integration",
        "experiment_kind": "MURMURS_ISOLATED",
        "stage": "CALIBRATION",
        "randomization_seed": 12345,
        "repetitions_per_arm": 1,
        "executor_timeout_seconds": 30,
        "common_control_identity": {
            "orchestra_revision": "06ede6bde3aa7682194950ba9130ba52e4fb0ea5",
            "repository_revision": "test-repo-rev",
            "starting_state_digest": DIGEST,
            "task_prompt_digest": DIGEST,
            "system_instruction_digest": DIGEST,
            "provider": "antigravity",
            "model": "gemini-3.7-flash-high",
            "model_revision": None,
            "reasoning_setting": "default",
            "temperature": 0.0,
            "tool_access_digest": DIGEST,
            "specialist_set_digest": DIGEST,
            "required_specialist_set_digest": DIGEST,
            "authority_digest": DIGEST,
            "governance_digest": DIGEST,
            "validation_contract_digest": DIGEST,
            "environment_digest": DIGEST,
            "retry_policy_digest": DIGEST,
            "resource_budget_digest": DIGEST,
        },
        "arms": [
            {"arm_id": "default", "topology_candidate_id": "fixed-top", "topology_class": "FIXED_DETERMINISTIC", "topology_digest": DIGEST, "communication_mode": "DEFAULT"},
            {"arm_id": "caveman", "topology_candidate_id": "fixed-top", "topology_class": "FIXED_DETERMINISTIC", "topology_digest": DIGEST, "communication_mode": "CAVEMAN"},
            {"arm_id": "murmurs", "topology_candidate_id": "fixed-top", "topology_class": "FIXED_DETERMINISTIC", "topology_digest": DIGEST, "communication_mode": "MURMURS"},
        ],
        "tasks": [
            {
                "task_id": "task-01",
                "task_class": "SINGLE_DOMAIN",
                "starting_state_digest": DIGEST,
                "task_prompt_digest": DIGEST,
                "task_payload": {
                    "raw_host_output": _mock_host_envelope(input_tokens=1200, output_tokens=300),
                    "caveman_policy_content": VALID_CAVEMAN_SKILL_MD,
                },
            }
        ],
        "a5_evaluation": None,
        "murmurs_evaluation": {"same_counter_identity_for_token_delta": True},
        "interaction_evaluation": None,
        "preregistration_digest": None,
        "benefit_thresholds": None,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    output_dir = tmp_path / "bench-out"

    cmd = [sys.executable, str(EXECUTOR_PATH)]
    rc = runner.run(manifest_path, cmd, output_dir)
    assert rc == 0

    plan = json.loads((output_dir / "plan.json").read_text(encoding="utf-8"))
    assert len(plan["entries"]) == 3

    run_files = sorted((output_dir / "runs").glob("*.json"))
    assert len(run_files) == 3

    for r_file in run_files:
        run_record = json.loads(r_file.read_text(encoding="utf-8"))
        schema = _load_schema("comparative-benchmark-run.schema.json")
        jsonschema.Draft202012Validator(schema).validate(run_record)
        assert run_record["tokens"]["source"] == "HOST_REPORTED"
        assert run_record["tokens"]["counter_id"] == "antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high"
        assert run_record["tokens"]["fresh_billable_tokens"] is None
        assert run_record["outcome"]["status"] == "PASS"

    experiment = json.loads((output_dir / "experiment.json").read_text(encoding="utf-8"))
    exp_schema = _load_schema("comparative-benchmark-experiment.schema.json")
    jsonschema.Draft202012Validator(exp_schema).validate(experiment)
    assert experiment["status"] == "COMPLETE"
    assert experiment["conclusion"] == "MEASUREMENT_CALIBRATED"


# B3.1.2 Communication Arm Operationalization Tests (20 Required Invariants)


def test_26_default_binds_normal_no_compression_treatment() -> None:
    # Requirement 1: DEFAULT binds NORMAL/no-compression treatment.
    prompt_text = "Implement deterministic sorting on table rows."
    req = _base_request(communication_mode="DEFAULT", prompt=prompt_text, raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req)
    _validate_result_schema(res)

    raw_ev = res["raw_evidence"]
    assert raw_ev["communication_mode"] == "DEFAULT"
    assert raw_ev["presentation_mode"] == "NORMAL"
    assert raw_ev["treatment_effective"] is True
    assert raw_ev["treatment_provenance"]["source"] == "ORCHESTRA_CANONICAL_PRESENTATION"
    assert raw_ev["treatment_provenance"]["presentation_mode"] == "NORMAL"
    assert raw_ev["task_prompt_digest"] == executor.digest_json(prompt_text)
    assert raw_ev["effective_prompt_or_policy_digest"] == executor.digest_json(prompt_text)


def test_27_caveman_binds_exact_pinned_policy() -> None:
    # Requirement 2: CAVEMAN binds only the exact pinned external output policy.
    # Checks blob bd22d86b32e4a99e09ff7482a35509faac7a6f65 and rev ae405e872270acc57484693612ae038b16c8f6cd
    blob_hash = executor.compute_git_blob_hash(VALID_CAVEMAN_SKILL_MD.encode("utf-8"))
    assert blob_hash == executor.PINNED_CAVEMAN_BLOB

    prompt_text = "Refactor telemetry handler."
    req = _base_request(
        communication_mode="CAVEMAN",
        prompt=prompt_text,
        caveman_policy_content=VALID_CAVEMAN_SKILL_MD,
        raw_host_output=_mock_host_envelope(),
    )
    res = executor.execute_request(req)
    _validate_result_schema(res)

    raw_ev = res["raw_evidence"]
    assert raw_ev["communication_mode"] == "CAVEMAN"
    assert raw_ev["presentation_mode"] == "NORMAL"
    assert raw_ev["treatment_effective"] is True

    prov = raw_ev["treatment_provenance"]
    assert prov["source"] == "EXTERNAL_COMPARATIVE_BASELINE"
    assert prov["external_repository"] == "JuliusBrussee/caveman"
    assert prov["pinned_revision"] == "ae405e872270acc57484693612ae038b16c8f6cd"
    assert prov["skill_path"] == "skills/caveman/SKILL.md"
    assert prov["pinned_blob_identity"] == "bd22d86b32e4a99e09ff7482a35509faac7a6f65"
    assert prov["loaded_policy_digest"] == executor.digest_json(VALID_CAVEMAN_SKILL_MD)

    assert raw_ev["task_prompt_digest"] == executor.digest_json(prompt_text)
    expected_effective = f"[COMMUNICATION POLICY]\n{VALID_CAVEMAN_SKILL_MD.strip()}\n\n[TASK]\n{prompt_text}"
    assert raw_ev["effective_prompt_or_policy_digest"] == executor.digest_json(expected_effective)


def test_28_caveman_revision_mismatch_fails_closed() -> None:
    # Requirement 3: CAVEMAN revision mismatch fails closed.
    req = _base_request(
        communication_mode="CAVEMAN",
        prompt="Sample task",
        caveman_policy_content=VALID_CAVEMAN_SKILL_MD,
        caveman_repo_revision="0000000000000000000000000000000000000000",
        raw_host_output=_mock_host_envelope(),
    )
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE"
    assert "revision mismatch" in str(res["raw_evidence"]["detail"]["error"])


def test_29_caveman_blob_mismatch_fails_closed() -> None:
    # Requirement 4: CAVEMAN blob mismatch fails closed.
    tampered_policy = VALID_CAVEMAN_SKILL_MD + "\n# Extra tampered line"
    req = _base_request(
        communication_mode="CAVEMAN",
        prompt="Sample task",
        caveman_policy_content=tampered_policy,
        raw_host_output=_mock_host_envelope(),
    )
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE"
    assert "blob mismatch" in str(res["raw_evidence"]["detail"]["error"])


def test_30_caveman_missing_policy_fails_closed(tmp_path: Path) -> None:
    # Requirement 5: CAVEMAN missing policy fails closed.
    non_existent = tmp_path / "missing_caveman_skill.md"
    req = _base_request(
        communication_mode="CAVEMAN",
        prompt="Sample task",
        caveman_policy_path=non_existent,
        raw_host_output=_mock_host_envelope(),
    )
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE"


def test_31_caveman_compress_or_proxy_is_rejected() -> None:
    # Requirement 6: caveman-compress/proxy is not selected by B3.
    prohibited_content = "---\nname: caveman-compress\n---\nCompress memory files."
    req = _base_request(
        communication_mode="CAVEMAN",
        prompt="Sample task",
        caveman_policy_content=prohibited_content,
        raw_host_output=_mock_host_envelope(),
    )
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE"


def test_32_murmurs_binds_canonical_presentation_mode() -> None:
    # Requirement 7: MURMURS binds canonical PresentationMode.MURMURS.
    prompt_text = "Audit cryptographic keystore."
    req = _base_request(
        communication_mode="MURMURS",
        prompt=prompt_text,
        raw_host_output=_mock_host_envelope(),
    )
    res = executor.execute_request(req)
    _validate_result_schema(res)

    raw_ev = res["raw_evidence"]
    assert raw_ev["communication_mode"] == "MURMURS"
    assert raw_ev["presentation_mode"] == "MURMURS"
    assert raw_ev["treatment_effective"] is True
    assert raw_ev["task_prompt_digest"] == executor.digest_json(prompt_text)
    assert raw_ev["effective_prompt_or_policy_digest"] == executor.digest_json(prompt_text)


def test_33_murmurs_policy_and_vocabulary_identity_recorded() -> None:
    # Requirement 8: Murmurs policy/vocabulary identity is recorded.
    req = _base_request(
        communication_mode="MURMURS",
        prompt="Audit cryptographic keystore.",
        raw_host_output=_mock_host_envelope(),
    )
    res = executor.execute_request(req)
    _validate_result_schema(res)

    prov = res["raw_evidence"]["treatment_provenance"]
    assert prov["source"] == "ORCHESTRA_CANONICAL_PRESENTATION"
    assert prov["presentation_mode"] == "MURMURS"
    assert "presentation_policy_digest" in prov
    assert len(prov["presentation_policy_digest"]) == 64
    assert "murmurs_vocabulary_digest" in prov
    assert len(prov["murmurs_vocabulary_digest"]) == 64


def test_34_murmurs_cannot_silently_become_default(tmp_path: Path) -> None:
    # Requirement 9: MURMURS cannot silently become DEFAULT (missing presentation contracts fail closed).
    empty_root = tmp_path / "empty_repo"
    empty_root.mkdir()
    req = _base_request(
        communication_mode="MURMURS",
        prompt="Sample task",
        raw_host_output=_mock_host_envelope(),
    )
    res = executor.execute_request(req, presentation_root=empty_root)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_35_distinct_treatment_identities_across_three_arms() -> None:
    # Requirement 10: DEFAULT/CAVEMAN/MURMURS produce distinct treatment identities.
    task_prompt = "Verify distributed consensus algorithm."

    req_default = _base_request(communication_mode="DEFAULT", prompt=task_prompt, raw_host_output=_mock_host_envelope())
    res_default = executor.execute_request(req_default)
    _validate_result_schema(res_default)

    req_caveman = _base_request(
        communication_mode="CAVEMAN",
        prompt=task_prompt,
        caveman_policy_content=VALID_CAVEMAN_SKILL_MD,
        raw_host_output=_mock_host_envelope(),
    )
    res_caveman = executor.execute_request(req_caveman)
    _validate_result_schema(res_caveman)

    req_murmurs = _base_request(communication_mode="MURMURS", prompt=task_prompt, raw_host_output=_mock_host_envelope())
    res_murmurs = executor.execute_request(req_murmurs)
    _validate_result_schema(res_murmurs)

    id_default = res_default["raw_evidence"]["treatment_identity"]
    id_caveman = res_caveman["raw_evidence"]["treatment_identity"]
    id_murmurs = res_murmurs["raw_evidence"]["treatment_identity"]

    assert id_default != id_caveman
    assert id_default != id_murmurs
    assert id_caveman != id_murmurs


def test_36_underlying_task_prompt_digest_remains_identical_across_arms() -> None:
    # Requirement 11: Underlying task prompt digest remains identical across arms.
    task_prompt = "Refactor parser to handle UTF-8 symbols cleanly."
    expected_prompt_digest = executor.digest_json(task_prompt)

    req_def = _base_request(communication_mode="DEFAULT", prompt=task_prompt, raw_host_output=_mock_host_envelope())
    res_def = executor.execute_request(req_def)

    req_cav = _base_request(
        communication_mode="CAVEMAN",
        prompt=task_prompt,
        caveman_policy_content=VALID_CAVEMAN_SKILL_MD,
        raw_host_output=_mock_host_envelope(),
    )
    res_cav = executor.execute_request(req_cav)

    req_mur = _base_request(communication_mode="MURMURS", prompt=task_prompt, raw_host_output=_mock_host_envelope())
    res_mur = executor.execute_request(req_mur)

    assert res_def["raw_evidence"]["task_prompt_digest"] == expected_prompt_digest
    assert res_cav["raw_evidence"]["task_prompt_digest"] == expected_prompt_digest
    assert res_mur["raw_evidence"]["task_prompt_digest"] == expected_prompt_digest

    # But Caveman effective prompt digest differs because it contains the policy
    assert res_cav["raw_evidence"]["effective_prompt_or_policy_digest"] != expected_prompt_digest
    assert res_def["raw_evidence"]["effective_prompt_or_policy_digest"] == expected_prompt_digest


def test_37_topology_identity_remains_identical_across_arms() -> None:
    # Requirement 12: Topology identity remains identical across arms.
    top_cand = "fixed-topology-b3"
    top_digest = executor.digest_json({"topology": "deterministic-v1"})

    for mode in ("DEFAULT", "CAVEMAN", "MURMURS"):
        req = _base_request(
            communication_mode=mode,
            caveman_policy_content=VALID_CAVEMAN_SKILL_MD if mode == "CAVEMAN" else None,
            raw_host_output=_mock_host_envelope(),
        )
        req["arm"]["topology_candidate_id"] = top_cand
        req["arm"]["topology_digest"] = top_digest

        res = executor.execute_request(req)
        _validate_result_schema(res)
        assert res["raw_evidence"]["topology_candidate_id"] == top_cand
        assert res["raw_evidence"]["topology_digest"] == top_digest


def test_38_unknown_communication_mode_fails_closed() -> None:
    # Requirement 13: Unknown communication mode fails closed.
    req = _base_request(communication_mode="UNSUPPORTED_MODE", raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_39_treatment_activation_evidence_is_present() -> None:
    # Requirement 14: Treatment activation evidence is present in raw_evidence.
    req = _base_request(communication_mode="DEFAULT", raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req)
    _validate_result_schema(res)

    raw_ev = res["raw_evidence"]
    assert "treatment_effective" in raw_ev
    assert "treatment_identity" in raw_ev
    assert "treatment_provenance" in raw_ev
    assert "task_prompt_digest" in raw_ev
    assert "effective_prompt_or_policy_digest" in raw_ev


def test_40_no_live_provider_subprocess_executes_in_tests() -> None:
    # Requirement 15: No live provider subprocess executes in tests.
    call_records: list[Any] = []

    def mock_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        call_records.append(cmd)
        return 0, json.dumps(_mock_host_envelope()), ""

    req = _base_request(communication_mode="DEFAULT", raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req, runner_fn=mock_runner)
    assert len(call_records) == 0
    assert res["outcome"]["status"] == "PASS"


def test_41_stream_json_transport_supported_across_arms() -> None:
    # Requirement 16: If stream-json is implemented, all three arms use the same transport.
    stream_lines = [
        json.dumps({"type": "step_update", "event_kind": "TOOL_STARTED", "content": "Running test"}),
        json.dumps({"type": "step_update", "event_kind": "TOOL_COMPLETED", "content": "Completed test"}),
        json.dumps(_mock_host_envelope(input_tokens=800, output_tokens=200, total_tokens=1000)),
    ]
    stream_payload = "\n".join(stream_lines)

    for mode in ("DEFAULT", "CAVEMAN", "MURMURS"):
        req = _base_request(
            communication_mode=mode,
            transport="stream-json",
            caveman_policy_content=VALID_CAVEMAN_SKILL_MD if mode == "CAVEMAN" else None,
            raw_host_output=stream_payload,
        )
        res = executor.execute_request(req)
        _validate_result_schema(res)

        assert res["tokens"]["source"] == "HOST_REPORTED"
        assert res["tokens"]["counter_id"] == "antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high"
        assert res["raw_evidence"]["transport"] == "stream-json-usage"
        assert res["outcome"]["status"] == "PASS"


def test_42_stream_json_parser_preserves_raw_event_sequence() -> None:
    # Requirement 17: Stream-json parser preserves raw event sequence.
    events = [
        {"type": "step_update", "event_kind": "TOOL_STARTED", "content": "step 1"},
        {"type": "step_update", "event_kind": "TOOL_COMPLETED", "content": "step 2"},
        _mock_host_envelope(input_tokens=900, output_tokens=300),
    ]
    req = _base_request(
        communication_mode="DEFAULT",
        transport="stream-json",
        raw_host_output=events,
    )
    res = executor.execute_request(req)
    _validate_result_schema(res)

    assert "stream_events" in res["raw_evidence"]
    assert len(res["raw_evidence"]["stream_events"]) == 3
    assert res["raw_evidence"]["stream_events"][0]["content"] == "step 1"
    assert res["raw_evidence"]["stream_events"][1]["content"] == "step 2"


def test_43_stream_json_terminal_native_usage_counters_map_correctly() -> None:
    # Requirement 18: Terminal native usage counters map correctly in stream-json.
    events = [
        {"type": "step_update", "event_kind": "EXECUTION_HEARTBEAT"},
        _mock_host_envelope(
            input_tokens=1400,
            output_tokens=350,
            thinking_tokens=110,
            cache_read_tokens=220,
            total_tokens=2080,
        ),
    ]
    req = _base_request(
        communication_mode="DEFAULT",
        transport="stream-json",
        raw_host_output=events,
    )
    res = executor.execute_request(req)
    _validate_result_schema(res)

    tok = res["tokens"]
    assert tok["source"] == "HOST_REPORTED"
    assert tok["counter_id"] == "antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high"
    assert tok["input_tokens"] == 1400
    assert tok["output_tokens"] == 350
    assert tok["reasoning_tokens"] == 110
    assert tok["cached_input_tokens"] == 220
    assert tok["fresh_billable_tokens"] is None
    assert res["raw_evidence"]["total_tokens"] == 2080


def test_44_json_and_stream_json_counter_identities_cannot_be_mixed(tmp_path: Path) -> None:
    # Requirement 19: json and stream-json counter identities cannot be mixed.
    cid_json = executor.compute_counter_id(transport="json-usage")
    cid_stream = executor.compute_counter_id(transport="stream-json-usage")
    assert cid_json != cid_stream
    assert cid_json == "antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high"
    assert cid_stream == "antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high"

    # Runner cross-run invariant check fails if counter_id differs across runs
    manifest_path = tmp_path / "mixed_manifest.json"
    manifest = {
        "schema_version": "orchestra.comparative-benchmark-manifest.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "fixture-b3-mixed-counter",
        "experiment_kind": "MURMURS_ISOLATED",
        "stage": "CALIBRATION",
        "randomization_seed": 12345,
        "repetitions_per_arm": 1,
        "executor_timeout_seconds": 30,
        "common_control_identity": {
            "orchestra_revision": "06ede6bde3aa7682194950ba9130ba52e4fb0ea5",
            "repository_revision": "test-repo-rev",
            "starting_state_digest": DIGEST,
            "task_prompt_digest": DIGEST,
            "system_instruction_digest": DIGEST,
            "provider": "antigravity",
            "model": "gemini-3.7-flash-high",
            "model_revision": None,
            "reasoning_setting": "default",
            "temperature": 0.0,
            "tool_access_digest": DIGEST,
            "specialist_set_digest": DIGEST,
            "required_specialist_set_digest": DIGEST,
            "authority_digest": DIGEST,
            "governance_digest": DIGEST,
            "validation_contract_digest": DIGEST,
            "environment_digest": DIGEST,
            "retry_policy_digest": DIGEST,
            "resource_budget_digest": DIGEST,
        },
        "arms": [
            {"arm_id": "default", "topology_candidate_id": "fixed-top", "topology_class": "FIXED_DETERMINISTIC", "topology_digest": DIGEST, "communication_mode": "DEFAULT"},
            {"arm_id": "murmurs", "topology_candidate_id": "fixed-top", "topology_class": "FIXED_DETERMINISTIC", "topology_digest": DIGEST, "communication_mode": "MURMURS"},
        ],
        "tasks": [
            {
                "task_id": "task-01",
                "task_class": "SINGLE_DOMAIN",
                "starting_state_digest": DIGEST,
                "task_prompt_digest": DIGEST,
                "task_payload": {
                    "raw_host_output": _mock_host_envelope(input_tokens=1000, output_tokens=200),
                },
            }
        ],
        "a5_evaluation": None,
        "murmurs_evaluation": {"same_counter_identity_for_token_delta": True},
        "interaction_evaluation": None,
        "preregistration_digest": None,
        "benefit_thresholds": None,
    }

    # Simulate runs with different counter_ids
    run1 = {
        "task_id": "task-01",
        "repetition_index": 1,
        "outcome": {"status": "PASS"},
        "tokens": {"source": "HOST_REPORTED", "counter_id": cid_json},
        "a5_shadow_observation": None,
    }
    run2 = {
        "task_id": "task-01",
        "repetition_index": 1,
        "outcome": {"status": "PASS"},
        "tokens": {"source": "HOST_REPORTED", "counter_id": cid_stream},
        "a5_shadow_observation": None,
    }
    with pytest.raises(Exception, match="MURMURS_ISOLATED requires identical counter_id"):
        runner.enforce_cross_run_invariants(manifest, [run1, run2])


def test_45_final_task_outcome_still_requires_independent_evidence() -> None:
    # Requirement 20: Final task outcome still requires independent validation/governance evidence across all treatments.
    for mode in ("DEFAULT", "CAVEMAN", "MURMURS"):
        # When validation_passed is False, outcome status must be FAIL even if host succeeded
        envelope_fail = _mock_host_envelope(
            status="SUCCESS",
            task_completed=True,
            validation_passed=False,
            governance_valid=True,
        )
        req = _base_request(
            communication_mode=mode,
            caveman_policy_content=VALID_CAVEMAN_SKILL_MD if mode == "CAVEMAN" else None,
            raw_host_output=envelope_fail,
        )
        res = executor.execute_request(req)
        _validate_result_schema(res)
        assert res["outcome"]["status"] == "FAIL"
        assert res["outcome"]["validation_passed"] is False

        # When governance_valid is False, outcome status must be FAIL
        envelope_gov_fail = _mock_host_envelope(
            status="SUCCESS",
            task_completed=True,
            validation_passed=True,
            governance_valid=False,
        )
        req2 = _base_request(
            communication_mode=mode,
            caveman_policy_content=VALID_CAVEMAN_SKILL_MD if mode == "CAVEMAN" else None,
            raw_host_output=envelope_gov_fail,
        )
        res2 = executor.execute_request(req2)
        _validate_result_schema(res2)
        assert res2["outcome"]["status"] == "FAIL"
        assert res2["outcome"]["governance_valid"] is False


# B3.1.3 Exact Host Version Pin Externalization Tests (14 Invariants)


def test_46_preflight_passes_on_exact_expected_version_1_1_15(tmp_path: Path) -> None:
    # Invariant 1: expected 1.1.15 + observed 1.1.15 passes preflight
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    req = _base_request()
    valid, reason, detail, ver = executor.run_host_preflight(
        req,
        expected_cli_version="1.1.15",
        settings_path=settings_file,
        version_runner_fn=lambda cmd: (0, "antigravity-cli 1.1.15\n", ""),
    )
    assert valid is True
    assert reason is None
    assert detail is None
    assert ver == "1.1.15"


def test_47_preflight_fails_closed_before_model_call_on_newer_version_1_1_16(tmp_path: Path) -> None:
    # Invariant 2: expected 1.1.15 + observed 1.1.16 fails before model invocation
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    req = _base_request()
    valid, reason, detail, ver = executor.run_host_preflight(
        req,
        expected_cli_version="1.1.15",
        settings_path=settings_file,
        version_runner_fn=lambda cmd: (0, "antigravity-cli 1.1.16\n", ""),
    )
    assert valid is False
    assert reason == "MEASUREMENT_CAPTURE_FAILURE"
    assert "1.1.16" in str(detail)
    assert ver is None


def test_48_preflight_fails_closed_before_model_call_on_older_version_1_1_14(tmp_path: Path) -> None:
    # Invariant 3: expected 1.1.15 + observed 1.1.14 fails before model invocation
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    req = _base_request()
    valid, reason, detail, ver = executor.run_host_preflight(
        req,
        expected_cli_version="1.1.15",
        settings_path=settings_file,
        version_runner_fn=lambda cmd: (0, "antigravity-cli 1.1.14\n", ""),
    )
    assert valid is False
    assert reason == "MEASUREMENT_CAPTURE_FAILURE"
    assert "1.1.14" in str(detail)
    assert ver is None


def test_49_live_execution_fails_closed_when_expected_version_missing() -> None:
    # Invariant 4: missing expected version at CLI live execution fails closed
    req = _base_request()
    res = executor.execute_request(req)
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert "expected_cli_version" in str(res["raw_evidence"]["detail"])


def test_50_empty_or_whitespace_expected_version_rejected(tmp_path: Path) -> None:
    # Invariant 5: empty / whitespace expected version is rejected
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    assert executor.validate_version_format("") is False
    assert executor.validate_version_format("   ") is False
    assert executor.validate_version_format(None) is False

    req = _base_request()
    res = executor.execute_request(
        req,
        expected_cli_version="   ",
        settings_path=settings_file,
        version_runner_fn=lambda cmd: (0, "1.1.15\n", ""),
    )
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_51_malformed_expected_version_range_and_operators_rejected(tmp_path: Path) -> None:
    # Invariant 6: malformed expected version (ranges, >=1.1.15, latest) is rejected
    invalid_versions = [
        ">=1.1.15",
        "^1.1.15",
        "~1.1.15",
        "1.1.x",
        "1.1.*",
        "latest",
        "LATEST",
        "=1.1.15",
        "1.1.15 - 1.1.16",
    ]
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    for bad_ver in invalid_versions:
        assert executor.validate_version_format(bad_ver) is False
        req = _base_request()
        res = executor.execute_request(
            req,
            expected_cli_version=bad_ver,
            settings_path=settings_file,
            version_runner_fn=lambda cmd: (0, f"{bad_ver}\n", ""),
        )
        _validate_result_schema(res)
        assert res["outcome"]["status"] == "INVALID_RUN"
        assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_52_json_counter_identity_derives_from_exact_validated_version() -> None:
    # Invariant 7: json counter identity derives from exact expected/validated version
    cid_15 = executor.compute_counter_id(cli_version="1.1.15", transport="json-usage")
    assert cid_15 == "antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high"

    cid_14 = executor.compute_counter_id(cli_version="1.1.14", transport="json-usage")
    assert cid_14 == "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"
    assert cid_15 != cid_14


def test_53_stream_json_counter_identity_derives_from_exact_validated_version() -> None:
    # Invariant 8: stream-json counter identity derives from exact expected/validated version
    cid_stream_15 = executor.compute_counter_id(cli_version="1.1.15", transport="stream-json-usage")
    assert cid_stream_15 == "antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high"

    cid_stream_14 = executor.compute_counter_id(cli_version="1.1.14", transport="stream-json-usage")
    assert cid_stream_14 == "antigravity-cli-1.1.14:stream-json-usage:gemini-3.7-flash-high"
    assert cid_stream_15 != cid_stream_14


def test_54_raw_evidence_records_dual_provenance_for_expected_and_observed_version(tmp_path: Path) -> None:
    # Invariant 9: dual provenance (expected_cli_version + observed_cli_version) preserved
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "antigravity-cli 1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        return (0, json.dumps(_mock_host_envelope(cli_version="1.1.15")), "")

    req = _base_request()
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    raw_ev = res["raw_evidence"]
    assert raw_ev["expected_cli_version"] == "1.1.15"
    assert raw_ev["expected_cli_version_provenance"]["source"] == "EXECUTOR_ARGUMENT"
    assert raw_ev["expected_cli_version_provenance"]["value"] == "1.1.15"
    assert raw_ev["observed_cli_version"] == "1.1.15"
    assert raw_ev["cli_version_provenance"]["source"] == "PREFLIGHT_COMMAND"
    assert raw_ev["cli_version_provenance"]["value"] == "1.1.15"


def test_55_counter_identity_drift_inside_paired_arms_fails_closed(tmp_path: Path) -> None:
    # Invariant 10: counter identity cannot silently drift inside paired arms
    manifest_path = tmp_path / "drift_manifest.json"
    manifest = {
        "schema_version": "orchestra.comparative-benchmark-manifest.v1",
        "program_id": "orchestra.shared-comparative-benchmark.v1",
        "experiment_id": "fixture-b3-drift",
        "experiment_kind": "MURMURS_ISOLATED",
        "stage": "CALIBRATION",
        "randomization_seed": 12345,
        "repetitions_per_arm": 1,
        "executor_timeout_seconds": 30,
        "common_control_identity": {
            "orchestra_revision": "06ede6bde3aa7682194950ba9130ba52e4fb0ea5",
            "repository_revision": "test-repo-rev",
            "starting_state_digest": DIGEST,
            "task_prompt_digest": DIGEST,
            "system_instruction_digest": DIGEST,
            "provider": "antigravity",
            "model": "gemini-3.7-flash-high",
            "model_revision": None,
            "reasoning_setting": "default",
            "temperature": 0.0,
            "tool_access_digest": DIGEST,
            "specialist_set_digest": DIGEST,
            "required_specialist_set_digest": DIGEST,
            "authority_digest": DIGEST,
            "governance_digest": DIGEST,
            "validation_contract_digest": DIGEST,
            "environment_digest": DIGEST,
            "retry_policy_digest": DIGEST,
            "resource_budget_digest": DIGEST,
        },
        "arms": [
            {"arm_id": "default", "topology_candidate_id": "fixed-top", "topology_class": "FIXED_DETERMINISTIC", "topology_digest": DIGEST, "communication_mode": "DEFAULT"},
            {"arm_id": "caveman", "topology_candidate_id": "fixed-top", "topology_class": "FIXED_DETERMINISTIC", "topology_digest": DIGEST, "communication_mode": "CAVEMAN"},
        ],
        "tasks": [
            {
                "task_id": "task-01",
                "task_class": "SINGLE_DOMAIN",
                "starting_state_digest": DIGEST,
                "task_prompt_digest": DIGEST,
                "task_payload": {
                    "raw_host_output": _mock_host_envelope(input_tokens=1000, output_tokens=200),
                },
            }
        ],
        "a5_evaluation": None,
        "murmurs_evaluation": {"same_counter_identity_for_token_delta": True},
        "interaction_evaluation": None,
        "preregistration_digest": None,
        "benefit_thresholds": None,
    }

    run_v15 = {
        "task_id": "task-01",
        "repetition_index": 1,
        "outcome": {"status": "PASS"},
        "tokens": {"source": "HOST_REPORTED", "counter_id": "antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high"},
        "a5_shadow_observation": None,
    }
    run_v14 = {
        "task_id": "task-01",
        "repetition_index": 1,
        "outcome": {"status": "PASS"},
        "tokens": {"source": "HOST_REPORTED", "counter_id": "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"},
        "a5_shadow_observation": None,
    }
    with pytest.raises(Exception, match="MURMURS_ISOLATED requires identical counter_id"):
        runner.enforce_cross_run_invariants(manifest, [run_v15, run_v14])


def test_56_historical_1_1_14_fixture_supported_when_expected_version_explicitly_set() -> None:
    # Invariant 11: historical 1.1.14 fixture behavior supported by passing expected_cli_version="1.1.14" explicitly
    envelope_14 = _mock_host_envelope(cli_version="1.1.14", input_tokens=1100, output_tokens=220)
    req = _base_request(raw_host_output=envelope_14)
    res = executor.execute_request(req, expected_cli_version="1.1.14")
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "PASS"
    assert res["tokens"]["counter_id"] == "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"
    assert res["raw_evidence"]["expected_cli_version"] == "1.1.14"
    assert res["raw_evidence"]["observed_cli_version"] == "1.1.14"


def test_57_zero_live_antigravity_model_turns_in_test_suite() -> None:
    # Invariant 12: zero live AGY model turns in tests
    call_log: list[str] = []

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        call_log.append("called")
        return (0, json.dumps(_mock_host_envelope()), "")

    # Mock output bypasses live subprocess entirely
    req = _base_request(raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req, runner_fn=mock_model_runner)
    assert len(call_log) == 0
    assert res["outcome"]["status"] == "PASS"


def test_58_all_b3_1_2_communication_treatments_remain_green_with_1_1_15() -> None:
    # Invariant 13: all B3.1.2 treatment tests remain green
    for mode in ("DEFAULT", "CAVEMAN", "MURMURS"):
        req = _base_request(
            communication_mode=mode,
            caveman_policy_content=VALID_CAVEMAN_SKILL_MD if mode == "CAVEMAN" else None,
            raw_host_output=_mock_host_envelope(cli_version="1.1.15"),
        )
        res = executor.execute_request(req, expected_cli_version="1.1.15")
        _validate_result_schema(res)
        assert res["outcome"]["status"] == "PASS"
        assert res["raw_evidence"]["communication_mode"] == mode
        assert res["tokens"]["counter_id"] == "antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high"


def test_59_host_success_alone_cannot_become_benchmark_task_pass() -> None:
    # Invariant 14: host SUCCESS alone cannot become benchmark task PASS
    bare_success = {
        "status": "SUCCESS",
        "cli_version": "1.1.15",
        "model": "gemini-3.7-flash-high",
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 200,
        },
    }
    req = _base_request(raw_host_output=bare_success)
    res = executor.execute_request(req, expected_cli_version="1.1.15")
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "FAIL"
    assert res["outcome"]["task_completed"] is False
    assert res["outcome"]["validation_passed"] is False
    assert res["outcome"]["governance_valid"] is False
    assert res["tokens"]["source"] == "HOST_REPORTED"


def test_60_resolve_use_g1_credits_helper_state_table() -> None:
    # State A: key absent -> effective false, SYSTEM_DEFAULT_SPARSE_PERSISTENCE
    ok, err, policy = executor.resolve_use_g1_credits({})
    assert ok is True
    assert err is None
    assert policy == {
        "setting_name": "useG1Credits",
        "key_present": False,
        "observed_value": None,
        "effective_value": False,
        "effective_source": "SYSTEM_DEFAULT_SPARSE_PERSISTENCE",
        "fallback_allowed": False,
    }

    # State B: key explicitly false -> effective false, EXPLICIT_SETTING
    ok, err, policy = executor.resolve_use_g1_credits({"useG1Credits": False})
    assert ok is True
    assert err is None
    assert policy == {
        "setting_name": "useG1Credits",
        "key_present": True,
        "observed_value": False,
        "effective_value": False,
        "effective_source": "EXPLICIT_SETTING",
        "fallback_allowed": False,
    }

    # State C: key explicitly true -> fails closed, fallback_allowed True
    ok, err, policy = executor.resolve_use_g1_credits({"useG1Credits": True})
    assert ok is False
    assert "explicitly true" in str(err)
    assert policy == {
        "setting_name": "useG1Credits",
        "key_present": True,
        "observed_value": True,
        "effective_value": True,
        "effective_source": "EXPLICIT_SETTING",
        "fallback_allowed": True,
    }

    # State D: key present with invalid/non-boolean values
    invalid_cases = [
        None,
        0,
        1,
        "false",
        "true",
        {},
        [],
        3.14,
    ]
    for val in invalid_cases:
        ok, err, policy = executor.resolve_use_g1_credits({"useG1Credits": val})
        assert ok is False
        assert err is not None
        assert policy["key_present"] is True
        assert policy["observed_value"] == val
        assert policy["effective_value"] is None
        assert policy["effective_source"] == "MALFORMED_EXPLICIT_SETTING"
        assert policy["fallback_allowed"] is False

    # Non-dict inputs
    for non_dict in (None, [1, 2], "string", 42):
        ok, err, policy = executor.resolve_use_g1_credits(non_dict)
        assert ok is False
        assert "not an object" in str(err)


def test_61_preflight_passes_on_sparse_omitted_use_g1_credits(tmp_path: Path) -> None:
    # Key absent in settings.json passes preflight and preserves sparse provenance
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=None)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sparse settings verification")
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is True
    assert res["outcome"]["status"] == "PASS"
    raw_ev = res["raw_evidence"]
    assert raw_ev["useG1Credits"] is False
    assert raw_ev["credit_fallback_policy"] == {
        "setting_name": "useG1Credits",
        "key_present": False,
        "observed_value": None,
        "effective_value": False,
        "effective_source": "SYSTEM_DEFAULT_SPARSE_PERSISTENCE",
        "fallback_allowed": False,
    }


def test_62_preflight_passes_on_explicit_false_use_g1_credits(tmp_path: Path) -> None:
    # Explicit false in settings.json passes preflight and preserves explicit provenance
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Explicit false verification")
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is True
    assert res["outcome"]["status"] == "PASS"
    raw_ev = res["raw_evidence"]
    assert raw_ev["useG1Credits"] is False
    assert raw_ev["credit_fallback_policy"] == {
        "setting_name": "useG1Credits",
        "key_present": True,
        "observed_value": False,
        "effective_value": False,
        "effective_source": "EXPLICIT_SETTING",
        "fallback_allowed": False,
    }


def test_63_preflight_fails_closed_on_explicit_true_use_g1_credits(tmp_path: Path) -> None:
    # Explicit true in settings.json fails closed as INVALID_RUN / MEASUREMENT_CAPTURE_FAILURE
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=True)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Explicit true verification")
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is False
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    detail = res["raw_evidence"]["detail"]
    assert detail["credit_fallback_policy"]["fallback_allowed"] is True
    assert detail["credit_fallback_policy"]["effective_value"] is True
    assert detail["credit_fallback_policy"]["key_present"] is True


def test_64_preflight_fails_closed_on_null_use_g1_credits(tmp_path: Path) -> None:
    # JSON null (None in Python) fails closed without coercion
    settings_file = tmp_path / "settings_null.json"
    settings_file.write_text(json.dumps({"useG1Credits": None}), encoding="utf-8")
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Null check")
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is False
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_65_preflight_fails_closed_on_numeric_0_use_g1_credits(tmp_path: Path) -> None:
    # Numeric 0 fails closed (not coerced to False)
    settings_file = tmp_path / "settings_zero.json"
    settings_file.write_text(json.dumps({"useG1Credits": 0}), encoding="utf-8")
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request()
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)
    assert model_called is False
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_66_preflight_fails_closed_on_numeric_1_use_g1_credits(tmp_path: Path) -> None:
    # Numeric 1 fails closed (not coerced to True)
    settings_file = tmp_path / "settings_one.json"
    settings_file.write_text(json.dumps({"useG1Credits": 1}), encoding="utf-8")
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request()
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)
    assert model_called is False
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_67_preflight_fails_closed_on_string_false_use_g1_credits(tmp_path: Path) -> None:
    # String "false" fails closed (not coerced to False)
    settings_file = tmp_path / "settings_str_false.json"
    settings_file.write_text(json.dumps({"useG1Credits": "false"}), encoding="utf-8")
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request()
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)
    assert model_called is False
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_68_preflight_fails_closed_on_string_true_use_g1_credits(tmp_path: Path) -> None:
    # String "true" fails closed (not coerced to True)
    settings_file = tmp_path / "settings_str_true.json"
    settings_file.write_text(json.dumps({"useG1Credits": "true"}), encoding="utf-8")
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request()
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)
    assert model_called is False
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_69_preflight_fails_closed_on_object_or_list_use_g1_credits(tmp_path: Path) -> None:
    # Object or list value fails closed
    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    for val in ({}, [1, 2]):
        sf = tmp_path / f"settings_{type(val).__name__}.json"
        sf.write_text(json.dumps({"useG1Credits": val}), encoding="utf-8")
        req = _base_request()
        res = executor.execute_request(
            req,
            expected_cli_version="1.1.15",
            settings_path=sf,
            version_runner_fn=mock_version_runner,
        )
        _validate_result_schema(res)
        assert res["outcome"]["status"] == "INVALID_RUN"
        assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_70_missing_settings_file_fails_closed(tmp_path: Path) -> None:
    # Non-existent settings.json file fails closed
    missing_file = tmp_path / "does_not_exist" / "settings.json"
    req = _base_request()
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        settings_path=missing_file,
        version_runner_fn=lambda cmd: (0, "1.1.15\n", ""),
    )
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_71_malformed_json_settings_file_fails_closed(tmp_path: Path) -> None:
    # Malformed JSON syntax in settings.json fails closed
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ unclosed json", encoding="utf-8")
    req = _base_request()
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        settings_path=bad_file,
        version_runner_fn=lambda cmd: (0, "1.1.15\n", ""),
    )
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_72_exact_cli_version_mismatch_fails_closed_before_model_invocation(tmp_path: Path) -> None:
    # CLI version mismatch fails closed before model execution
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=None)
    model_called = False

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request()
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=lambda cmd: (0, "antigravity-cli 1.1.16\n", ""),
    )
    _validate_result_schema(res)
    assert model_called is False
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_73_model_mismatch_fails_closed_before_model_invocation(tmp_path: Path) -> None:
    # Model mismatch fails closed
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=None)
    req = _base_request()
    req["control_identity"]["model"] = "gemini-2.5-pro"
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        settings_path=settings_file,
        version_runner_fn=lambda cmd: (0, "1.1.15\n", ""),
    )
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_74_counter_identity_invariants_preserved() -> None:
    # Counter identities remain deterministic and exact
    json_counter = executor.compute_counter_id(cli_version="1.1.15", transport="json-usage")
    stream_counter = executor.compute_counter_id(cli_version="1.1.15", transport="stream-json-usage")
    assert json_counter == "antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high"
    assert stream_counter == "antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high"


def test_75_provenance_distinguishes_explicit_setting_from_system_default_sparse(tmp_path: Path) -> None:
    # Provenance semantics distinguish EXPLICIT_SETTING from SYSTEM_DEFAULT_SPARSE_PERSISTENCE
    settings_sparse = tmp_path / "sparse.json"
    settings_sparse.write_text("{}", encoding="utf-8")

    settings_explicit = tmp_path / "explicit.json"
    settings_explicit.write_text(json.dumps({"useG1Credits": False}), encoding="utf-8")

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        return (0, json.dumps(_mock_host_envelope()), "")

    res_sparse = executor.execute_request(
        _base_request(prompt="sparse test"),
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_sparse,
        version_runner_fn=mock_version_runner,
    )
    res_explicit = executor.execute_request(
        _base_request(prompt="explicit test"),
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_explicit,
        version_runner_fn=mock_version_runner,
    )

    _validate_result_schema(res_sparse)
    _validate_result_schema(res_explicit)

    pol_sparse = res_sparse["raw_evidence"]["credit_fallback_policy"]
    pol_explicit = res_explicit["raw_evidence"]["credit_fallback_policy"]

    assert pol_sparse["effective_source"] == "SYSTEM_DEFAULT_SPARSE_PERSISTENCE"
    assert pol_sparse["key_present"] is False
    assert pol_sparse["observed_value"] is None
    assert pol_sparse["effective_value"] is False

    assert pol_explicit["effective_source"] == "EXPLICIT_SETTING"
    assert pol_explicit["key_present"] is True
    assert pol_explicit["observed_value"] is False
    assert pol_explicit["effective_value"] is False


def test_76_stream_json_sparse_settings_provenance(tmp_path: Path) -> None:
    # Stream-json transport preserves sparse settings provenance
    settings_file = tmp_path / "sparse_stream.json"
    settings_file.write_text("{}", encoding="utf-8")

    events = [
        {"type": "step_update", "content": "Working..."},
        {
            "type": "result",
            "status": "SUCCESS",
            "cli_version": "1.1.15",
            "usage": {"input_tokens": 1200, "output_tokens": 300, "thinking_tokens": 50, "cache_read_tokens": 100, "total_tokens": 1650},
            "task_completed": True,
            "validation_passed": True,
            "governance_valid": True,
            "response": "Done with task",
        },
    ]
    raw_stream = "\n".join(json.dumps(ev) for ev in events)

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        return (0, raw_stream, "")

    req = _base_request(prompt="Stream sparse test", transport="stream-json")
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
        transport="stream-json",
    )
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "PASS"
    assert res["tokens"]["counter_id"] == "antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high"
    pol = res["raw_evidence"]["credit_fallback_policy"]
    assert pol["effective_source"] == "SYSTEM_DEFAULT_SPARSE_PERSISTENCE"
    assert pol["key_present"] is False
    assert pol["effective_value"] is False


def _mock_agy_1_1_15_wrapped_result(
    status: str = "SUCCESS",
    input_tokens: int = 142896,
    output_tokens: int = 4692,
    thinking_tokens: int = 2804,
    cache_read_tokens: int = 786302,
    total_tokens: int = 147588,
    response: str = "diagnostic response",
    conversation_id: str = "synthetic-test-id",
    duration_seconds: float = 86.5398064,
    num_turns: int = 1,
    cli_version: str | None = None,
    model: str | None = None,
    task_completed: bool = True,
    validation_passed: bool = True,
    governance_valid: bool = True,
) -> dict[str, Any]:
    res: dict[str, Any] = {
        "conversation_id": conversation_id,
        "duration_seconds": duration_seconds,
        "num_turns": num_turns,
        "response": response,
        "status": status,
        "usage": {
            "cache_read_tokens": cache_read_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "thinking_tokens": thinking_tokens,
            "total_tokens": total_tokens,
        },
        "task_completed": task_completed,
        "validation_passed": validation_passed,
        "governance_valid": governance_valid,
    }
    if cli_version is not None:
        res["cli_version"] = cli_version
    if model is not None:
        res["model"] = model
    return {
        "event": "result",
        "result": res,
    }


def test_77_normalize_stream_terminal_event_helper_unit_tests() -> None:
    # Helper unit tests for normalize_stream_terminal_event
    wrapped = _mock_agy_1_1_15_wrapped_result()
    ok, err, norm = executor.normalize_stream_terminal_event(wrapped)
    assert ok is True
    assert err is None
    assert norm is not None
    assert norm["status"] == "SUCCESS"
    assert norm["usage"]["input_tokens"] == 142896
    assert norm["conversation_id"] == "synthetic-test-id"

    # Flat legacy event
    flat = {"type": "result", "status": "SUCCESS", "usage": {"input_tokens": 100, "output_tokens": 50}}
    ok, err, norm = executor.normalize_stream_terminal_event(flat)
    assert ok is True
    assert err is None
    assert norm["usage"]["input_tokens"] == 100

    # Non-dict event
    ok, err, norm = executor.normalize_stream_terminal_event("not-a-dict")  # type: ignore
    assert ok is False
    assert "not a JSON object" in (err or "")

    # Wrapped event with non-dict result payload
    ok, err, norm = executor.normalize_stream_terminal_event({"event": "result", "result": "invalid"})
    assert ok is False
    assert "nested result payload is not a JSON object" in (err or "")

    # Wrapped event with missing result key
    ok, err, norm = executor.normalize_stream_terminal_event({"event": "result"})
    assert ok is False
    assert "missing result payload" in (err or "")

    # Conflicting outer status
    conflict_status = {
        "event": "result",
        "status": "FAIL",
        "result": {"status": "SUCCESS", "usage": {"input_tokens": 100, "output_tokens": 50}},
    }
    ok, err, norm = executor.normalize_stream_terminal_event(conflict_status)
    assert ok is False
    assert "conflicting outer wrapper and nested result critical field: status" in (err or "")

    # Conflicting outer usage
    conflict_usage = {
        "event": "result",
        "usage": {"input_tokens": 999, "output_tokens": 1},
        "result": {"status": "SUCCESS", "usage": {"input_tokens": 100, "output_tokens": 50}},
    }
    ok, err, norm = executor.normalize_stream_terminal_event(conflict_usage)
    assert ok is False
    assert "conflicting outer wrapper and nested result critical field: usage" in (err or "")


def test_78_wrapped_agy_1_1_15_terminal_event_detected_and_accepted() -> None:
    # Requirement: wrapped event=result matching AGY 1.1.15 is detected and parsed correctly
    wrapped = _mock_agy_1_1_15_wrapped_result()
    events = [
        {"event": "step_update", "content": "Processing task step..."},
        wrapped,
    ]
    raw_stream = "\n".join(json.dumps(ev) for ev in events)

    req = _base_request(prompt="AGY 1.1.15 stream test", transport="stream-json")
    res = executor.parse_antigravity_output(
        raw_stream,
        req,
        elapsed_ms=86540,
        expected_cli_version="1.1.15",
        transport="stream-json-usage",
    )
    _validate_result_schema(res)

    # 1. wrapped event=result is detected as terminal
    assert res["outcome"]["status"] == "PASS"

    # 2. nested result.status=SUCCESS is accepted
    assert res["outcome"]["task_completed"] is True
    assert res["outcome"]["validation_passed"] is True
    assert res["outcome"]["governance_valid"] is True

    # 3. nested usage maps to HOST_REPORTED tokens
    tok = res["tokens"]
    assert tok["source"] == "HOST_REPORTED"
    assert tok["input_tokens"] == 142896
    assert tok["output_tokens"] == 4692
    assert tok["reasoning_tokens"] == 2804
    assert tok["cached_input_tokens"] == 786302
    assert tok["fresh_billable_tokens"] is None

    # 4. counter identity is the qualified stream counter
    assert tok["counter_id"] == "antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high"

    # 5. cache_read_tokens maps without being invented into total_tokens
    assert res["raw_evidence"]["total_tokens"] == 147588

    # 6. response contributes to user-visible output accounting
    resp_bytes = len("diagnostic response".encode("utf-8"))
    assert res["communication"]["user_visible_bytes"] >= resp_bytes

    # 7. original wrapper is retained
    assert "terminal_event_envelope" in res["raw_evidence"]
    assert res["raw_evidence"]["terminal_event_envelope"]["event"] == "result"
    assert "result" in res["raw_evidence"]["terminal_event_envelope"]

    # 8. normalized result payload is retained
    assert "terminal_result_payload" in res["raw_evidence"]
    assert res["raw_evidence"]["terminal_result_payload"]["status"] == "SUCCESS"
    assert res["raw_evidence"]["terminal_result_payload"]["conversation_id"] == "synthetic-test-id"


def test_79_wrapped_stream_malformed_result_fails_closed() -> None:
    # Requirement: malformed result value fails closed
    req = _base_request(transport="stream-json")

    # String result
    res_str = executor.parse_stream_json_output(
        [{"event": "result", "result": "malformed_string"}],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_str)
    assert res_str["outcome"]["status"] == "INVALID_RUN"
    assert res_str["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Null result
    res_null = executor.parse_stream_json_output(
        [{"event": "result", "result": None}],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_null)
    assert res_null["outcome"]["status"] == "INVALID_RUN"
    assert res_null["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Integer result
    res_int = executor.parse_stream_json_output(
        [{"event": "result", "result": 12345}],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_int)
    assert res_int["outcome"]["status"] == "INVALID_RUN"
    assert res_int["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Missing result key with event=result
    res_missing = executor.parse_stream_json_output(
        [{"event": "result"}],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_missing)
    assert res_missing["outcome"]["status"] == "INVALID_RUN"
    assert res_missing["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_80_wrapped_stream_missing_or_non_success_status_fails_closed() -> None:
    # Requirement: missing nested status or non-SUCCESS nested status fails closed
    req = _base_request(transport="stream-json")

    # Missing status
    res_missing_status = executor.parse_stream_json_output(
        [{
            "event": "result",
            "result": {
                "usage": {"input_tokens": 100, "output_tokens": 50},
                "response": "ok",
            },
        }],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_missing_status)
    assert res_missing_status["outcome"]["status"] == "INVALID_RUN"
    assert res_missing_status["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Non-SUCCESS status
    res_fail_status = executor.parse_stream_json_output(
        [{
            "event": "result",
            "result": {
                "status": "ERROR",
                "usage": {"input_tokens": 100, "output_tokens": 50},
                "response": "failed",
            },
        }],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_fail_status)
    assert res_fail_status["outcome"]["status"] == "INVALID_RUN"
    assert res_fail_status["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_81_wrapped_stream_missing_or_malformed_usage_fails_closed() -> None:
    # Requirement: missing usage or malformed usage fails closed
    req = _base_request(transport="stream-json")

    # Missing usage
    res_no_usage = executor.parse_stream_json_output(
        [{
            "event": "result",
            "result": {
                "status": "SUCCESS",
                "response": "ok",
            },
        }],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_no_usage)
    assert res_no_usage["outcome"]["status"] == "INVALID_RUN"
    assert res_no_usage["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Non-dict usage
    res_str_usage = executor.parse_stream_json_output(
        [{
            "event": "result",
            "result": {
                "status": "SUCCESS",
                "usage": "invalid_usage_string",
            },
        }],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_str_usage)
    assert res_str_usage["outcome"]["status"] == "INVALID_RUN"
    assert res_str_usage["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Missing input_tokens
    res_missing_input = executor.parse_stream_json_output(
        [{
            "event": "result",
            "result": {
                "status": "SUCCESS",
                "usage": {"output_tokens": 50},
            },
        }],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_missing_input)
    assert res_missing_input["outcome"]["status"] == "INVALID_RUN"
    assert res_missing_input["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Negative tokens
    res_neg_input = executor.parse_stream_json_output(
        [{
            "event": "result",
            "result": {
                "status": "SUCCESS",
                "usage": {"input_tokens": -1, "output_tokens": 50},
            },
        }],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_neg_input)
    assert res_neg_input["outcome"]["status"] == "INVALID_RUN"
    assert res_neg_input["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_82_conflicting_outer_wrapper_and_nested_critical_values_fail_closed() -> None:
    # Requirement: conflicting outer and nested critical values fail closed
    req = _base_request(transport="stream-json")

    # Conflicting status
    res_status_conflict = executor.parse_stream_json_output(
        [{
            "event": "result",
            "status": "FAIL",
            "result": {
                "status": "SUCCESS",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
        }],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_status_conflict)
    assert res_status_conflict["outcome"]["status"] == "INVALID_RUN"
    assert res_status_conflict["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Conflicting usage
    res_usage_conflict = executor.parse_stream_json_output(
        [{
            "event": "result",
            "usage": {"input_tokens": 999, "output_tokens": 999},
            "result": {
                "status": "SUCCESS",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
        }],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_usage_conflict)
    assert res_usage_conflict["outcome"]["status"] == "INVALID_RUN"
    assert res_usage_conflict["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Conflicting cli_version
    res_ver_conflict = executor.parse_stream_json_output(
        [{
            "event": "result",
            "cli_version": "1.1.14",
            "result": {
                "status": "SUCCESS",
                "cli_version": "1.1.15",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
        }],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_ver_conflict)
    assert res_ver_conflict["outcome"]["status"] == "INVALID_RUN"
    assert res_ver_conflict["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    # Conflicting model
    res_model_conflict = executor.parse_stream_json_output(
        [{
            "event": "result",
            "model": "gemini-2.5-pro",
            "result": {
                "status": "SUCCESS",
                "model": "gemini-3.7-flash-high",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
        }],
        req,
        expected_cli_version="1.1.15",
    )
    _validate_result_schema(res_model_conflict)
    assert res_model_conflict["outcome"]["status"] == "INVALID_RUN"
    assert res_model_conflict["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_83_matching_outer_and_nested_critical_fields_accepted() -> None:
    # Requirement: non-conflicting outer metadata is accepted and merged without error
    req = _base_request(transport="stream-json")
    event = {
        "event": "result",
        "status": "SUCCESS",
        "cli_version": "1.1.15",
        "model": "gemini-3.7-flash-high",
        "result": {
            "status": "SUCCESS",
            "cli_version": "1.1.15",
            "model": "gemini-3.7-flash-high",
            "usage": {"input_tokens": 500, "output_tokens": 100},
            "task_completed": True,
            "validation_passed": True,
            "governance_valid": True,
            "response": "All matched",
        },
    }
    res = executor.parse_stream_json_output([event], req, expected_cli_version="1.1.15")
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "PASS"
    assert res["tokens"]["input_tokens"] == 500


def test_84_multiple_conflicting_terminal_results_in_stream_fails_closed() -> None:
    # Requirement: multiple conflicting terminal results fail closed
    req = _base_request(transport="stream-json")
    ev1 = _mock_agy_1_1_15_wrapped_result(status="SUCCESS", input_tokens=1000)
    ev2 = _mock_agy_1_1_15_wrapped_result(status="SUCCESS", input_tokens=2000)  # different usage!

    res = executor.parse_stream_json_output([ev1, ev2], req, expected_cli_version="1.1.15")
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"


def test_85_flat_legacy_terminal_fixture_remains_supported() -> None:
    # Requirement: flat legacy terminal fixtures continue to be accepted
    flat_event = {
        "type": "result",
        "status": "SUCCESS",
        "cli_version": "1.1.15",
        "model": "gemini-3.7-flash-high",
        "usage": {
            "input_tokens": 1500,
            "output_tokens": 400,
            "thinking_tokens": 120,
            "cache_read_tokens": 300,
            "total_tokens": 2320,
        },
        "task_completed": True,
        "validation_passed": True,
        "governance_valid": True,
        "response": "Legacy flat response",
    }
    req = _base_request(transport="stream-json")
    res = executor.parse_stream_json_output([flat_event], req, expected_cli_version="1.1.15")
    _validate_result_schema(res)
    assert res["outcome"]["status"] == "PASS"
    assert res["tokens"]["input_tokens"] == 1500
    assert res["raw_evidence"]["terminal_event_envelope"] == flat_event
    assert res["raw_evidence"]["terminal_result_payload"]["status"] == "SUCCESS"


def test_86_intermediate_progress_events_with_event_field_recognized() -> None:
    # Requirement: event=step_update recognized and terminal result excluded from intermediate count
    events = [
        {"event": "step_update", "content": "Thinking step 1"},
        {"event": "step_update", "content": "Thinking step 2"},
        {"event": "tool_start", "event_kind": "TOOL_STARTED", "content": "Running tool"},
        {"event": "tool_complete", "event_kind": "TOOL_COMPLETED", "content": "Finished tool"},
        _mock_agy_1_1_15_wrapped_result(),
    ]
    raw_stream = "\n".join(json.dumps(ev) for ev in events)

    req = _base_request(transport="stream-json", communication_mode="DEFAULT")
    res = executor.parse_stream_json_output(raw_stream, req, expected_cli_version="1.1.15")
    _validate_result_schema(res)

    comm = res["communication"]
    # 4 intermediate events, terminal result is excluded from progress_messages count
    assert comm["progress_messages"] == 4
    assert comm["model_progress_calls"] == 4
    # User visible bytes include content of intermediate events + terminal response
    assert comm["user_visible_bytes"] > len("diagnostic response".encode("utf-8"))


def test_87_wrapped_stream_across_all_communication_treatments() -> None:
    # Requirement: DEFAULT, CAVEMAN, MURMURS arms all work with wrapped AGY 1.1.15 stream-json output
    wrapped = _mock_agy_1_1_15_wrapped_result()
    events = [
        {"event": "step_update", "event_kind": "TOOL_STARTED", "content": "Running test"},
        {"event": "step_update", "event_kind": "TOOL_COMPLETED", "content": "Completed test"},
        wrapped,
    ]
    stream_payload = "\n".join(json.dumps(ev) for ev in events)

    for mode in ("DEFAULT", "CAVEMAN", "MURMURS"):
        req = _base_request(
            communication_mode=mode,
            transport="stream-json",
            caveman_policy_content=VALID_CAVEMAN_SKILL_MD if mode == "CAVEMAN" else None,
            raw_host_output=stream_payload,
        )
        res = executor.execute_request(req)
        _validate_result_schema(res)

        assert res["tokens"]["source"] == "HOST_REPORTED"
        assert res["tokens"]["counter_id"] == "antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high"
        assert res["tokens"]["input_tokens"] == 142896
        assert res["tokens"]["cached_input_tokens"] == 786302
        assert res["raw_evidence"]["transport"] == "stream-json-usage"
        assert res["outcome"]["status"] == "PASS"


def test_88_zero_live_model_calls_across_all_stream_tests() -> None:
    # Requirement: zero tests execute a real Antigravity model turn
    call_records: list[list[str]] = []

    def tracking_runner(cmd: list[str], prompt: str = "") -> tuple[int, str, str]:
        call_records.append(cmd)
        return (0, json.dumps(_mock_agy_1_1_15_wrapped_result()), "")

    req = _base_request(
        raw_host_output=json.dumps(_mock_agy_1_1_15_wrapped_result()),
        transport="stream-json",
    )
    res = executor.execute_request(req, runner_fn=tracking_runner)
    _validate_result_schema(res)

    # When mock output is provided, runner is never called
    assert len(call_records) == 0
    assert res["outcome"]["status"] == "PASS"


def test_89_explicit_valid_workspace_binding(tmp_path: Path) -> None:
    # Requirement: explicit valid workspace binding via task_payload or argument
    ws_dir = tmp_path / "valid_workspace"
    ws_dir.mkdir()
    settings_file = _create_mock_settings(tmp_path)

    captured_cmds: list[list[str]] = []

    def mock_runner(cmd: list[str], prompt: str = "") -> tuple[int, str, str]:
        captured_cmds.append(cmd)
        return (0, json.dumps(_mock_host_envelope()), "")

    def mock_version(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15", "")

    req = _base_request(workspace_dir=str(ws_dir))
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version,
    )
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "PASS"
    assert res["raw_evidence"]["workspace_binding"]["bound"] is True
    assert res["raw_evidence"]["workspace_binding"]["workspace_path"] == str(ws_dir.resolve())
    assert res["raw_evidence"]["workspace_binding"]["workspace_flag"] == "--add-dir"
    assert res["raw_evidence"]["workspace_binding"]["workspace_mechanism"] == "CLI_ADD_DIR"
    assert res["raw_evidence"]["workspace_binding"]["provenance"]["source"] == "TASK_PAYLOAD"
    assert len(captured_cmds) == 1
    cmd = captured_cmds[0]
    assert "--add-dir" in cmd
    idx = cmd.index("--add-dir")
    assert cmd[idx + 1] == str(ws_dir.resolve())


def test_90_missing_workspace_in_live_execution_fails_closed(tmp_path: Path) -> None:
    # Requirement: missing workspace in live execution fails closed before runner invocation
    settings_file = _create_mock_settings(tmp_path)
    runner_called = False

    def mock_runner(cmd: list[str], prompt: str = "") -> tuple[int, str, str]:
        nonlocal runner_called
        runner_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(require_workspace=True)  # Workspace required but not provided
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_runner,
        settings_path=settings_file,
    )
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert "workspace" in res["raw_evidence"]["detail"]["error"].lower()
    assert not runner_called


def test_91_nonexistent_workspace_fails_closed(tmp_path: Path) -> None:
    # Requirement: nonexistent workspace path fails closed before runner invocation
    nonexistent = tmp_path / "does_not_exist_dir"
    settings_file = _create_mock_settings(tmp_path)
    runner_called = False

    def mock_runner(cmd: list[str], prompt: str = "") -> tuple[int, str, str]:
        nonlocal runner_called
        runner_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(workspace_dir=str(nonexistent))
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_runner,
        settings_path=settings_file,
    )
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert "does not exist" in res["raw_evidence"]["detail"]["error"].lower()
    assert not runner_called


def test_92_file_path_instead_of_directory_fails_closed(tmp_path: Path) -> None:
    # Requirement: workspace pointing to a regular file instead of directory fails closed
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("hello", encoding="utf-8")
    settings_file = _create_mock_settings(tmp_path)
    runner_called = False

    def mock_runner(cmd: list[str], prompt: str = "") -> tuple[int, str, str]:
        nonlocal runner_called
        runner_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(workspace_dir=str(file_path))
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_runner,
        settings_path=settings_file,
    )
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert "not a directory" in res["raw_evidence"]["detail"]["error"].lower()
    assert not runner_called


def test_93_workspace_path_containing_spaces_safe(tmp_path: Path) -> None:
    # Requirement: workspace directory with spaces is safely bound in argument array
    ws_spaces = tmp_path / "my isolated test workspace"
    ws_spaces.mkdir()
    settings_file = _create_mock_settings(tmp_path)

    captured_cmds: list[list[str]] = []

    def mock_runner(cmd: list[str], prompt: str = "") -> tuple[int, str, str]:
        captured_cmds.append(cmd)
        return (0, json.dumps(_mock_host_envelope()), "")

    def mock_version(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15", "")

    req = _base_request(workspace_dir=str(ws_spaces))
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version,
    )
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "PASS"
    assert len(captured_cmds) == 1
    cmd = captured_cmds[0]
    idx = cmd.index("--add-dir")
    assert cmd[idx + 1] == str(ws_spaces.resolve())
    assert isinstance(cmd, list)


def test_94_command_is_argument_array_with_shell_false(tmp_path: Path) -> None:
    # Requirement: command remains argument list with no shell string concatenation
    ws_dir = tmp_path / "safe_ws"
    ws_dir.mkdir()
    settings_file = _create_mock_settings(tmp_path)

    captured_cmds: list[list[str]] = []

    def mock_runner(cmd: list[str], prompt: str = "") -> tuple[int, str, str]:
        captured_cmds.append(cmd)
        return (0, json.dumps(_mock_host_envelope()), "")

    def mock_version(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15", "")

    req = _base_request(workspace_dir=str(ws_dir))
    executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version,
    )

    assert len(captured_cmds) == 1
    cmd = captured_cmds[0]
    assert isinstance(cmd, list)
    assert all(isinstance(token, str) for token in cmd)
    assert cmd[0] == "agy"
    assert "--add-dir" in cmd
    assert cmd[cmd.index("--add-dir") + 1] == str(ws_dir.resolve())
    assert "--model" in cmd
    assert cmd[cmd.index("--model") + 1] == "gemini-3.7-flash-high"
    assert "-p" in cmd
    assert "--output-format" in cmd


def test_95_treatments_and_invariants_unaffected_by_workspace_binding(tmp_path: Path) -> None:
    # Requirement: DEFAULT, CAVEMAN, MURMURS treatment identity, prompt digest, topology digest remain unaffected by workspace binding
    ws1 = tmp_path / "ws_arm1"
    ws2 = tmp_path / "ws_arm2"
    ws1.mkdir()
    ws2.mkdir()

    for mode in ("DEFAULT", "CAVEMAN", "MURMURS"):
        req1 = _base_request(
            communication_mode=mode,
            workspace_dir=str(ws1),
            caveman_policy_content=VALID_CAVEMAN_SKILL_MD if mode == "CAVEMAN" else None,
            raw_host_output=_mock_host_envelope(),
        )
        req2 = _base_request(
            communication_mode=mode,
            workspace_dir=str(ws2),
            caveman_policy_content=VALID_CAVEMAN_SKILL_MD if mode == "CAVEMAN" else None,
            raw_host_output=_mock_host_envelope(),
        )
        res1 = executor.execute_request(req1)
        res2 = executor.execute_request(req2)
        _validate_result_schema(res1)
        _validate_result_schema(res2)

        # Invariants preserved across distinct workspace directories
        assert res1["raw_evidence"]["task_prompt_digest"] == res2["raw_evidence"]["task_prompt_digest"]
        assert res1["raw_evidence"]["treatment_identity"] == res2["raw_evidence"]["treatment_identity"]
        assert res1["raw_evidence"]["topology_digest"] == res2["raw_evidence"]["topology_digest"]
        assert res1["governance_digest"] == res2["governance_digest"]
        assert res1["validation_digest"] == res2["validation_digest"]


def test_96_workspace_failure_preempts_live_host_call(tmp_path: Path) -> None:
    # Requirement: workspace failure happens before live host invocation or preflight
    invalid_ws = tmp_path / "non_existent_folder_xyz"
    settings_file = _create_mock_settings(tmp_path)
    version_runner_called = False
    runner_called = False

    def mock_version(cmd: list[str]) -> tuple[int, str, str]:
        nonlocal version_runner_called
        version_runner_called = True
        return (0, "1.1.15", "")

    def mock_runner(cmd: list[str], prompt: str = "") -> tuple[int, str, str]:
        nonlocal runner_called
        runner_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(workspace_dir=str(invalid_ws))
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version,
    )
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert not version_runner_called
    assert not runner_called


def test_97_no_fallback_to_scratch_directory(tmp_path: Path) -> None:
    # Requirement: no implicit fallback to ~/.gemini/antigravity-cli/scratch
    settings_file = _create_mock_settings(tmp_path)
    runner_called = False

    def mock_runner(cmd: list[str], prompt: str = "") -> tuple[int, str, str]:
        nonlocal runner_called
        runner_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(workspace_dir="")  # empty string workspace
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        runner_fn=mock_runner,
        settings_path=settings_file,
    )
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "INVALID_RUN"
    assert res["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert not runner_called


def test_98_workspace_via_task_payload_and_cli_argument(tmp_path: Path) -> None:
    # Requirement: workspace can be provided via task_payload, request root, or executor argument
    ws_arg = tmp_path / "ws_arg"
    ws_payload = tmp_path / "ws_payload"
    ws_arg.mkdir()
    ws_payload.mkdir()
    settings_file = _create_mock_settings(tmp_path)

    captured_cmds: list[list[str]] = []

    def mock_runner(cmd: list[str], prompt: str = "") -> tuple[int, str, str]:
        captured_cmds.append(cmd)
        return (0, json.dumps(_mock_host_envelope()), "")

    def mock_version(cmd: list[str]) -> tuple[int, str, str]:
        return (0, "1.1.15", "")

    # Argument overrides payload
    req = _base_request(workspace_dir=str(ws_payload))
    res = executor.execute_request(
        req,
        expected_cli_version="1.1.15",
        workspace_dir=ws_arg,
        runner_fn=mock_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version,
    )
    _validate_result_schema(res)

    assert res["outcome"]["status"] == "PASS"
    assert res["raw_evidence"]["workspace_binding"]["workspace_path"] == str(ws_arg.resolve())
    assert res["raw_evidence"]["workspace_binding"]["provenance"]["source"] == "EXECUTOR_ARGUMENT"
    assert captured_cmds[-1][captured_cmds[-1].index("--add-dir") + 1] == str(ws_arg.resolve())


def test_99_zero_live_antigravity_invocation_across_all_workspace_tests(tmp_path: Path) -> None:
    # Requirement: no test executes real Antigravity model turn
    ws = tmp_path / "zero_live_ws"
    ws.mkdir()
    called = False

    def spy_runner(cmd: list[str], prompt: str = "") -> tuple[int, str, str]:
        nonlocal called
        called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    # When mock output is provided, runner is not called
    req = _base_request(workspace_dir=str(ws), raw_host_output=_mock_host_envelope())
    res = executor.execute_request(req, runner_fn=spy_runner)
    _validate_result_schema(res)

    assert not called
    assert res["outcome"]["status"] == "PASS"
    assert res["raw_evidence"]["workspace_binding"]["bound"] is True
