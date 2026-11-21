# Live HTML 추가 기능 등록을 지운다.
& {
    $id = '6f2b8c1e-4d7a-4e55-9a3b-2c8f5d1e7a90'
    $key = 'HKCU:\Software\Microsoft\Office\16.0\WEF\Developer'
    $dir = Join-Path $env:LOCALAPPDATA 'LiveHTML'
    if (Test-Path $key) { Remove-ItemProperty -Path $key -Name $id -ErrorAction SilentlyContinue }
    if (Test-Path $dir) { Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue }
    Write-Host '지웠습니다: Live HTML 추가 기능. PowerPoint를 다시 열면 적용됩니다.' -ForegroundColor Green
}
