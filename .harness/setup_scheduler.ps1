# setup_scheduler.ps1
# Windows 작업 스케줄러에 intel_collector.py 일일 자동 실행 등록
# 실행: powershell -ExecutionPolicy Bypass -File .harness/setup_scheduler.ps1

$taskName   = "KNOT_IntelCollector"
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$vaultDir   = Split-Path -Parent $scriptDir
$pythonExe  = (Get-Command python -ErrorAction SilentlyContinue).Source
$scriptPath = Join-Path $scriptDir "intel_collector.py"

if (-not $pythonExe) {
    Write-Host "[오류] Python을 찾을 수 없습니다. Python을 설치 후 다시 실행하세요." -ForegroundColor Red
    exit 1
}

Write-Host "[스케줄러] 등록 정보:"
Write-Host "  작업 이름 : $taskName"
Write-Host "  Python    : $pythonExe"
Write-Host "  스크립트  : $scriptPath"
Write-Host "  실행 시각 : 매일 오전 08:00"
Write-Host "  작업 폴더 : $vaultDir"

$action  = New-ScheduledTaskAction -Execute $pythonExe -Argument $scriptPath -WorkingDirectory $vaultDir
$trigger = New-ScheduledTaskTrigger -Daily -At "08:00"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -StartWhenAvailable

try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    Write-Host "[완료] 작업 스케줄러 등록 성공!" -ForegroundColor Green
    Write-Host "  확인: 작업 스케줄러 앱 → '$taskName'"
} catch {
    Write-Host "[오류] 등록 실패: $_" -ForegroundColor Red
    Write-Host "  PowerShell을 관리자 권한으로 실행 후 다시 시도하세요."
}
