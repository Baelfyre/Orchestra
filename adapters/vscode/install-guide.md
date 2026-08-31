# VS Code Installation Guide

1. Keep the full skill folders in a local documentation or tools directory if needed.
2. Use Conductor to choose the smallest relevant skill text.
3. Copy or reference that skill in workspace instructions where supported.
4. Use the scaffold-only `package.json` only as packaging metadata that points to the shared `VSCodeAdapter`.
5. Do not assume automatic skill discovery unless the extension is configured for it.

## Optional P2.2B provider qualification workflow

This workflow observes an already configured VS Code environment. It does not install providers, extensions, credentials, or models.

1. Use an exact Orchestra revision and confirm `git status --porcelain` is empty.
2. Start a new VS Code agent session.
3. Explicitly select the Session Target harness you intend to observe, such as Copilot, Claude, or Codex.
4. Record the exact visible model and the provider/source grouping shown by VS Code when available.
5. Ask the selected session to read `tests/fixtures/vscode-provider-qualification/fixture-v1.json` and return its stored challenge values without editing repository files.
6. Confirm the repository is still clean.
7. Preserve bounded evidence for the harness, model, provider source, fixture result, repository revision, and clean before/after state. Do not capture credentials or secrets.
8. Encode that evidence in a `orchestra.vscode-provider-observation.v1` JSON record.
9. Validate it with:

```sh
python scripts/qualify_vscode_provider.py --input observation.json --output receipt.json
```

A passing receipt is evidence only. It does not grant provider execution, automatic routing, merge, release, deployment, or policy authority.

See [`../../docs/project/PRIORITY_2_VSCODE_MULTI_HARNESS_QUALIFICATION.md`](../../docs/project/PRIORITY_2_VSCODE_MULTI_HARNESS_QUALIFICATION.md) for the full contract and classification rules.
