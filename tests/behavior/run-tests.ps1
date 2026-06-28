$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

$scripts = @(
    @{ Name = "validate-structure.ps1"; Path = "scripts/validate-structure.ps1" },
    @{ Name = "validate-manifest.ps1"; Path = "scripts/validate-manifest.ps1" },
    @{ Name = "check-stale-references.ps1"; Path = "scripts/check-stale-references.ps1" },
    @{ Name = "validate-codex-export.ps1"; Path = "adapters/codex/validate-codex-export.ps1" },
    @{ Name = "evaluate-governance.ps1"; Path = "tests/behavior/evaluate-governance.ps1" },
    @{ Name = "runtime-guardrail.ps1"; Path = "scripts/runtime-guardrail.ps1" }
)

$failed = $false

foreach ($s in $scripts) {
    Write-Host "========================================"
    Write-Host "Running $($s.Name)..."
    Write-Host "========================================"
    
    $fullPath = Join-Path $Root $s.Path
    $psExe = (Get-Process -Id $PID).Path
    & $psExe -NoProfile -ExecutionPolicy Bypass -File $fullPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: $($s.Name) failed with exit code $LASTEXITCODE!" -ForegroundColor Red
        $failed = $true
    } else {
        Write-Host "SUCCESS: $($s.Name) passed." -ForegroundColor Green
    }
}

# ====================================================================
# Regression Tests for Guardrails & State Locking (Phase 5)
# ====================================================================
Write-Host "`n========================================"
Write-Host "Running Guardrail & Lock Regression Tests..."
Write-Host "========================================"

$guardrailScript = Join-Path $Root "scripts/runtime-guardrail.ps1"
$lockScript = Join-Path $Root "scripts/manage-state-lock.ps1"

# Test 1: Guardrail enforcement on isolated mock fixture
$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) "orchestra-guardrail-test-$(New-Guid)"
New-Item -ItemType Directory -Path $tempDir | Out-Null
try {
    $violationFile = Join-Path $tempDir "mock_secrets.txt"
    Set-Content -Path $violationFile -Value "AWS_SECRET = AKIA1234567890ABCDEF" -Encoding UTF8

    & $psExe -NoProfile -ExecutionPolicy Bypass -File $guardrailScript -TargetDir $tempDir -Enabled -Enforce
    $enforceExit = $LASTEXITCODE

    & $psExe -NoProfile -ExecutionPolicy Bypass -File $guardrailScript -TargetDir $tempDir -Enabled
    $warnExit = $LASTEXITCODE

    if ($enforceExit -ne 1) {
        Write-Host "ERROR: Guardrail did not fail on violation in enforce mode! (Exit code: $enforceExit)" -ForegroundColor Red
        $failed = $true
    } elseif ($warnExit -ne 0) {
        Write-Host "ERROR: Guardrail failed on warning-only mode! (Exit code: $warnExit)" -ForegroundColor Red
        $failed = $true
    } else {
        Write-Host "SUCCESS: Guardrail warning-first and enforcement tests passed." -ForegroundColor Green
    }
}
finally {
    if (Test-Path -LiteralPath $tempDir) {
        Remove-Item -LiteralPath $tempDir -Recurse -Force | Out-Null
    }
}

# Test 2: Project Context Validator on mock fixture
$contextScript = Join-Path $Root "scripts/validate-project-context.ps1"
$tempDir2 = Join-Path ([System.IO.Path]::GetTempPath()) "orchestra-context-test-$(New-Guid)"
New-Item -ItemType Directory -Path $tempDir2 | Out-Null
try {
    # Test missing file warning mode
    & $psExe -NoProfile -ExecutionPolicy Bypass -File $contextScript -Mode "Implementation Mode" -ContextFile (Join-Path $tempDir2 "MISSING.md")
    $warnExit = $LASTEXITCODE

    # Test missing file error mode
    & $psExe -NoProfile -ExecutionPolicy Bypass -File $contextScript -Mode "Release Mode" -ContextFile (Join-Path $tempDir2 "MISSING.md")
    $errExit = $LASTEXITCODE

    if ($warnExit -ne 0) {
        Write-Host "ERROR: Context validator failed in warning mode! (Exit code: $warnExit)" -ForegroundColor Red
        $failed = $true
    } elseif ($errExit -ne 1) {
        Write-Host "ERROR: Context validator did not fail in Release mode! (Exit code: $errExit)" -ForegroundColor Red
        $failed = $true
    } else {
        Write-Host "SUCCESS: Context validator tests passed." -ForegroundColor Green
    }
}
finally {
    if (Test-Path -LiteralPath $tempDir2) {
        Remove-Item -LiteralPath $tempDir2 -Recurse -Force | Out-Null
    }
}

# Test 3: State Locking tests
& $psExe -NoProfile -ExecutionPolicy Bypass -File $lockScript -Action Release | Out-Null

& $psExe -NoProfile -ExecutionPolicy Bypass -File $lockScript -Action Acquire -ProcessId $PID | Out-Null
$acquireExit = $LASTEXITCODE

& $psExe -NoProfile -ExecutionPolicy Bypass -File $lockScript -Action Check | Out-Null
$checkExit = $LASTEXITCODE

& $psExe -NoProfile -ExecutionPolicy Bypass -File $lockScript -Action Release | Out-Null
$releaseExit = $LASTEXITCODE

& $psExe -NoProfile -ExecutionPolicy Bypass -File $lockScript -Action Check | Out-Null
$checkExitAfter = $LASTEXITCODE

if ($acquireExit -ne 0) {
    Write-Host "ERROR: Lock acquisition failed!" -ForegroundColor Red
    $failed = $true
} elseif ($checkExit -ne 1) {
    Write-Host "ERROR: Lock collision check did not detect active lock! (Exit code: $checkExit)" -ForegroundColor Red
    $failed = $true
} elseif ($releaseExit -ne 0) {
    Write-Host "ERROR: Lock release failed!" -ForegroundColor Red
    $failed = $true
} elseif ($checkExitAfter -ne 0) {
    Write-Host "ERROR: Lock check still active after release! (Exit code: $checkExitAfter)" -ForegroundColor Red
    $failed = $true
} else {
    Write-Host "SUCCESS: Lock acquisition, collision protection, and release tests passed." -ForegroundColor Green
}

Write-Host "`n========================================"
if ($failed) {
    Write-Host "Validation suite FAILED." -ForegroundColor Red
    exit 1
} else {
    Write-Host "Validation suite PASSED!" -ForegroundColor Green
    exit 0
}
