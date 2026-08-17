param(
    [Parameter(Mandatory = $true)] [string] $CommandId,
    [Parameter(Mandatory = $true)] [string] $FilePath,
    [string[]] $ArgumentList = @(),
    [string] $EvidenceDir = "artifacts/context-execution",
    [string] $Python = "python",
    [int] $MinContextBytes = 4096,
    [double] $MinToonSavingsPercent = 10.0
)

$ErrorActionPreference = "Stop"

function Get-Sha256([string] $Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        return ("0" * 64)
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Convert-ToPortablePath([string] $Path) {
    return $Path.Replace('\', '/')
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$compiler = Join-Path $root "internal/context/context_compiler.py"
$evidenceRoot = Join-Path $root $EvidenceDir
$runDir = Join-Path $evidenceRoot $CommandId
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$stdoutPath = Join-Path $runDir "stdout.log"
$stderrPath = Join-Path $runDir "stderr.log"
$stdoutSummaryPath = Join-Path $runDir "stdout-summary.json"
$stderrSummaryPath = Join-Path $runDir "stderr-summary.json"
$contextSourcePath = Join-Path $runDir "context-source.json"
$contextPath = Join-Path $runDir "context.compiled"
$contextManifestPath = Join-Path $runDir "context-manifest.json"
$receiptPath = Join-Path $runDir "validation-execution-receipt.json"

$headBefore = (& git -C $root rev-parse HEAD 2>$null)
$started = [DateTimeOffset]::UtcNow

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $FilePath
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.WorkingDirectory = $root
foreach ($arg in $ArgumentList) {
    [void] $psi.ArgumentList.Add($arg)
}

$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $psi
[void] $process.Start()

# Read both redirected streams concurrently. Sequential ReadToEnd calls can block
# when a verbose child process fills the other redirected stream's buffer.
$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$process.WaitForExit()
$stdout = $stdoutTask.GetAwaiter().GetResult()
$stderr = $stderrTask.GetAwaiter().GetResult()
$exitCode = $process.ExitCode
$finished = [DateTimeOffset]::UtcNow

[System.IO.File]::WriteAllText($stdoutPath, $stdout, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($stderrPath, $stderr, [System.Text.UTF8Encoding]::new($false))

& $Python $compiler summarize-log $stdoutPath $stdoutSummaryPath
if ($LASTEXITCODE -ne 0) { throw "stdout summarization failed" }
& $Python $compiler summarize-log $stderrPath $stderrSummaryPath
if ($LASTEXITCODE -ne 0) { throw "stderr summarization failed" }

$stdoutSummary = Get-Content -Raw -LiteralPath $stdoutSummaryPath | ConvertFrom-Json
$stderrSummary = Get-Content -Raw -LiteralPath $stderrSummaryPath | ConvertFrom-Json
$headAfter = (& git -C $root rev-parse HEAD 2>$null)

$receipt = [ordered]@{
    schema_version = "1.0.0"
    command_id = $CommandId
    command = @($FilePath) + @($ArgumentList)
    exit_code = $exitCode
    verdict = if ($exitCode -eq 0) { "PASS" } else { "FAIL" }
    started_at = $started.ToString("o")
    finished_at = $finished.ToString("o")
    stdout_sha256 = Get-Sha256 $stdoutPath
    stderr_sha256 = Get-Sha256 $stderrPath
    head_before = $headBefore
    head_after = $headAfter
    evidence_ref = Convert-ToPortablePath $runDir
}
$receipt | ConvertTo-Json -Depth 10 | Set-Content -Encoding utf8NoBOM -LiteralPath $receiptPath

$contextSource = [ordered]@{
    schema_version = "orchestra.execution-context.v1"
    authority = "DERIVED_NON_AUTHORITATIVE"
    command_id = $CommandId
    verdict = $receipt.verdict
    exit_code = $exitCode
    started_at = $receipt.started_at
    finished_at = $receipt.finished_at
    head_before = $headBefore
    head_after = $headAfter
    receipt_path = Convert-ToPortablePath $receiptPath
    raw_evidence = [ordered]@{
        stdout_path = Convert-ToPortablePath $stdoutPath
        stdout_sha256 = $receipt.stdout_sha256
        stderr_path = Convert-ToPortablePath $stderrPath
        stderr_sha256 = $receipt.stderr_sha256
    }
    stdout = $stdoutSummary
    stderr = $stderrSummary
}
$contextSource | ConvertTo-Json -Depth 20 | Set-Content -Encoding utf8NoBOM -LiteralPath $contextSourcePath

& $Python $compiler compile $contextSourcePath $contextPath $contextManifestPath `
    --source-identity (Convert-ToPortablePath $receiptPath) `
    --min-bytes $MinContextBytes `
    --min-savings-percent $MinToonSavingsPercent
if ($LASTEXITCODE -ne 0) { throw "context compilation failed" }

& $Python $compiler verify $contextSourcePath $contextPath $contextManifestPath
if ($LASTEXITCODE -ne 0) { throw "context projection parity failed" }

Write-Output "ORCHESTRA_COMMAND_ID=$CommandId"
Write-Output "ORCHESTRA_VERDICT=$($receipt.verdict)"
Write-Output "ORCHESTRA_EXIT_CODE=$exitCode"
Write-Output "ORCHESTRA_RECEIPT=$(Convert-ToPortablePath $receiptPath)"
Write-Output "ORCHESTRA_CONTEXT=$(Convert-ToPortablePath $contextPath)"
Write-Output "ORCHESTRA_CONTEXT_MANIFEST=$(Convert-ToPortablePath $contextManifestPath)"

exit $exitCode
