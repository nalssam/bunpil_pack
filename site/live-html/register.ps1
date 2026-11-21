# Live HTML 추가 기능을 이 PC의 PowerPoint에 등록한다 (현재 사용자만, 관리자 권한 불필요).
# 쓰는 법:  powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/live-html/register.ps1 | iex"
& {
    $ErrorActionPreference = 'Stop'
    $id = '6f2b8c1e-4d7a-4e55-9a3b-2c8f5d1e7a90'
    $site = 'https://nalssam-bunpil.vercel.app/live-html'
    if ($env:LIVEHTML_SITE) { $site = $env:LIVEHTML_SITE.TrimEnd('/') }      # 시험용
    $dir = Join-Path $env:LOCALAPPDATA 'LiveHTML'
    $manifest = Join-Path $dir 'manifest.xml'
    $key = 'HKCU:\Software\Microsoft\Office\16.0\WEF\Developer'

    New-Item -ItemType Directory -Force $dir | Out-Null
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest "$site/manifest.xml" -OutFile $manifest -UseBasicParsing
    if (-not (Select-String -Path $manifest -Pattern $id -Quiet)) { throw "manifest.xml 을 제대로 받지 못했습니다: $manifest" }
    if (-not (Test-Path $key)) { New-Item -Path $key -Force | Out-Null }
    Set-ItemProperty -Path $key -Name $id -Value $manifest

    Write-Host ''
    Write-Host '등록했습니다: Live HTML 추가 기능' -ForegroundColor Green
    Write-Host "  설정 파일: $manifest"
    Write-Host '  PowerPoint를 완전히 종료했다가 다시 열면 살아있는 PPT의 화면이 움직입니다.'
    Write-Host '  지우려면: powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/live-html/unregister.ps1 | iex"'
}
