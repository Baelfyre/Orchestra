$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$evalsFile = Join-Path $PSScriptRoot "governance-conformance-fixtures.json"

if (-not (Test-Path $evalsFile)) {
    Write-Host "ERROR: Evals fixture not found at $evalsFile" -ForegroundColor Red
    exit 1
}

$evals = Get-Content $evalsFile -Raw | ConvertFrom-Json
$failed = $false

Write-Host "[INFO] Governance instruction conformance checks: Validating static behavioral expectations in source rules..."

foreach ($eval in $evals) {
    $filePath = $eval.file

    if ($filePath) {
        $sourcePath = Join-Path $Root $filePath
        if (Test-Path $sourcePath) {
            $skillPath = $sourcePath
        } else {
            Write-Host "FAIL: $($eval.scenario) -> File not found: $sourcePath" -ForegroundColor Red
            $failed = $true
            continue
        }
    } else {
        # Check source repo first, then optional .agents directory alignment
        $sourcePath = Join-Path $Root "skills\$($eval.skill)\SKILL.md"
        $agentPath = Join-Path $Root ".agents\skills\$($eval.skill)\SKILL.md"

        if (Test-Path $sourcePath) {
            $skillPath = $sourcePath
        } elseif (Test-Path $agentPath) {
            $skillPath = $agentPath
            Write-Host "WARNING: Validating local .agents copy for $($eval.skill), source missing in skills/" -ForegroundColor Yellow
        } else {
            Write-Host "FAIL: $($eval.scenario) -> Skill file not found: $sourcePath" -ForegroundColor Red
            $failed = $true
            continue
        }
    }

    $content = Get-Content $skillPath -Raw
    
    if ([regex]::IsMatch($content, $eval.pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
        Write-Host "PASS: $($eval.scenario)" -ForegroundColor Green
    } else {
        Write-Host "FAIL: $($eval.scenario) -> Rule missing or contradicted in $skillPath" -ForegroundColor Red
        $failed = $true
    }
}

if ($failed) {
    Write-Host "[ERROR] Governance instruction conformance checks failed!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "[SUCCESS] All static behavioral expectation checks passed." -ForegroundColor Green
    exit 0
}
