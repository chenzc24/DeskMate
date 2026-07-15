# Windows PowerShell 5.1 surfaces native stderr (including harmless pip notices)
# as ErrorRecord objects. Native exit codes below remain the authority.
$ErrorActionPreference = 'Continue'

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
$env:PIP_PROGRESS_BAR = 'off'

if (-not (Test-Path -LiteralPath $Python)) {
    py -3.12 -m venv (Join-Path $Root '.venv')
}

& $Python -m pip install `
    'torch==2.11.0' `
    'torchvision==0.26.0' `
    --index-url 'https://download.pytorch.org/whl/cu128'
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python -m pip install -r (Join-Path $Root 'requirements-training.txt')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Expected = Get-Content -ErrorAction Stop -LiteralPath (Join-Path $Root 'requirements-training.lock.txt') |
    Where-Object { $_.Trim() }
$Actual = & $Python -m pip freeze | Where-Object { $_.Trim() }
$Difference = Compare-Object -ReferenceObject $Expected -DifferenceObject $Actual
if ($Difference) {
    $Difference | Format-Table -AutoSize
    throw 'Installed training environment does not match requirements-training.lock.txt'
}

& $Python (Join-Path $PSScriptRoot 'fetch_baseline_model_assets.py') --model-id B-M01-BASE
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python (Join-Path $PSScriptRoot 'verify_training_environment.py')
exit $LASTEXITCODE
