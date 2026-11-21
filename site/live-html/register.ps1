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
    # TLS 1.2 를 켠다. 이 줄이 막혀 있는 PC(제한된 언어 모드)에서도 등록은 계속한다.
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }
    # 임시 파일로 받아 확인한 뒤에 제자리로 옮긴다(잘못 받은 내용이 쓰던 설정 파일을 덮어쓰지 않게).
    $tmp = "$manifest.tmp"
    Invoke-WebRequest "$site/manifest.xml" -OutFile $tmp -UseBasicParsing
    if (-not (Select-String -LiteralPath $tmp -Pattern $id -SimpleMatch -Quiet)) {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        throw "manifest.xml 을 제대로 받지 못했습니다: $site/manifest.xml"
    }
    Move-Item -LiteralPath $tmp -Destination $manifest -Force
    if (-not (Test-Path $key)) { New-Item -Path $key -Force | Out-Null }
    Set-ItemProperty -Path $key -Name $id -Value $manifest

    Write-Host ''
    Write-Host '등록했습니다: Live HTML 추가 기능' -ForegroundColor Green
    Write-Host "  설정 파일: $manifest"
    Write-Host '  PowerPoint를 완전히 종료했다가 다시 열면 살아있는 PPT의 화면이 움직입니다.'
    Write-Host '  지우려면: powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/live-html/unregister.ps1 | iex"'
}
