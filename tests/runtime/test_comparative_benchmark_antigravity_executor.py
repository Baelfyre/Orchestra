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
    cli_version: str = "1.1.14",
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
    assert res["tokens"]["counter_id"] == "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"
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
    cid2 = executor.compute_counter_id("1.1.14", "gemini-3.7-flash-high", "json-usage")
    assert cid1 == "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"
    assert cid1 == cid2 == executor.DEFAULT_COUNTER_ID


def test_13_changed_cli_or_model_identity_changes_counter_identity() -> None:
    base_cid = executor.DEFAULT_COUNTER_ID

    cid_cli_change = executor.compute_counter_id(cli_version="1.2.0")
    assert cid_cli_change != base_cid
    assert cid_cli_change == "antigravity-cli-1.2.0:json-usage:gemini-3.7-flash-high"

    cid_model_change = executor.compute_counter_id(model="gemini-2.5-pro")
    assert cid_model_change != base_cid
    assert cid_model_change == "antigravity-cli-1.1.14:json-usage:gemini-2.5-pro"

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
        return (0, "1.1.14\n", "")

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


def test_18_preflight_accepts_exact_cli_version_1_1_14(tmp_path: Path) -> None:
    settings_file = _create_mock_settings(tmp_path, use_g1_credits=False)
    model_called = False

    def mock_version_runner(cmd: list[str]) -> tuple[int, str, str]:
        assert cmd == ["agy", "--version"]
        return (0, "antigravity-cli 1.1.14\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sample prompt")
    res = executor.execute_request(
        req,
        runner_fn=mock_model_runner,
        settings_path=settings_file,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res)

    assert model_called is True
    assert res["outcome"]["status"] == "PASS"
    assert res["raw_evidence"]["cli_version"] == "1.1.14"


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
        return (0, "1.1.14\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sample prompt")
    res = executor.execute_request(
        req,
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
        return (0, "1.1.14\n", "")

    def mock_model_runner(cmd: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal model_called
        model_called = True
        return (0, json.dumps(_mock_host_envelope()), "")

    req = _base_request(prompt="Sample prompt")
    res = executor.execute_request(
        req,
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
        return (0, "1.1.14\n", "")

    missing_settings = tmp_path / "non_existent_settings.json"
    req1 = _base_request(prompt="Sample prompt")
    res1 = executor.execute_request(
        req1,
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
        settings_path=malformed_settings,
        version_runner_fn=mock_version_runner,
    )
    _validate_result_schema(res2)
    assert res2["outcome"]["status"] == "INVALID_RUN"
    assert res2["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"

    missing_key_settings = _create_mock_settings(tmp_path / "sub", use_g1_credits=None)
    req3 = _base_request(prompt="Sample prompt")
    res3 = executor.execute_request(
        req3,
        settings_path=missing_key_settings,
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
    assert raw_ev["cli_version_provenance"]["source"] == "PREFLIGHT_COMMAND"
    assert raw_ev["cli_version_provenance"]["value"] == "1.1.14"
    assert raw_ev["model_provenance"]["source"] == "PINNED_COMMAND_ARGUMENT"
    assert raw_ev["model_provenance"]["value"] == "gemini-3.7-flash-high"
    assert raw_ev["usage_provenance"]["source"] == "HOST_REPORTED_JSON_USAGE"
    assert raw_ev["counter_id_provenance"]["provenance"] == "ORCHESTRA_ASSIGNED_MEASUREMENT_SURFACE"
    assert raw_ev["counter_id_provenance"]["vendor_assigned_claim"] is False
    assert raw_ev["counter_id_provenance"]["identifier"] == "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"


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
        assert run_record["tokens"]["counter_id"] == "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"
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
        assert res["tokens"]["counter_id"] == "antigravity-cli-1.1.14:stream-json-usage:gemini-3.7-flash-high"
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
    assert tok["counter_id"] == "antigravity-cli-1.1.14:stream-json-usage:gemini-3.7-flash-high"
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
    assert cid_json == "antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high"
    assert cid_stream == "antigravity-cli-1.1.14:stream-json-usage:gemini-3.7-flash-high"

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
