# Kontrolled Kaos Claude Code Installation Guide

Add the canonical marketplace and install the Kaos package:

```text
/plugin marketplace add Baelfyre/Kaos
/plugin install kaos@orchestra
```

Invoke Conductor with `/kaos:conductor`. The namespace is required; bare `/kaos` is not the Claude Code plugin command.

The former plugin ID was `orchestra`; the marketplace key remains `orchestra` to preserve its source registration. For an existing installation, confirm the new package is enabled and `/kaos:conductor` is available before removing the old entry:

```sh
claude plugin uninstall orchestra@orchestra
```

Use `CLAUDE.template.md` only when the project needs local guidance beyond the installed skills.
