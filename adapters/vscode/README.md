# VS Code AI Adapter

Use selected skill Markdown as workspace instructions, prompt references, or local context documents. Automatic discovery depends on the installed AI extension and its configuration.

This folder also includes a scaffold-only `package.json` that points VS Code packaging metadata at the shared `VSCodeAdapter` runtime contract.

## Multi-harness provider qualification

The post-v1.7 P2.2B qualification layer treats VS Code as an observation environment for distinct Local, Copilot, Claude, and Codex harness/model paths.

It preserves these boundaries:

```text
HOST != HARNESS
HARNESS != PROVIDER_SOURCE
PROVIDER_SOURCE != PROVIDER
PROVIDER != MODEL
MODEL != AUTHORITY
```

The adapter scaffold does not automatically control VS Code sessions, choose models, install extensions, mutate credentials, or infer provider-native qualification from a model name.

Live evidence is user-controlled and validated through:

```text
python scripts/qualify_vscode_provider.py --input <observation.json> --output <receipt.json>
```

See [`../../docs/project/PRIORITY_2_VSCODE_MULTI_HARNESS_QUALIFICATION.md`](../../docs/project/PRIORITY_2_VSCODE_MULTI_HARNESS_QUALIFICATION.md) for the frozen fixture, evidence classifications, operator protocol, and non-authorizing boundary.

See [install-guide.md](install-guide.md), [workspace-instructions.template.md](workspace-instructions.template.md), and [package.json](package.json).
