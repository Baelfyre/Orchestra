import json
from pathlib import Path
import unittest

from orchestra_runtime.evidence import (
    EvidenceMismatchError,
    SourceStateReceipt,
    ValidationExecutionReceipt,
    build_validation_execution_receipt,
    receipt_digest,
)


REAL_HEAD = "8d819f84fcd422cc38cd0a0231f4d6781b3d42c1"
FAKE_SAME_PREFIX_HEAD = "8d819f8ecf3014a66e408ec202206bf06da62a80"
REAL_MAIN = "68d29dd386662b878db1d9ac7a3b83f46c21a341"
FAKE_SAME_PREFIX_MAIN = "68d29dd5496a715f5c908f5173da8722241cfb1c"
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestSourceStateReceipt(unittest.TestCase):
    def build_receipt(self) -> SourceStateReceipt:
        return SourceStateReceipt(
            repository="Baelfyre/Orderly",
            canonical_branch="main",
            live_canonical_sha=REAL_MAIN,
            pull_request_number=16,
            exact_pr_head=REAL_HEAD,
            merge_or_squash_sha=REAL_MAIN,
            verification_timestamp="2026-08-14T19:35:00Z",
            verification_method="GITHUB_API",
        )

    def test_rejects_short_sha_as_canonical_identity(self):
        with self.assertRaises(ValueError):
            SourceStateReceipt(
                repository="Baelfyre/Orderly",
                canonical_branch="main",
                live_canonical_sha="68d29dd",
                verification_timestamp="2026-08-14T19:35:00Z",
                verification_method="GITHUB_API",
            )

    def test_same_short_prefix_wrong_full_sha_fails_closed(self):
        receipt = self.build_receipt()
        with self.assertRaises(EvidenceMismatchError):
            receipt.assert_canonical_sha(FAKE_SAME_PREFIX_MAIN)
        with self.assertRaises(EvidenceMismatchError):
            receipt.assert_pr_head(FAKE_SAME_PREFIX_HEAD)

    def test_canonical_closeout_merge_must_match_live_main(self):
        with self.assertRaises(EvidenceMismatchError):
            SourceStateReceipt(
                repository="Baelfyre/Orderly",
                canonical_branch="main",
                live_canonical_sha=REAL_MAIN,
                pull_request_number=16,
                exact_pr_head=REAL_HEAD,
                merge_or_squash_sha=FAKE_SAME_PREFIX_MAIN,
                verification_timestamp="2026-08-14T19:35:00Z",
                verification_method="GITHUB_API",
            )

    def test_source_receipt_digest_is_deterministic(self):
        receipt = self.build_receipt()
        self.assertEqual(receipt.digest, receipt_digest(receipt.to_dict()))
        self.assertEqual(receipt.digest, self.build_receipt().digest)
        self.assertEqual(len(receipt.digest), 64)


class TestValidationExecutionReceipt(unittest.TestCase):
    def test_exit_code_derives_authoritative_verdict(self):
        receipt = build_validation_execution_receipt(
            command_id="git-diff-check",
            command=("git", "diff", "--check", "base..head"),
            exit_code=2,
            started_at="2026-08-15T05:00:00Z",
            finished_at="2026-08-15T05:00:01Z",
            stdout="trailing whitespace",
            stderr="",
            head_before=REAL_MAIN,
            head_after=REAL_MAIN,
        )
        self.assertEqual(receipt.verdict, "FAIL")
        self.assertEqual(receipt.to_dict()["verdict"], "FAIL")
        self.assertTrue(receipt.exact_state_preserved)

    def test_agent_claimed_pass_cannot_override_nonzero_exit(self):
        receipt = ValidationExecutionReceipt(
            command_id="git-diff-check",
            command=("git", "diff", "--check"),
            exit_code=2,
            started_at="2026-08-15T05:00:00Z",
            finished_at="2026-08-15T05:00:01Z",
            stdout_sha256=EMPTY_SHA256,
            stderr_sha256=EMPTY_SHA256,
        )
        with self.assertRaises(EvidenceMismatchError):
            receipt.assert_claimed_verdict("PASS")
        receipt.assert_claimed_verdict("FAIL")

    def test_verdict_cannot_be_injected_through_constructor(self):
        with self.assertRaises(TypeError):
            ValidationExecutionReceipt(
                command_id="git-diff-check",
                command=("git", "diff", "--check"),
                exit_code=2,
                started_at="2026-08-15T05:00:00Z",
                finished_at="2026-08-15T05:00:01Z",
                stdout_sha256=EMPTY_SHA256,
                stderr_sha256=EMPTY_SHA256,
                verdict="PASS",  # type: ignore[call-arg]
            )

    def test_receipt_hashes_stdout_and_stderr(self):
        receipt = build_validation_execution_receipt(
            command_id="noop",
            command=("python", "-c", "pass"),
            exit_code=0,
            started_at="2026-08-15T05:00:00+00:00",
            finished_at="2026-08-15T05:00:00Z",
        )
        self.assertEqual(receipt.stdout_sha256, EMPTY_SHA256)
        self.assertEqual(receipt.stderr_sha256, EMPTY_SHA256)
        self.assertEqual(receipt.verdict, "PASS")


class TestPublishedSchemas(unittest.TestCase):
    def test_schema_documents_are_strict_and_versioned(self):
        root = Path(__file__).resolve().parents[2]
        for name in (
            "source-state-receipt.schema.json",
            "validation-execution-receipt.schema.json",
        ):
            with (root / "machine" / "schemas" / name).open("r", encoding="utf-8") as handle:
                schema = json.load(handle)
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0.0")

        with (root / "machine" / "schemas" / "validation-execution-receipt.schema.json").open("r", encoding="utf-8") as handle:
            validation_schema = json.load(handle)
        self.assertEqual(validation_schema["properties"]["verdict"]["enum"], ["PASS", "FAIL"])
        self.assertIn("verdict", validation_schema["required"])


if __name__ == "__main__":
    unittest.main()
