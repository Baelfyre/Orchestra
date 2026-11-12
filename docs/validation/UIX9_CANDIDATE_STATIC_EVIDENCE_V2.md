# UIX-9 candidate static evidence V2

This additive contract separates historical UIX-9 V1 verification from static evidence for a modified guidance candidate.

- `FROZEN_HISTORICAL_V1` reads the manifest and identity from manifest-snapshot commit `9f49a29827513199ae16ea29b8e75bfbb90ca38d`, then reads its guidance materials from source commit `bf6f14316fa8814eeac91440c4a7d70be0d04b9e`. The frozen digest remains `f989ac579875fbcd349f812fa6e241ba5c8505f9f940abcb5e0e30006f1606ab`.
- `CANDIDATE_STATIC_V2` reads the current candidate manifest and material bytes. Its guidance digest, per-file hashes, base SHA/tree, and unstaged content fingerprint are independently bound. The V1 manifest schema and frozen records are unchanged.
- Guidance text is normalized to UTF-8/LF. The digest hashes sorted `path<TAB>sha256<TAB>role<TAB>revision_identity` rows joined with LF.
- Evidence status is limited to `DRAFT_DIAGNOSTIC` or `STATIC_EVIDENCE_PENDING_REVIEW`. Pending review requires all 58 UIX9 cases to pass with zero skips. Neither status is approval, live-host authorization, merge approval, or publication approval.
- Test logs and JUnit XML are SHA-256 checked as regular non-symlink files outside the repository. Their test case names and outcomes are included in the record.
- Frozen evaluator and validator digests are recomputed from frozen Git objects. Candidate source digests are recorded separately.

After local validation, create the evidence JSON outside the repository. The `--runs` input is an external JSON array containing observed `suite_id`, exact `command`, process `exit_code`, `log_path`, and `junit_path` for each run:

```powershell
python -B scripts/uix9_static_evidence_v2.py --root . --schema machine/schemas/uix9-candidate-static-evidence.v2.schema.json --runs <external-runs.json> --output <external-evidence.json>
```

Static V2 evidence cannot authorize UIX9B/UIX9C execution and does not change the existing live gates.