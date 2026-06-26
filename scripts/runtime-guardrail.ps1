# Programmatic Runtime Guardrail Check for Orchestra AI workflows
# Checks files/changes for potential secrets, copyleft licensing, PII leaks, destructive operations, or cross-repo modifications.

param(
    [string]$TargetDir = (Split-Path -Parent $PSScriptRoot),
    [switch]$StagedOnly,
    [switch]$Enabled,
    [switch]$Enforce
)

$ErrorActionPreference = 'Stop'

# Source common helpers
$helpers = Join-Path $PSScriptRoot 'helpers.ps1'
if (Test-Path $helpers) {
    . $helpers
}

# Resolve activation flags
$isRun = $Enabled -or ($env:ORCHESTRA_RUN_GUARDRAILS -eq 'true')
$isEnforce = $Enforce -or ($env:ORCHESTRA_ENFORCE_GUARDRAILS -eq 'true')

if (-not $isRun) {
    Write-Host "SKIPPED: Guardrails disabled." -ForegroundColor Yellow
    exit 0
}

Write-ColorHost 'INFO' 'Orchestra Programmatic Guardrail: Commencing scanning...'
if (-not $isEnforce) {
    Write-ColorHost 'INFO' 'Enforcement is disabled (warning-only mode). Warnings will not block commit.'
}

$violations = @()

# 1. Gather files/changes to scan
$filesToScan = @()
if ($StagedOnly) {
    try {
        $staged = git diff --name-only --cached 2>$null
        if ($LASTEXITCODE -eq 0 -and $staged) {
            foreach ($f in $staged) {
                $fullPath = Join-Path $TargetDir $f
                if (Test-Path -LiteralPath $fullPath -PathType Leaf) {
                    $filesToScan += [PSCustomObject]@{ Path = $fullPath; Relative = $f }
                }
            }
        }
    }
    catch {
        Write-ColorHost 'WARNING' 'Git diff failed or not a git repo. Scanning target directory recursively instead.'
    }
}

if ($filesToScan.Count -eq 0) {
    # Scan target directory recursively (skipping standard exclusions)
    $files = Get-ChildItem -Path $TargetDir -Recurse -File | Where-Object {
        $_.FullName -notmatch '[\\/]\.git[\\/]' -and
        $_.FullName -notmatch '[\\/]\.amalgam[\\/]' -and
        $_.FullName -notmatch '[\\/]tests[\\/]' -and
        $_.FullName -notmatch '[\\/]brain[\\/]' -and
        $_.Name -ne 'runtime-guardrail.ps1' -and
        $_.Extension -notin @('.ico', '.png', '.jpg', '.zip', '.tar', '.gz')
    }
    foreach ($f in $files) {
        $relative = $f.FullName.Substring($TargetDir.Length + 1)
        $filesToScan += [PSCustomObject]@{ Path = $f.FullName; Relative = $relative }
    }
}

# 2. Scans
foreach ($item in $filesToScan) {
    # Skip self and documentation when scanning for their own documented patterns
    if ($item.Relative -match 'runtime-guardrail\.ps1|VALIDATION\.md') {
        continue
    }

    $content = Get-Content -LiteralPath $item.Path -Raw
    $lines = @(Get-Content -LiteralPath $item.Path)

    # A. Secrets Check
    $secretPatterns = @{
        'AWS Access Key ID'  = '\bAKIA[0-9A-Z]{16}\b'
        'Slack Webhook'      = 'https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+'
        'Generic API Key'    = '(?i)api[_-]?key\s*[:=]\s*["''][A-Za-z0-9_\-+=]{16,}["'']'
        'Private Key Header' = '-----BEGIN[ A-Z]+PRIVATE KEY-----'
    }

    foreach ($key in $secretPatterns.Keys) {
        $pattern = $secretPatterns[$key]
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match $pattern) {
                $violations += "SECRET EXPOSURE ($key) in $($item.Relative):L$($i + 1) -> $($lines[$i].Trim())"
            }
        }
    }

    # B. License Compliance Check
    if ($item.Relative -match 'package\.json|dependencies|plugin\.json') {
        $copyleftPatterns = @('(?i)"gpl', '(?i)"agpl', '(?i)"lgpl', '(?i)"copyleft')
        for ($i = 0; $i -lt $lines.Count; $i++) {
            foreach ($p in $copyleftPatterns) {
                if ($lines[$i] -match $p) {
                    $violations += "COPYLEFT LICENSE DETECTED ($($lines[$i].Trim())) in $($item.Relative):L$($i + 1). Please confirm compatibility."
                }
            }
        }
    }

    # C. PII Detection
    $piiPatterns = @('(?i)\bSSN\b', '(?i)\bsocial\s+security\b', '(?i)\bcredit\s*card\b', '(?i)\bcard[_-]?number\b')
    $hasPii = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        foreach ($p in $piiPatterns) {
            if ($lines[$i] -match $p) {
                $hasPii = $true
                $violations += "PII SENSITIVE FIELD DETECTED ($($lines[$i].Trim())) in $($item.Relative):L$($i + 1)."
            }
        }
    }

    if ($hasPii) {
        $privacyDocs = @('PrivacyPolicy.md', 'PRIVACY_POLICY.md', 'PRIVACY.md', 'docs/PRIVACY.md', 'docs/governance/PRIVACY.md')
        $hasPrivacyDoc = $false
        foreach ($doc in $privacyDocs) {
            if (Test-Path (Join-Path $TargetDir $doc)) {
                $hasPrivacyDoc = $true
                break
            }
        }
        if (-not $hasPrivacyDoc) {
            $violations += "PRIVACY GAPS: PII fields collected in $($item.Relative) but no PRIVACY_POLICY.md file was found."
        }
    }

    # D. Destructive Operations Guard
    $destructivePatterns = @{
        'Force deletion'          = '(?i)\brm\s+-rf\b'
        'Destructive Remove-Item' = '(?i)\bremove-item\b.*\b-force\b'
        'Raw Disk Formatting'     = '(?i)\bformat-volume\b|(?i)\bclear-disk\b'
    }
    foreach ($key in $destructivePatterns.Keys) {
        $pattern = $destructivePatterns[$key]
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match $pattern) {
                $violations += "DESTRUCTIVE OPERATION DETECTED ($key) in $($item.Relative):L$($i + 1) -> $($lines[$i].Trim())"
            }
        }
    }

    # E. Unsafe Command Execution Guard
    $unsafePatterns = @{
        'Invoke-Expression' = '(?i)\binvoke-expression\b|(?i)\biex\b'
    }
    foreach ($key in $unsafePatterns.Keys) {
        $pattern = $unsafePatterns[$key]
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match $pattern) {
                $violations += "UNSAFE EXECUTION DETECTED ($key) in $($item.Relative):L$($i + 1) -> $($lines[$i].Trim())"
            }
        }
    }

    # F. Forbidden Repository Target Guard
    $statePath = Join-Path $TargetDir ".amalgam/state.json"
    if (Test-Path -LiteralPath $statePath) {
        $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        if ($state.forbidden_repos) {
            foreach ($forbidden in $state.forbidden_repos) {
                # Convert windows backslashes to generic comparison
                $normPath = $item.Relative -replace '\\','/'
                $normForbidden = $forbidden -replace '\\','/'
                if ($normPath -match [regex]::Escape($normForbidden)) {
                    $violations += "FORBIDDEN TARGET MUTATION in $($item.Relative): Modifying forbidden repository area '$forbidden'."
                }
            }
        }
    }

    # G. Stale Routing Reference Guard
    # Ignore allowed legacy alias files/tests
    $isAllowedAlias = $item.Relative -replace '\\','/' -match 'aliases\.json|commands/|tests/|plugin\.json|\.codex-plugin/plugin\.json|scripts/refresh-installed-integrations\.ps1|README\.md|ROUTING_MAP\.md|docs/project/|DECISION_LOG\.md|SESSION_HANDOFF\.md|skills/conductor/SKILL\.md|examples/plugin-manifest\.example\.json'
    if (-not $isAllowedAlias) {
        $legacyNames = @(
            'amalgam-conductor', 'cloak-meister', 'scribe-meister', 'clockwork-meister',
            'meister-chronicler', 'acme-overseer', 'hidden-dagger', 'cipher-meister', 'meister-weaver'
        )
        foreach ($ln in $legacyNames) {
            for ($i = 0; $i -lt $lines.Count; $i++) {
                if ($lines[$i] -match $ln) {
                    $violations += "STALE REFERENCE DETECTED (Legacy name '$ln') in $($item.Relative):L$($i + 1) -> $($lines[$i].Trim())"
                }
            }
        }
    }
}

# 3. Report Results
if ($violations.Count -gt 0) {
    if ($isEnforce) {
        Write-ColorHost 'ERROR' "Guardrail scan failed with $($violations.Count) safety violations:"
        foreach ($v in $violations) {
            Write-ColorHost 'ERROR' " - $v"
        }
        Write-Host "`n[WHAT FAILED] Repository files or changes violated Orchestra's runtime guardrails." -ForegroundColor Red
        Write-Host "[WHY IT FAILED] Active safety checks blocked the operation due to unsafe patterns (e.g. secrets, copyleft licenses, PII leaks, destructive commands, or stale naming references)." -ForegroundColor Red
        Write-Host "[HOW TO FIX IT] Review the specific files and line numbers flagged above. Address the violations by removing sensitive strings, cleaning up commands, or replacing legacy names with clean slugs. To run locally without blocking, disable enforcement or omit the -Enforce parameter." -ForegroundColor Yellow
        exit 1
    } else {
        Write-ColorHost 'WARNING' "Guardrail scan found $($violations.Count) potential warnings (Warning-Only Mode):"
        foreach ($v in $violations) {
            Write-ColorHost 'WARNING' " - $v"
        }
        Write-Host "`n[WHAT FAILED] Potential safety warnings were detected by the guardrail scanner." -ForegroundColor Yellow
        Write-Host "[WHY IT FAILED] Staged or changed files contain patterns that would block commits under active enforcement." -ForegroundColor Yellow
        Write-Host "[HOW TO FIX IT] Address the warning details above. To enforce these rules on commits, set the environment variable: `$env:ORCHESTRA_ENFORCE_GUARDRAILS = 'true'` or run with the `-Enforce` parameter." -ForegroundColor Cyan
        exit 0
    }
}

Write-ColorHost 'SUCCESS' 'Guardrail scan passed successfully! No safety issues found.'
exit 0
