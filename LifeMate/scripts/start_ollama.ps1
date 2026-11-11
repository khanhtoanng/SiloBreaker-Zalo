param(
    [string]$OllamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
    [string]$LogDirectory = (Join-Path $PSScriptRoot '..\..\local_lifemate_artifacts\ollama_server')
)
$ErrorActionPreference = 'Stop'
try {
    $existing = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 2
    Write-Output "Ollama is already running locally: $($existing.version)"
    return
} catch { }
if (-not (Test-Path -LiteralPath $OllamaPath -PathType Leaf)) {
    throw 'Install Ollama first, or pass -OllamaPath with the installed executable path.'
}
$sourceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$logRoot = [IO.Path]::GetFullPath($LogDirectory)
if ($logRoot -eq $sourceRoot -or $logRoot.StartsWith($sourceRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Keep runtime logs outside the implementation source root.'
}
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$previousOllamaHost = $env:OLLAMA_HOST
$previousOllamaCloud = $env:OLLAMA_NO_CLOUD
try {
    $env:OLLAMA_HOST = '127.0.0.1:11434'
    $env:OLLAMA_NO_CLOUD = '1'
    $serverProcess = Start-Process -FilePath $OllamaPath -ArgumentList 'serve' -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logRoot 'stdout.log') `
        -RedirectStandardError (Join-Path $logRoot 'stderr.log')
} finally {
    $env:OLLAMA_HOST = $previousOllamaHost
    $env:OLLAMA_NO_CLOUD = $previousOllamaCloud
}
for ($attempt = 0; $attempt -lt 15; $attempt++) {
    try {
        $version = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 2
        Write-Output "Started local Ollama $($version.version), process $($serverProcess.Id); cloud disabled."
        return
    } catch {
        if ($serverProcess.HasExited) { throw "Ollama exited; inspect $logRoot" }
        Start-Sleep -Seconds 1
    }
}
throw "Ollama did not become ready; inspect $logRoot"
