# CyberLab Windows Endpoint Agent Installer (PowerShell)
# Usage: powershell -ExecutionPolicy Bypass -File .\deploy\install-agent.ps1 -ServerUrl http://SOC_IP:8000 [-EnrollmentKey KEY]
param(
    [Parameter(Mandatory=$true)][string]$ServerUrl,
    [string]$EnrollmentKey = "",
    [int]$Interval = 10
)

$InstallDir = "$env:ProgramData\CyberLabAgent"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

$ScriptRoot = Split-Path -Parent $PSScriptRoot
Copy-Item "$ScriptRoot\agent\cyberlab_agent.py" "$InstallDir\cyberlab_agent.py" -Force

python -m pip install --quiet psutil

$ArgsList = "`"$InstallDir\cyberlab_agent.py`" --server $ServerUrl --config `"$InstallDir\config.json`" --interval $Interval"
if ($EnrollmentKey -ne "") {
    $ArgsList = "$ArgsList --enrollment-key $EnrollmentKey"
}

Write-Host "[+] Installed CyberLab Agent to $InstallDir" -ForegroundColor Green
Write-Host "[*] Starting agent daemon connected to $ServerUrl ..." -ForegroundColor Cyan
Start-Process python -ArgumentList $ArgsList -WindowStyle Hidden
Write-Host "[+] CyberLab Agent is now running in the background." -ForegroundColor Green
