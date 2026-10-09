$helpers = Join-Path $PSScriptRoot 'helpers.ps1'
if (Test-Path $helpers) {
    . $helpers
}

$root = Get-ProjectRoot
$gitDir = Join-Path $root ".git"
if (-not (Test-Path -LiteralPath $gitDir -PathType Container)) {
    Write-ColorHost 'WARNING' 'Not a Git repository or .git folder not found. Skipping hook installation.'
    exit 0
}

$hookDir = Join-Path $gitDir "hooks"
if (-not (Test-Path -LiteralPath $hookDir -PathType Container)) {
    New-Item -ItemType Directory -Path $hookDir | Out-Null
}

$hookFile = Join-Path $hookDir "pre-commit"

$hookContent = @'
#!/bin/sh
# Orchestra pre-commit hook to enforce runtime guardrails programmatically

echo "[INFO] Running Orchestra pre-commit guardrail checks..."

if command -v pwsh >/dev/null 2>&1; then
  pwsh -NoProfile -ExecutionPolicy Bypass -Command '$env:ORCHESTRA_RUN_GUARDRAILS="true"; $env:ORCHESTRA_ENFORCE_GUARDRAILS="true"; ./scripts/runtime-guardrail.ps1 -StagedOnly'
else
  powershell -NoProfile -ExecutionPolicy Bypass -Command '$env:ORCHESTRA_RUN_GUARDRAILS="true"; $env:ORCHESTRA_ENFORCE_GUARDRAILS="true"; ./scripts/runtime-guardrail.ps1 -StagedOnly'
fi

exitCode=$?
if [ $exitCode -ne 0 ]; then
  echo "[ERROR] Pre-commit hook blocked commit due to Orchestra guardrail violations."
  exit 1
fi

exit 0
'@

[System.IO.File]::WriteAllText($hookFile, ($hookContent -replace "`r`n", "`n"))
Write-ColorHost 'SUCCESS' "Pre-commit hook installed successfully at $hookFile"
