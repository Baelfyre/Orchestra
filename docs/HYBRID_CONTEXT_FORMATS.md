# Hybrid context formats

Orchestra uses Markdown, JSON, JSON Schema/JSONL, and TOON for different responsibilities. TOON is a derived AI-context representation only and never becomes repository authority.

## Representation roles

| Format | Role |
| --- | --- |
| Markdown | Human explanation, rationale, examples, troubleshooting, and progressive-disclosure guidance |
| JSON | Canonical machine state, identity, routing, governance, receipts, manifests, provenance, and normalized execution evidence |
| JSON Schema | Validation contracts for canonical machine records |
| JSONL | Append-only event/history streams where applicable |
| TOON | Optional derived AI-facing context for large or repetitive structured data after authority, schema, and drift checks |

## Context compilation rule

`canonical JSON -> authority/drift validation -> bounded selection -> measured serializer choice -> TOON or compact JSON -> AI`

TOON is selected only when the source is large enough and the encoded projection provides material measured savings. Small, deeply nested, irregular, or non-beneficial records fall back to compact JSON.

The default compiler thresholds are 4 KiB of compact JSON and at least 10 percent measured byte savings. These are context-transport defaults, not authority rules, and may be benchmarked later against live host tokenization.

## Long command, Git, test, and CI output

Raw stdout/stderr remains evidence and is written to files. The PowerShell execution wrapper creates:

1. raw `stdout.log` and `stderr.log`;
2. SHA-256 hashes for both logs;
3. the existing JSON validation execution receipt shape;
4. bounded JSON summaries containing head/tail and signal lines;
5. a derived context projection selected as TOON or compact JSON;
6. a JSON projection manifest binding source semantic digest and projection digest.

Successful runs therefore do not require an agent to ingest thousands of raw console lines. On failure, the agent can progressively disclose the raw log or a relevant slice while retaining the original evidence hashes.

## Authority and drift boundaries

- TOON authority is `NONE_DERIVED_CONTEXT_ONLY`.
- Promotion from TOON directly into canonical state is forbidden.
- A projection must match both its source semantic SHA-256 and its own projection SHA-256.
- Source-state drift between otherwise valid canonical records must be resolved before compilation; serialization cannot resolve conflicting authority.
- Live external source reality must still be re-read where the governing workflow requires it.
- Raw logs and canonical JSON receipts are retained even when an AI-facing TOON projection is emitted.

## Commands

Compile an existing JSON context record:

```powershell
python scripts/context_compiler.py compile input.json context.compiled context-manifest.json
python scripts/context_compiler.py verify input.json context.compiled context-manifest.json
```

Run a verbose command without sending the full output to the AI by default:

```powershell
./scripts/invoke-contextual-command.ps1 `
  -CommandId validate-runtime `
  -FilePath python `
  -ArgumentList @("-m", "pytest", "-q")
```

The wrapper returns only the verdict and evidence/context paths to the console. Full raw output remains available under the evidence directory for diagnosis.
