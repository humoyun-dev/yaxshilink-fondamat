# Requires: Windows PowerShell run as Administrator

param(
    [string]$ProjectDir = "$PSScriptRoot\..\..",
    [string]$PythonExe = "$PSScriptRoot\..\..\.venv\Scripts\python.exe",
    [string]$TaskName = "YaxshiLink Fandomat",
    [string]$Args = "`"$ProjectDir\main.py`" --no-config-prompt"
)

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $Args -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 9999 -RestartInterval (New-TimeSpan -Seconds 10)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "YaxshiLink Fandomat device runtime" -Force

Write-Host "Scheduled task '$TaskName' registered. It will start at user logon and restart on failure."
