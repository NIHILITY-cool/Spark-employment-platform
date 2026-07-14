param(
  [int]$BackendPort = 8082,
  [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$toolsMaven = Join-Path $root ".tools\apache-maven-3.9.9\bin\mvn.cmd"
$mvn = if (Test-Path $toolsMaven) { $toolsMaven } else { "mvn.cmd" }
$nodeCommand = Get-Command node -ErrorAction Stop
$node = $nodeCommand.Source

function Test-Port($port) {
  $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  return $null -ne $connection
}

function Start-LoggedProcess($name, $filePath, $arguments, $workingDirectory) {
  $logDir = Join-Path $root ".tools"
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  $stdout = Join-Path $logDir "$name.out.log"
  $stderr = Join-Path $logDir "$name.err.log"
  Start-Process -FilePath $filePath `
    -ArgumentList $arguments `
    -WorkingDirectory $workingDirectory `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -WindowStyle Hidden | Out-Null
}

if (-not (Test-Port $BackendPort)) {
  Start-LoggedProcess "backend-dev" $mvn "spring-boot:run" $backendDir
  Write-Host "Starting backend on port $BackendPort ..."
} else {
  Write-Host "Backend port $BackendPort is already in use."
}

if (-not (Test-Port $FrontendPort)) {
  $viteBin = Join-Path $frontendDir "node_modules\vite\bin\vite.js"
  Start-LoggedProcess "frontend-dev" $node @($viteBin, "--host", "127.0.0.1", "--port", "$FrontendPort") $frontendDir
  Write-Host "Starting frontend on port $FrontendPort ..."
} else {
  Write-Host "Frontend port $FrontendPort is already in use."
}

Write-Host "Open http://127.0.0.1:$FrontendPort/"
Write-Host "Logs are written to .tools/backend-dev.*.log and .tools/frontend-dev.*.log"
