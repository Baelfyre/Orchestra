param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$pythonScript = Join-Path $PSScriptRoot "validate_structure.py"

python $pythonScript
exit $LASTEXITCODE
