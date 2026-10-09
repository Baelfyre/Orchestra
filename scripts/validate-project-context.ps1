param (
    [string]$Mode,
    [string]$ContextFile
)

$ErrorActionPreference = 'Stop'
$pythonArgs = @()
if ($Mode) { $pythonArgs += "--mode"; $pythonArgs += $Mode }
if ($ContextFile) { $pythonArgs += "--context-file"; $pythonArgs += $ContextFile }

python "$PSScriptRoot\validate_project_context.py" @pythonArgs
exit $LASTEXITCODE
