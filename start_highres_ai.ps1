[CmdletBinding()]
param(
    [string]$PiHost = '100.80.46.54',
    [switch]$NoDisplay
)

$ErrorActionPreference = 'Stop'

$projectRoot = $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
$pipelineScript = Join-Path $projectRoot 'scripts\runtime\run_robot_pipeline.py'
$resultFile = Join-Path $projectRoot 'runtime\latest_result.json'
$baseUrl = 'http://{0}:5000' -f $PiHost

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Python environment was not found: $pythonExe. Run scripts\\tools\\bootstrap_training_env.ps1 first."
}

if (-not (Test-Path -LiteralPath $pipelineScript)) {
    throw "Inference entry point was not found: $pipelineScript"
}

try {
    $requestParams = @{
        Uri = "$baseUrl/api/status"
        TimeoutSec = 8
        UseBasicParsing = $true
    }
    $statusResponse = Invoke-WebRequest @requestParams
    if ($statusResponse.StatusCode -ne 200) {
        throw "HTTP $($statusResponse.StatusCode)"
    }
}
catch {
    throw "The Raspberry Pi service cannot be reached at $baseUrl. Verify its IP, network connection, and web service. Details: $($_.Exception.Message)"
}

$pipelineArgs = @(
    $pipelineScript
    '--source'
    "$baseUrl/highres_feed"
    '--result-file'
    $resultFile
)

if (-not $NoDisplay) {
    $pipelineArgs += '--display'
}

Write-Host "Starting high-resolution AI recognition from $baseUrl/highres_feed"
Write-Host 'Press Q in the assisted video window to stop.'
& $pythonExe @pipelineArgs
exit $LASTEXITCODE
