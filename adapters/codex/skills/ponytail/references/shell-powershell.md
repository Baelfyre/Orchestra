# Shell and PowerShell Implementation Reference

## Use When

Load only after repository evidence confirms shell or PowerShell scripts are part of the supported workflow. Preserve cross-platform requirements, execution-policy assumptions, quoting style, error semantics, and existing helper functions.

## General Rules

- Treat paths, arguments, environment values, and user input as data, not executable code.
- Quote values according to the shell actually executing the script.
- Avoid dynamic command-string evaluation. Prefer direct process invocation and argument arrays.
- Prefer argument arrays or native command invocation over building command strings.
- Fail on real errors and preserve useful diagnostics.
- Make destructive behavior explicit and separately authorized.
- Keep scripts idempotent when they may be rerun.

## POSIX Shell

When Bash is confirmed, strict mode may be useful if compatible with existing script behavior:

```bash
set -euo pipefail
```

Do not add it blindly to a legacy script because it can change failure semantics.

Quote parameter expansions:

```bash
config_path="$root/config/settings.json"
python "$script_path" --config "$config_path"
```

Use arrays in Bash when passing multiple arguments:

```bash
args=(--check --format json)
python "$script" "${args[@]}"
```

Use temporary directories through established platform or repository helpers. Register cleanup only through a bounded cleanup primitive whose target is the verified temporary directory created by the current operation. Do not place broad recursive-force deletion commands in reusable specialist guidance.

Destructive cleanup must remain within an explicitly created temporary path and any broader deletion requires separate authorization.

## PowerShell

Prefer cmdlet parameters and arrays instead of concatenated command strings.

```powershell
$path = Join-Path $Root "config\settings.json"
& python $ScriptPath --config $path
if ($LASTEXITCODE -ne 0) {
    throw "Validation failed with exit code $LASTEXITCODE"
}
```

Use `-LiteralPath` when a path should not interpret wildcard characters.

```powershell
if (Test-Path -LiteralPath $path -PathType Leaf) {
    Get-Content -LiteralPath $path -Raw
}
```

For native commands, check `$LASTEXITCODE`. For PowerShell cmdlets, use exceptions/`-ErrorAction Stop` where failure must stop execution.

```powershell
Copy-Item -LiteralPath $source -Destination $target -ErrorAction Stop
```

Prefer `Join-Path` and .NET path APIs over hand-built separators for portable repository tooling.

## Environment Variables

Read environment variables without printing secrets. Preserve existing precedence rules.

PowerShell:

```powershell
$mode = $env:ORCHESTRA_MODE
```

Bash:

```bash
mode="${ORCHESTRA_MODE:-}"
```

Do not persist secret environment values into tracked config, logs, or command output.

## Cross-Platform Scripts

When the same workflow runs on Windows and POSIX:
- prefer cross-platform runtimes already used by the repo, such as Python or Node, for complex shared logic;
- keep host-specific wrappers thin;
- do not assume `bash`, `python3`, GNU flags, Windows drive letters, or PowerShell availability without evidence;
- normalize line endings only when the repository contract requires it;
- test path handling and subprocess behavior on supported OS runners.

## Process Execution

Avoid invoking a shell when direct process execution is available. Pass arguments separately to prevent quoting/injection bugs.

Python example of the preferred subprocess shape:

```python
subprocess.run(["git", "status", "--short"], check=True)
```

Do not replace this with `shell=True` merely for convenience.

## Common Failure Patterns

Avoid:
- unquoted shell expansions;
- dynamic command-string evaluation for ordinary command execution;
- treating PowerShell cmdlet success and native-process exit codes as identical;
- relying on Bash-only builtins in commands consumed by PowerShell hosts;
- hardcoded machine paths;
- recursive force deletion outside a verified temporary/sandbox path;
- swallowing command failures and continuing to a success message.
