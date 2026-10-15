# ─────────────────────────────────────────────────────────────
#  nalssam's 분필팩 — 한 줄 설치 (Windows PowerShell 5.1 이상)
#
#    Claude 쓰는 선생님   irm https://nalssam-bunpil.vercel.app/claude.ps1 | iex
#    Codex 쓰는 선생님    irm https://nalssam-bunpil.vercel.app/codex.ps1 | iex
#    직접 고르기          $env:BUNPIL_PROFILE="all"; irm https://nalssam-bunpil.vercel.app/install.ps1 | iex
#    지우기               irm https://nalssam-bunpil.vercel.app/uninstall.ps1 | iex
#    더블클릭             압축을 푼 폴더의 Install-Windows.bat
#
#  하는 일
#   1) 컴퓨터에 있는 Claude Code, Codex(ChatGPT)를 찾는다 (옵션을 주면 없을 때 설치한다)
#   2) 분필팩(플러그인 5종)을 내려받아 %USERPROFILE%\.bunpil 에 두고 설치한다 (Git 없어도 됨)
#   3) 날쌤 추천 스킬·MCP·플러그인 묶음을 함께 설치한다 (catalog/recommended.json)
#   4) 이미 설치되어 있으면 최신으로 바꾼다 (다시 실행 = 업데이트)
#
#  옵션은 환경변수로 준다 (irm | iex 에는 인자를 넘길 수 없다). 값 "1" = 켜기
#   BUNPIL_PROFILE  teacher | creator | dev | all (쉼표로 여러 개, 기본 teacher)
#   BUNPIL_ONLY     claude | codex                 한쪽에만 설치
#   BUNPIL_INSTALL_CLAUDE · BUNPIL_INSTALL_CODEX   없으면 Claude Code / Codex CLI까지 설치
#   BUNPIL_WITH_TOOLS  Node.js·uv·Git이 없으면 함께 설치
#   BUNPIL_RECS="0" 분필팩 5종만 · BUNPIL_HWPX="0" 한글 플러그인 빼기 · BUNPIL_ASK · BUNPIL_UNINSTALL
#   BUNPIL_NALSSAM  날쌤팩(영상·모션·분석 도구)은 macOS·Linux·WSL2 전용 — Windows에서는 WSL2 안내만 한다
#   BUNPIL_SITE · BUNPIL_REPO(owner/repo를 마켓플레이스로) · BUNPIL_HOME(기본 ~\.bunpil) · BUNPIL_KEEP_POLICY
#  관리자 권한이 필요 없다. (Git for Windows 설치만 Windows가 확인 창을 띄울 수 있다)
# ─────────────────────────────────────────────────────────────
$bunpilPreset = $null  # 미리 정한 값 없음(멈춘 실행이 남긴 값도 지운다)
$bunpilScriptDir = $PSScriptRoot
$bunpilPresetArg = $null
if (Test-Path variable:bunpilPreset) { $bunpilPresetArg = $bunpilPreset; Remove-Variable -Name bunpilPreset -ErrorAction SilentlyContinue }
$bunpilOldEnc = $null
try { $bunpilOldEnc = [Console]::OutputEncoding } catch { }

try {
& {
  param([string]$ScriptDir, $Preset)

  $ErrorActionPreference = 'Continue'
  $ProgressPreference = 'SilentlyContinue'
  $oldOutEnc = $null
  try { $oldOutEnc = [Console]::OutputEncoding; [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch { }
  try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }

  $isWin = ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT)
  $sep = [IO.Path]::PathSeparator

  function Opt([string]$name, [string]$key, [string]$default) {
    $v = [Environment]::GetEnvironmentVariable($name)
    if ($v) { return $v }
    if ($Preset -and $Preset.ContainsKey($key) -and $Preset[$key]) { return [string]$Preset[$key] }
    return $default
  }

  $site = (Opt 'BUNPIL_SITE' 'Site' 'https://nalssam-bunpil.vercel.app').TrimEnd('/')
  $repoDefault = 'nalssam/bunpil_pack'
  $market = 'bunpil'
  $plugins = @('bunpil-start', 'bunpil-class', 'bunpil-school', 'bunpil-builder', 'bunpil-connect')
  $skillsCli = 'skills@1.7.2'
  $playwrightMcp = '@playwright/mcp@latest'
  $nodeDist = (Opt 'BUNPIL_NODE_DIST' 'NodeDist' 'https://nodejs.org/dist/latest-v24.x').TrimEnd('/')
  $pptxCommit = 'ae3d919005100472805bf39ddab234bd1cf72577'   # ZZombie04/pptx_maker (날쌤팩 v1.0.1과 같은 커밋)
  $nalssamVersion = 'v1.0.1'
  $bunpilHome = Opt 'BUNPIL_HOME' 'Home' (Join-Path $HOME '.bunpil')
  $packDir = Join-Path $bunpilHome 'bunpil-pack'
  $only = Opt 'BUNPIL_ONLY' 'Only' ''
  $wantClaude = ($only -ne 'codex')
  $wantCodex = ($only -ne 'claude')
  $installClaude = ((Opt 'BUNPIL_INSTALL_CLAUDE' 'InstallClaude' '0') -eq '1')
  $installCodex = ((Opt 'BUNPIL_INSTALL_CODEX' 'InstallCodex' '0') -eq '1')
  $withTools = ((Opt 'BUNPIL_WITH_TOOLS' 'WithTools' '0') -eq '1')
  $ask = ((Opt 'BUNPIL_ASK' 'Ask' '0') -eq '1')
  $recs = ((Opt 'BUNPIL_RECS' 'Recs' '1') -ne '0')
  $skipHwpx = ((Opt 'BUNPIL_HWPX' 'Hwpx' '1') -eq '0')
  $uninstall = ((Opt 'BUNPIL_UNINSTALL' 'Uninstall' '0') -eq '1')
  $profiles = Opt 'BUNPIL_PROFILE' 'Profile' 'teacher'
  $nalssam = ((Opt 'BUNPIL_NALSSAM' 'Nalssam' '0') -eq '1') -or ((',' + $profiles + ',') -match ',nalssam,')
  if ((',' + $profiles + ',') -match ',all,') { $profiles = 'teacher,creator,dev' }
  $profileList = @($profiles.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -and $_ -ne 'nalssam' })
  if ($profileList.Count -eq 0) { $profileList = @('teacher') }

  $st = @{ errors = 0; pathChanged = $false; hasClaude = $false; hasCodex = $false; hasNpx = $false; hasUvx = $false; hasGit = $false; hwpxDone = $false; pptxDone = $false; mdWarm = $false }
  $gitSkip = 'Git이 없어 건너뜀 (Git 설치 후 같은 명령을 다시 실행)'

  function Say([string]$m) { Write-Host $m }
  function Head([string]$m) { Write-Host $m -ForegroundColor Cyan }
  function Ok([string]$m) { Write-Host "  [v] $m" -ForegroundColor Green }
  function Skip([string]$m) { Write-Host "  [-] $m" -ForegroundColor DarkGray }
  function Warn([string]$m) { Write-Host "  [!] $m" -ForegroundColor Yellow }
  function Fail([string]$m) { Write-Host "  [x] $m" -ForegroundColor Red; $st.errors++ }
  function InProfile([string]$p) { return ($profileList -contains $p) }

  # 명령 찾기: Windows에서는 .exe/.cmd를 먼저 찾는다 (npm이 만든 .ps1은 실행 정책에 막힐 수 있다)
  function Exe([string]$name) {
    $cands = @($name)
    if ($isWin) { $cands = @("$name.exe", "$name.cmd", "$name.bat", $name) }
    foreach ($n in $cands) {
      $c = Get-Command $n -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
      if ($c) { return $c.Path }
    }
    return $null
  }
  function Has([string]$name) { return [bool](Exe $name) }
  function Run([string]$name, [string[]]$argv) {
    $exe = Exe $name
    if (-not $exe) { return $false }
    & $exe @argv *> $null
    return ($LASTEXITCODE -eq 0)
  }
  function Capture([string]$name, [string[]]$argv) {
    $exe = Exe $name
    if (-not $exe) { return '' }
    $o = & $exe @argv 2>$null | Out-String
    return [string]$o
  }
  function FirstLine([string]$name, [string[]]$argv) {
    $t = (Capture $name $argv).Trim()
    if (-not $t) { return '' }
    return ($t -split "`r?`n")[0]
  }

  # PATH: 지금 창에 바로 반영하고, 필요하면 사용자 PATH에도 남긴다(새 창에서도 찾도록)
  function RefreshPath {
    if (-not $isWin) { return }
    $list = New-Object System.Collections.Generic.List[string]
    foreach ($src in @($env:PATH, [Environment]::GetEnvironmentVariable('Path', 'User'), [Environment]::GetEnvironmentVariable('Path', 'Machine'))) {
      if (-not $src) { continue }
      foreach ($p in $src.Split(';')) { if ($p -and -not $list.Contains($p)) { $list.Add($p) } }
    }
    $env:PATH = ($list -join ';')
  }
  function AddPath([string]$dir, [bool]$persist) {
    if (-not $dir) { return }
    if (@($env:PATH.Split($sep)) -notcontains $dir) { $env:PATH = $dir + $sep + $env:PATH }
    if ($persist -and $isWin) { AddUserPath $dir }
  }
  # 사용자 PATH에 영구로 더한다. 레지스트리 원문을 읽고 REG_EXPAND_SZ로 써서 %USERPROFILE% 같은 항목이 굳지 않게 한다
  function AddUserPath([string]$dir) {
    $key = $null
    try {
      $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', $true)
      if (-not $key) { return }
      $raw = [string]$key.GetValue('Path', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
      $parts = @($raw.Split(';') | Where-Object { $_ })
      foreach ($q in $parts) {
        if ([Environment]::ExpandEnvironmentVariables($q).TrimEnd('\') -ieq $dir.TrimEnd('\')) { return }
      }
      $key.SetValue('Path', (@($parts) + $dir) -join ';', [Microsoft.Win32.RegistryValueKind]::ExpandString)
      # 열려 있는 다른 프로그램에 환경 변수가 바뀌었다고 알린다(WM_SETTINGCHANGE)
      [Environment]::SetEnvironmentVariable('BUNPIL_PATH_REFRESH', '1', 'User')
      [Environment]::SetEnvironmentVariable('BUNPIL_PATH_REFRESH', $null, 'User')
      $st.pathChanged = $true
    } catch {
      Warn "사용자 PATH에 $dir 를 더하지 못했습니다 — 새 창에서 명령을 찾지 못하면 이 폴더를 PATH에 직접 더하세요"
    } finally {
      if ($key) { $key.Close() }
    }
  }
  function Download([string]$url, [string]$out) {
    try {
      Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing -ErrorAction Stop
      return ((Test-Path $out) -and ((Get-Item $out).Length -gt 0))
    } catch { return $false }
  }
  function Unpack([string]$zip, [string]$dest) {
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    $tar = $null
    if ($isWin) { $tar = Exe 'tar' }
    if ($tar) {
      & $tar -xf $zip -C $dest *> $null
      if ($LASTEXITCODE -eq 0) { return $true }
    }
    try { Expand-Archive -Path $zip -DestinationPath $dest -Force -ErrorAction Stop; return $true } catch { return $false }
  }
  # 공식 설치 프로그램은 새 PowerShell에서 실행한다(그 안의 exit가 이 창을 닫지 않도록)
  function PsExe {
    if ($PSVersionTable.PSEdition -eq 'Core') {
      $n = 'pwsh'
      if ($isWin) { $n = 'pwsh.exe' }
      $c = Join-Path $PSHOME $n
      if (Test-Path $c) { return $c }
    }
    if ($isWin -and $env:SystemRoot) {
      if ([Environment]::Is64BitOperatingSystem -and -not [Environment]::Is64BitProcess) {
        $c = Join-Path $env:SystemRoot 'Sysnative\WindowsPowerShell\v1.0\powershell.exe'
        if (Test-Path $c) { return $c }
      }
      $c = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
      if (Test-Path $c) { return $c }
      return 'powershell.exe'
    }
    return 'pwsh'
  }
  function RunRemotePs([string]$url, [string]$pre = '') {
    $psExe = PsExe
    $cmd = "$pre[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12; `$ProgressPreference = 'SilentlyContinue'; Invoke-RestMethod -UseBasicParsing '$url' | Invoke-Expression"
    & $psExe -NoProfile -ExecutionPolicy Bypass -Command $cmd *> $null
    return ($LASTEXITCODE -eq 0)
  }
  function WingetInstall([string]$id) {
    if (-not (Has 'winget')) { return $false }
    return (Run 'winget' @('install', '--id', $id, '-e', '--source', 'winget', '--silent', '--accept-package-agreements', '--accept-source-agreements'))
  }
  # Node.js를 관리자 권한 없이 ~\.bunpil\node 에 설치 (공식 배포본, SHA-256 확인)
  function InstallNodeLocal {
    $arch = 'x64'
    if ($isWin) {
      if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') { $arch = 'arm64' }
      $pattern = '  node-v[0-9.]+-win-' + $arch + '\.zip$'
    } else {
      $os = 'linux'
      if ((Capture 'uname' @('-s')).Trim() -eq 'Darwin') { $os = 'darwin' }
      $m = (Capture 'uname' @('-m')).Trim()
      if ($m -eq 'arm64' -or $m -eq 'aarch64') { $arch = 'arm64' }
      $pattern = '  node-v[0-9.]+-' + $os + '-' + $arch + '\.tar\.gz$'
    }
    $tmp = Join-Path $bunpilHome (".node." + $PID)
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $sums = Join-Path $tmp 'SHASUMS256.txt'
    $ok = $false
    if (Download "$nodeDist/SHASUMS256.txt" $sums) {
      $line = Get-Content $sums | Where-Object { $_ -match $pattern } | Select-Object -First 1
      if ($line) {
        $parts = $line -split '\s+'
        $sum = $parts[0]; $file = $parts[1]
        $arc = Join-Path $tmp $file
        if ((Download "$nodeDist/$file" $arc) -and ((Get-FileHash -Path $arc -Algorithm SHA256).Hash.ToLower() -eq $sum.ToLower())) {
          $base = $file -replace '\.zip$', '' -replace '\.tar\.gz$', ''
          $unpacked = $false
          if ($isWin) { $unpacked = Unpack $arc $tmp } else { & tar -xzf $arc -C $tmp *> $null; $unpacked = ($LASTEXITCODE -eq 0) }
          if ($unpacked -and (Test-Path (Join-Path $tmp $base))) {
            $dest = Join-Path $bunpilHome 'node'
            Remove-Item $dest -Recurse -Force -ErrorAction SilentlyContinue
            Move-Item (Join-Path $tmp $base) $dest
            if ($isWin) { AddPath $dest $true } else { AddPath (Join-Path $dest 'bin') $false }
            $ok = (Has 'node')
          }
        }
      }
    }
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    return $ok
  }
  # npm이 만든 codex.ps1 이 '스크립트 실행 안 됨'으로 막히지 않도록 현재 사용자 실행 정책을 RemoteSigned로
  function EnsureScriptPolicy {
    if (-not $isWin) { return }
    if ($env:BUNPIL_KEEP_POLICY -eq '1') { return }
    try {
      $cu = [string](Get-ExecutionPolicy -Scope CurrentUser)
      $lm = [string](Get-ExecutionPolicy -Scope LocalMachine)
      $blocked = @('Restricted', 'AllSigned', 'Undefined')
      if (($cu -eq 'Restricted') -or ($cu -eq 'AllSigned') -or (($cu -eq 'Undefined') -and ($blocked -contains $lm))) {
        Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force -ErrorAction Stop
        try { New-Item -ItemType Directory -Force -Path $bunpilHome | Out-Null; Set-Content -Path (Join-Path $bunpilHome 'policy-changed') -Value 'RemoteSigned' -Encoding ASCII } catch { }
        Ok "PowerShell에서 codex 명령이 실행되도록 현재 사용자 실행 정책을 RemoteSigned로 바꿨습니다 (되돌리기: Set-ExecutionPolicy -Scope CurrentUser Undefined)"
      }
    } catch { Warn "실행 정책을 바꾸지 못했습니다 — PowerShell에서 codex가 막히면 codex.cmd 로 실행하세요" }
  }

  # 정확한 이름으로 찾기
  function CHasMarket([string]$m) { return ((Capture 'claude' @('plugin', 'marketplace', 'list')) -match ('(?m)^\s*>\s+' + [regex]::Escape($m) + '\s*$')) }
  function CHasPlugin([string]$p) { return ((Capture 'claude' @('plugin', 'list')) -match ('(?m)^\s*>\s+' + [regex]::Escape($p) + '\s*$')) }
  function CMarketSrc([string]$m) {
    $lines = (Capture 'claude' @('plugin', 'marketplace', 'list')) -split "`r?`n"
    for ($i = 0; $i -lt $lines.Count; $i++) {
      if ($lines[$i] -match ('^\s*>\s+' + [regex]::Escape($m) + '\s*$')) { if ($i + 1 -lt $lines.Count) { return $lines[$i + 1] } }
    }
    return ''
  }
  function XMarketLine([string]$m) {
    foreach ($l in ((Capture 'codex' @('plugin', 'marketplace', 'list')) -split "`r?`n")) {
      if ($l -match ('^' + [regex]::Escape($m) + '\s')) { return $l }
    }
    return ''
  }
  function XHasMarket([string]$m) { return [bool](XMarketLine $m) }
  function SameSource([string]$line, [string]$source) {
    if (-not $line -or -not $source) { return $false }
    $a = $line.Replace('\', '/').ToLower(); $b = $source.Replace('\', '/').ToLower()
    return $a.Contains($b)
  }

  # 이 스크립트가 압축을 푼 분필팩 폴더 안에서 실행됐는지 확인(더블클릭 설치)
  $localSrc = Opt 'BUNPIL_LOCAL' 'Local' ''
  if (-not $localSrc -and $ScriptDir) {
    if ((Test-Path (Join-Path $ScriptDir '.claude-plugin/marketplace.json')) -and (Test-Path (Join-Path $ScriptDir 'plugins'))) { $localSrc = $ScriptDir }
  }

  Say ''
  Write-Host "nalssam's 분필팩" -ForegroundColor Cyan -NoNewline
  Say ' — 선생님의 AI 조수를 한 줄로'
  Say '누구도 소외되지 않는 기술, 혼자 닳지 않는 교사'
  Say ''

  # ── 지우기 ───────────────────────────────────────────────
  if ($uninstall) {
    Head '분필팩을 지웁니다'
    if ($wantClaude -and (Has 'claude')) {
      foreach ($p in $plugins) {
        if (CHasPlugin "$p@$market") { if (Run 'claude' @('plugin', 'uninstall', "$p@$market")) { Ok "Claude Code: $p 제거" } else { Fail "Claude Code: $p 제거 실패" } }
      }
      if (CHasMarket $market) { if (Run 'claude' @('plugin', 'marketplace', 'remove', $market)) { Ok 'Claude Code: 분필팩 목록 제거' } }
    }
    if ($wantCodex -and (Has 'codex')) {
      foreach ($p in $plugins) { if (Run 'codex' @('plugin', 'remove', "$p@$market")) { Ok "Codex: $p 제거" } }
      if (XHasMarket $market) { if (Run 'codex' @('plugin', 'marketplace', 'remove', $market)) { Ok 'Codex: 분필팩 목록 제거' } }
    }
    if ((Split-Path $packDir -Leaf) -eq 'bunpil-pack' -and (Test-Path $packDir)) {
      Remove-Item $packDir -Recurse -Force -ErrorAction SilentlyContinue
      if (-not (Test-Path $packDir)) { Ok "내려받은 분필팩 폴더 삭제 ($packDir)" }
    }
    Say ''
    Say '그대로 둔 것 (다른 곳에서도 쓰는 도구라서):'
    Say '  - 추천 묶음(한글 도구·MCP 등)  Claude Code: claude plugin uninstall <이름>@<마켓> · claude mcp remove <이름>'
    Say '                                 Codex: codex plugin remove <이름>@<마켓> · codex mcp remove <이름>'
    if (Test-Path (Join-Path $bunpilHome 'node')) { Say "  - 분필팩이 설치한 Node.js ($(Join-Path $bunpilHome 'node'))" }
    if ($isWin) { Say '  - 사용자 PATH에 더한 폴더(.bunpil\node, .local\bin 등) — 지우면 설치한 도구를 찾지 못할 수 있습니다' }
    if (Test-Path (Join-Path $bunpilHome 'policy-changed')) {
      Say '  - PowerShell 실행 정책(현재 사용자 RemoteSigned, codex 명령용)  되돌리기: Set-ExecutionPolicy -Scope CurrentUser Undefined'
    }
    Say '  - 작업 폴더의 CLAUDE.md·AGENTS.md·my-harness 폴더(선생님 파일)'
    if ($oldOutEnc) { try { [Console]::OutputEncoding = $oldOutEnc } catch { } }
    return
  }

  # ── 아무것도 없을 때 물어보기(더블클릭 설치) ─────────────
  $hasClaudeNow = $wantClaude -and (Has 'claude')
  $hasCodexNow = $wantCodex -and (Has 'codex')
  if (-not $hasClaudeNow -and -not $hasCodexNow -and $ask -and -not $installClaude -and -not $installCodex) {
    Say '이 컴퓨터에 Claude Code와 Codex가 모두 없습니다. 무엇을 설치할까요?'
    Say '  1) Claude Code  — Claude Pro 이상 유료 요금제'
    Say '  2) Codex        — ChatGPT 계정(무료 포함), Node.js가 함께 설치됩니다'
    Say '  3) 둘 다'
    $ans = ''
    try { $ans = Read-Host '번호를 누르고 Enter (그만두려면 그냥 Enter)' } catch { $ans = '' }
    switch (([string]$ans).Trim()) {
      '1' { $installClaude = $true; $wantCodex = $false; $withTools = $true }
      '2' { $installCodex = $true; $wantClaude = $false; $withTools = $true }
      '3' { $installClaude = $true; $installCodex = $true; $withTools = $true }
      default { Say '그만둡니다.'; if ($oldOutEnc) { try { [Console]::OutputEncoding = $oldOutEnc } catch { } }; return }
    }
    Say ''
  }

  # ── 준비물 설치 ──────────────────────────────────────────
  if ($isWin -and $withTools -and -not (Has 'git')) {
    Head 'Git for Windows 설치 (GitHub에서 추천 도구를 받을 때 필요)'
    Say '  Windows가 "이 앱이 디바이스를 변경할 수 있도록 허용하시겠어요?"라고 물으면 [예]를 누르세요.'
    if (WingetInstall 'Git.Git') { RefreshPath }
    if (Has 'git') { Ok 'Git for Windows 설치' }
    else { Warn 'Git을 설치하지 못했습니다 — Git이 필요한 일부 추천 도구만 건너뜁니다 (https://git-scm.com/download/win 에서 설치하고 같은 명령을 다시 실행하면 채워집니다)' }
    Say ''
  }
  if ($wantClaude -and $installClaude -and -not (Has 'claude')) {
    Head 'Claude Code 설치 (공식 설치 프로그램 · 1~2분)'
    if (RunRemotePs 'https://claude.ai/install.ps1') {
      RefreshPath
      AddPath (Join-Path $HOME '.local\bin') $true
      if (Has 'claude') { Ok ("Claude Code 설치 완료 (" + (FirstLine 'claude' @('--version')) + ")") }
      else { Fail 'Claude Code가 설치됐지만 찾지 못했습니다 — PowerShell 창을 새로 열고 다시 실행하세요' }
    } else { Fail 'Claude Code 설치 실패 — https://claude.com/download 에서 직접 설치하세요' }
    Say ''
  }
  if ($withTools) {
    Head '준비 도구 (Node.js·uv — 문서·자동화 도구에 필요)'
    if ((Has 'node') -and (Has 'npx')) { Ok ("Node.js " + (FirstLine 'node' @('--version')) + " 있음") }
    elseif (InstallNodeLocal) { Ok ("Node.js " + (FirstLine 'node' @('--version')) + " 설치 ($(Join-Path $bunpilHome 'node') · 관리자 권한 없이)") }
    else {
      $nodeOk = $false
      if ($isWin -and (WingetInstall 'OpenJS.NodeJS.LTS')) { RefreshPath; $nodeOk = (Has 'node') }
      if ($nodeOk) { Ok 'Node.js 설치 (winget)' }
      else { Warn 'Node.js를 설치하지 못했습니다 — https://nodejs.org 에서 LTS를 설치한 뒤 다시 실행하세요' }
    }
    if ((Has 'uv') -and (Has 'uvx')) { Ok 'uv 있음' }
    elseif ($isWin -and (RunRemotePs 'https://astral.sh/uv/install.ps1')) {
      RefreshPath
      AddPath (Join-Path $HOME '.local\bin') $true
      if (Has 'uv') { Ok 'uv 설치 (공식 설치 프로그램)' } else { Warn 'uv를 설치했지만 찾지 못했습니다' }
    }
    elseif (-not $isWin -and (Run 'sh' @('-c', 'curl -LsSf https://astral.sh/uv/install.sh | sh'))) {
      AddPath (Join-Path $HOME '.local/bin') $false
      if (Has 'uv') { Ok 'uv 설치 (공식 설치 프로그램)' } else { Warn 'uv를 설치했지만 찾지 못했습니다' }
    }
    else { Warn 'uv를 설치하지 못했습니다 — https://docs.astral.sh/uv 를 참고하세요' }
    Say ''
  }
  if ($wantCodex -and $installCodex -and -not (Has 'codex')) {
    Head 'Codex CLI 설치 (OpenAI 공식 설치 프로그램 · 1~2분)'
    $viaNpm = $false
    if ($isWin) {
      if (RunRemotePs 'https://chatgpt.com/codex/install.ps1' '$env:CODEX_NON_INTERACTIVE = ''1''; ') {
        RefreshPath
        if ($env:LOCALAPPDATA) { AddPath (Join-Path $env:LOCALAPPDATA 'Programs\OpenAI\Codex\bin') $true }
      }
    } else {
      $env:CODEX_NON_INTERACTIVE = '1'
      Run 'sh' @('-c', 'curl -fsSL https://chatgpt.com/codex/install.sh | sh') | Out-Null
      Remove-Item Env:CODEX_NON_INTERACTIVE -ErrorAction SilentlyContinue
      AddPath (Join-Path $HOME '.local/bin') $false
    }
    if (-not (Has 'codex') -and (Has 'npm')) {
      $viaNpm = $true
      if (-not (Run 'npm' @('install', '-g', '@openai/codex'))) { Run 'npm' @('install', '-g', '--prefix', (Join-Path $HOME '.local'), '@openai/codex') | Out-Null }
      $prefix = (Capture 'npm' @('prefix', '-g')).Trim()
      if ($prefix) { if ($isWin) { AddPath $prefix $true } else { AddPath (Join-Path $prefix 'bin') $false } }
    }
    if (Has 'codex') {
      Ok ("Codex CLI 설치 완료 (" + (FirstLine 'codex' @('--version')) + ")")
      if ($viaNpm) { EnsureScriptPolicy }
    } else { Fail 'Codex CLI 설치 실패 — https://developers.openai.com/codex 의 안내로 직접 설치한 뒤 다시 실행하세요' }
    Say ''
  }

  $st.hasClaude = $wantClaude -and (Has 'claude')
  $st.hasCodex = $wantCodex -and (Has 'codex')
  if (-not $st.hasClaude -and -not $st.hasCodex) {
    Fail 'Claude Code도 Codex도 찾지 못했습니다.'
    Say ''
    Say "  - Claude 쓰는 선생님:  irm $site/claude.ps1 | iex"
    Say "  - Codex 쓰는 선생님:   irm $site/codex.ps1 | iex"
    Say "  - 터미널 없이 Claude 앱에서: $site 의 'Claude 앱' 안내를 따르세요"
    if ($oldOutEnc) { try { [Console]::OutputEncoding = $oldOutEnc } catch { } }
    return
  }
  $st.hasNpx = Has 'npx'
  $st.hasUvx = Has 'uvx'
  $st.hasGit = Has 'git'

  # ── 분필팩 내려받기 ──────────────────────────────────────
  $source = ''; $sourceIsRepo = $false; $sourceFallback = $false
  # 폴더 옮기기: 백신·색인 프로그램이 잠깐 붙잡고 있을 수 있어 몇 번 다시 시도한다
  function MoveRetry([string]$from, [string]$to) {
    for ($i = 0; $i -lt 10; $i++) {
      try { Move-Item -LiteralPath $from -Destination $to -ErrorAction Stop; return $true } catch { Start-Sleep -Milliseconds 300 }
    }
    return $false
  }
  function PackVersion {
    $vf0 = Join-Path $packDir 'VERSION'
    if (Test-Path $vf0) { return (Get-Content $vf0 -TotalCount 1).Trim() }
    return '?'
  }
  function HasPack { return (Test-Path (Join-Path $packDir '.claude-plugin/marketplace.json')) }
  function PreparePack {
    $r = Opt 'BUNPIL_REPO' 'Repo' ''
    if ($r) { Ok "분필팩 저장소: $r"; return @{ ok = $true; source = $r; repo = $true; fallback = $false } }
    New-Item -ItemType Directory -Force -Path $bunpilHome | Out-Null
    # 지난 실행이 남긴 임시 폴더 정리. 분필팩 폴더가 없고 옛 사본만 남아 있으면 먼저 되돌린다
    foreach ($d in @(Get-ChildItem -LiteralPath $bunpilHome -Directory -Force -Filter '.tmp.*' -ErrorAction SilentlyContinue)) {
      $left = Join-Path $d.FullName 'old'
      if (-not (Test-Path $packDir) -and (Test-Path (Join-Path $left '.claude-plugin/marketplace.json'))) { [void](MoveRetry $left $packDir) }
      if ((Test-Path $packDir) -or -not (Test-Path $left)) { Remove-Item -LiteralPath $d.FullName -Recurse -Force -ErrorAction SilentlyContinue }
    }
    $tmp = Join-Path $bunpilHome (".tmp." + $PID)
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path (Join-Path $tmp 'new') | Out-Null
    $newPack = Join-Path (Join-Path $tmp 'new') 'bunpil-pack'
    if ($localSrc) {
      $a = (Resolve-Path $localSrc).Path.TrimEnd('\', '/')
      if ((Test-Path $packDir) -and ($a -eq (Resolve-Path $packDir).Path.TrimEnd('\', '/'))) {
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
        Ok "분필팩 폴더 사용 ($packDir)"; return @{ ok = $true; source = $packDir; repo = $false; fallback = $false }
      }
      New-Item -ItemType Directory -Force -Path $newPack | Out-Null
      foreach ($x in @('.claude-plugin', '.agents', 'plugins', 'catalog', 'VERSION', 'install.sh', 'install.ps1', 'README.md', 'LICENSE', 'NOTICE')) {
        $s = Join-Path $localSrc $x
        if (Test-Path $s) { Copy-Item $s $newPack -Recurse -Force }
      }
    } else {
      $zip = Join-Path $tmp 'bunpil-pack.zip'
      # 받기·압축 풀기·내용 확인 중 하나라도 실패하면(학교 방화벽이 안내 페이지를 대신 주는 경우 포함) 같은 길로 처리한다
      $got = (Download "$site/bunpil-pack.zip" $zip) -and (Unpack $zip (Join-Path $tmp 'new')) -and (Test-Path (Join-Path $newPack '.claude-plugin/marketplace.json'))
      if (-not $got) {
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
        if (HasPack) {
          Warn ("새 분필팩을 받지 못해(인터넷·학교 방화벽 확인) 이미 있는 분필팩(v" + (PackVersion) + ")을 그대로 씁니다")
          return @{ ok = $true; source = $packDir; repo = $false; fallback = $false }
        }
        if ($st.hasGit) { Warn "분필팩을 받지 못해 GitHub 저장소($repoDefault)를 대신 씁니다"; return @{ ok = $true; source = $repoDefault; repo = $true; fallback = $true } }
        Fail "분필팩을 받지 못했습니다 ($site/bunpil-pack.zip) — 인터넷 연결이나 학교 방화벽을 확인하세요. 사이트에서 zip을 직접 받아 압축을 풀고 Install-Windows.bat 으로 설치할 수도 있습니다"
        return @{ ok = $false }
      }
    }
    if (-not (Test-Path (Join-Path $newPack '.claude-plugin/marketplace.json'))) {
      Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
      Fail '받은 분필팩이 올바르지 않습니다'; return @{ ok = $false }
    }
    # 이전 폴더를 먼저 옆으로 옮긴 뒤 새 폴더를 놓는다. 못 바꾸면 지금 버전을 그대로 쓴다
    $old = Join-Path $tmp 'old'
    $busy = '다른 프로그램이 폴더를 쓰는 중일 수 있습니다. Claude Code·Codex 창과 그 폴더를 연 탐색기를 닫고 같은 명령을 다시 실행하면 바뀝니다'
    if ((Test-Path $packDir) -and -not (MoveRetry $packDir $old)) {
      Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
      Warn ("분필팩 폴더를 새 버전으로 바꾸지 못해 지금 버전(v" + (PackVersion) + ")을 그대로 씁니다 — " + $busy)
      return @{ ok = $true; source = $packDir; repo = $false; fallback = $false }
    }
    if (-not (MoveRetry $newPack $packDir)) {
      if ((Test-Path $old) -and -not (Test-Path $packDir)) { [void](MoveRetry $old $packDir) }
      if (HasPack) {
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
        Warn ("새 분필팩을 제자리에 두지 못해 지금 버전(v" + (PackVersion) + ")을 그대로 씁니다 — " + $busy)
        return @{ ok = $true; source = $packDir; repo = $false; fallback = $false }
      }
      Fail "분필팩 폴더를 준비하지 못했습니다 — 같은 명령을 다시 실행해 보세요 (임시 폴더: $tmp)"
      return @{ ok = $false }
    }
    if (Test-Path $packDir) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
    if ($isWin) {
      try { Get-ChildItem $packDir -Recurse -File | Unblock-File -ErrorAction SilentlyContinue } catch { }
      # Windows용 훅으로 바꿔 끼우기 (Git Bash 없이도 PowerShell로 개인정보 가드 실행)
      $hw = Join-Path $packDir 'plugins\claude\bunpil-start\hooks\hooks.windows.json'
      if (Test-Path $hw) { Copy-Item $hw (Join-Path $packDir 'plugins\claude\bunpil-start\hooks\hooks.json') -Force }
    }
    $ver = '?'
    $vf = Join-Path $packDir 'VERSION'
    if (Test-Path $vf) { $ver = (Get-Content $vf -TotalCount 1).Trim() }
    Ok "분필팩 v$ver 준비 ($packDir)"
    return @{ ok = $true; source = $packDir; repo = $false; fallback = $false }
  }

  # ── 공통 도우미 ──────────────────────────────────────────
  function CPlugin([string]$repoName, [string]$id, [string]$label) {
    if (CHasPlugin $id) {
      if (Run 'claude' @('plugin', 'update', $id)) { Ok "$label — 최신 확인" } else { Warn "$label — 업데이트 확인 실패(지금 버전 유지)" }
      return
    }
    if (-not $st.hasGit) { Skip "$label — $gitSkip"; return }
    $m = $id.Split('@')[1]
    if (CHasMarket $m) { Run 'claude' @('plugin', 'marketplace', 'update', $m) | Out-Null } else { Run 'claude' @('plugin', 'marketplace', 'add', $repoName) | Out-Null }
    if (Run 'claude' @('plugin', 'install', $id, '-y')) { Ok $label } else { Fail "$label — 설치 실패 (claude plugin install $id)" }
  }
  function CMarket([string]$repoName, [string]$m, [string]$label) {
    if (-not $st.hasGit) { Skip "$label — $gitSkip"; return }
    if (CHasMarket $m) {
      if (Run 'claude' @('plugin', 'marketplace', 'update', $m)) { Ok "$label — 목록 갱신" } else { Warn "$label — 목록 갱신 실패(지금 목록 유지)" }
    }
    elseif (Run 'claude' @('plugin', 'marketplace', 'add', $repoName)) { Ok "$label — 목록 등록(/plugin에서 골라 설치)" }
    else { Fail "$label — 목록 등록 실패" }
  }
  function XPlugin([string]$repoName, [string]$id, [string]$label) {
    if (-not $st.hasGit) { Skip "$label — $gitSkip"; return }
    $m = $id.Split('@')[1]
    if (XHasMarket $m) { Run 'codex' @('plugin', 'marketplace', 'upgrade', $m) | Out-Null } else { Run 'codex' @('plugin', 'marketplace', 'add', $repoName) | Out-Null }
    if (Run 'codex' @('plugin', 'add', $id)) { Ok $label } else { Fail "$label — 설치 실패 (codex plugin add $id)" }
  }
  function XMarket([string]$repoName, [string]$m, [string]$label) {
    if (-not $st.hasGit) { Skip "$label — $gitSkip"; return }
    if (XHasMarket $m) {
      if (Run 'codex' @('plugin', 'marketplace', 'upgrade', $m)) { Ok "$label — 목록 갱신" } else { Warn "$label — 목록 갱신 실패(지금 목록 유지)" }
    }
    elseif (Run 'codex' @('plugin', 'marketplace', 'add', $repoName)) { Ok "$label — 목록 등록(/plugins에서 골라 설치)" }
    else { Fail "$label — 목록 등록 실패" }
  }
  function SkillsAdd([string]$repoName, [string]$agent, [string]$label) {
    if (-not $st.hasNpx) { Skip "$label — Node.js가 없어 건너뜀"; return }
    if (-not $st.hasGit) { Skip "$label — $gitSkip"; return }
    $env:DISABLE_TELEMETRY = '1'; $env:DO_NOT_TRACK = '1'
    if (Run 'npx' @('-y', $skillsCli, 'add', $repoName, '-g', '-a', $agent, '-y', '--copy')) { Ok $label }
    else { Fail "$label — 스킬 설치 실패 (npx $skillsCli add $repoName -g -a $agent)" }
  }
  function McpAdd([string]$hostName, [string]$name, [string]$label, [string[]]$cmd) {
    if (Run $hostName @('mcp', 'get', $name)) { Ok "$label — 이미 연결됨"; return }
    # Windows에서 npx는 .cmd라서 cmd /c 로 감싼다
    if ($isWin -and $cmd[0] -eq 'npx') { $cmd = @('cmd', '/c') + $cmd }
    if ($hostName -eq 'claude') { $argv = @('mcp', 'add', '-s', 'user', $name, '--') + $cmd } else { $argv = @('mcp', 'add', $name, '--') + $cmd }
    if (Run $hostName $argv) { Ok $label } else { Fail "$label — MCP 등록 실패" }
  }
  # 첫 실행 때 내려받는 시간(30초 안팎) 때문에 MCP 연결이 시간 초과되지 않도록 미리 받아 둔다
  function WarmMarkitdown {
    if ($st.mdWarm) { return }
    $st.mdWarm = $true
    if ($st.hasUvx) { Run 'uvx' @('markitdown-mcp', '--help') | Out-Null }
  }
  function HwpxNew {
    if ($st.hwpxDone) { return }
    $st.hwpxDone = $true
    $targets = @()
    if ($st.hasClaude) { $targets += 'claude-code' }
    if ($st.hasCodex) { $targets += 'codex' }
    $zsrc = 'https://github.com/ZZombie04/hwpx_new/archive/refs/heads/main.zip'
    $gsrc = 'git+https://github.com/ZZombie04/hwpx_new.git'
    $done = $false
    if (Has 'uv') {
      if ($st.hasGit) { $done = Run 'uv' @('tool', 'install', '--force', "hwpx-new @ $gsrc") }
      if (-not $done) { $done = Run 'uv' @('tool', 'install', '--force', "hwpx-new @ $zsrc") }
    } elseif (Has 'pipx') {
      if ($st.hasGit) { $done = Run 'pipx' @('install', '--force', $gsrc) }
      if (-not $done) { $done = Run 'pipx' @('install', '--force', $zsrc) }
    } else { Skip '한글 양식 보고서(hwpx_new) — uv가 없어 건너뜀'; return }
    if ($isWin) { AddPath (Join-Path $HOME '.local\bin') $true } else { AddPath (Join-Path $HOME '.local/bin') $false }
    if ($done -and (Has 'hwpx-new') -and (Run 'hwpx-new' @('setup', '-y', '--only', ($targets -join ',')))) { Ok '한글 양식 보고서(hwpx_new) — 설치·MCP 연결' }
    else { Fail "한글 양식 보고서(hwpx_new) — 설치 실패 (pip install $zsrc)" }
  }

  # 한국어 발표 자료 엔진: 고정 커밋으로 설치하고 Claude Code·Codex에 MCP·스킬 연결
  function PptxMaker {
    if ($st.pptxDone) { return }
    $st.pptxDone = $true
    $label = '발표 자료(PPTX) 엔진 · ZZombie04/pptx_maker'
    $targets = @()
    if ($st.hasClaude) { $targets += 'claude-code' }
    if ($st.hasCodex) { $targets += 'codex'; $targets += 'skill' }
    if (-not (Has 'uv')) { Skip "$label — uv가 없어 건너뜀"; return }
    $gsrc = "git+https://github.com/ZZombie04/pptx_maker@$pptxCommit"
    $zsrc = "https://github.com/ZZombie04/pptx_maker/archive/$pptxCommit.zip"
    $done = $false
    if ($st.hasGit) { $done = Run 'uv' @('tool', 'install', '--force', "pptx-maker[images] @ $gsrc") }
    if (-not $done) { $done = Run 'uv' @('tool', 'install', '--force', "pptx-maker[images] @ $zsrc") }
    if ($isWin) { AddPath (Join-Path $HOME '.local\bin') $true } else { AddPath (Join-Path $HOME '.local/bin') $false }
    if ($done -and (Has 'pptx-maker') -and (Run 'pptx-maker' @('setup', '--yes', '--only', ($targets -join ',')))) { Ok "$label — 설치·MCP·스킬 연결" }
    else { Fail "$label — 설치 실패 (uv tool install `"pptx-maker @ $zsrc`")" }
  }
  # 날쌤팩은 macOS·Linux·WSL2 전용 설치기라 Windows에서는 안내만 한다
  function NalssamGuide {
    Head "[날쌤팩 $nalssamVersion]"
    if ($isWin) {
      Skip '날쌤팩 — Windows에서는 WSL2 Ubuntu 안에서 설치합니다(이 PowerShell의 Claude Code·Codex와는 따로 설치됨)'
      Say '    1) PowerShell(관리자)에서  wsl --install  → 다시 시작 → Ubuntu 열기'
      Say "    2) Ubuntu 터미널에서  bash -c `"`$(curl -fsSL https://raw.githubusercontent.com/nalssam/nalssam-pack/$nalssamVersion/install.sh)`" -- --claude"
    } else {
      Skip "날쌤팩 — macOS·Linux에서는 터미널 한 줄 설치에 --nalssam 을 붙이세요:  curl -fsSL $site/install.sh | sh -s -- --nalssam"
    }
  }

  # ── 분필팩 설치 ──────────────────────────────────────────
  function BunpilClaude([string]$src, [bool]$isRepo, [bool]$isFallback) {
    if (CHasMarket $market) {
      if (SameSource (CMarketSrc $market) $src) {
        if (Run 'claude' @('plugin', 'marketplace', 'update', $market)) { Ok '분필팩 목록 최신으로 갱신' } else { Warn '분필팩 목록 갱신 실패(지금 버전 유지)' }
      } elseif ($isFallback) {
        # 내려받기에 실패해 저장소를 쓰는 경우: 이미 설치된 분필팩을 지우지 않는다
        Run 'claude' @('plugin', 'marketplace', 'update', $market) | Out-Null
        Warn '분필팩 목록은 그대로 두었습니다(내려받기 실패)'
      } else {
        Run 'claude' @('plugin', 'marketplace', 'remove', $market) | Out-Null
        if (Run 'claude' @('plugin', 'marketplace', 'add', $src)) { Ok '분필팩 목록 위치 변경' } else { Fail '분필팩 목록 등록 실패'; return $false }
      }
    } elseif (Run 'claude' @('plugin', 'marketplace', 'add', $src)) { Ok '분필팩 목록 등록' }
    else { Fail '분필팩 목록 등록 실패'; return $false }
    foreach ($p in $plugins) {
      if (CHasPlugin "$p@$market") {
        if (Run 'claude' @('plugin', 'update', "$p@$market")) { Ok "$p — 최신 확인" } else { Warn "$p — 업데이트 확인 실패(지금 버전 유지)" }
      }
      elseif (Run 'claude' @('plugin', 'install', "$p@$market", '-y')) { Ok $p }
      else { Fail "$p — 설치 실패" }
    }
    return $true
  }
  function BunpilCodex([string]$src, [bool]$isRepo, [bool]$isFallback) {
    $line = XMarketLine $market
    if ($line) {
      if (SameSource $line $src) {
        if ($isRepo) {
          if (Run 'codex' @('plugin', 'marketplace', 'upgrade', $market)) { Ok '분필팩 목록 최신으로 갱신' } else { Warn '분필팩 목록 갱신 실패(지금 버전 유지)' }
        } else { Ok '분필팩 목록 확인' }   # 폴더 목록은 plugin add 가 새 내용을 읽는다
      }
      elseif ($isFallback) { Warn '분필팩 목록은 그대로 두었습니다(내려받기 실패)' }
      else {
        Run 'codex' @('plugin', 'marketplace', 'remove', $market) | Out-Null
        if (Run 'codex' @('plugin', 'marketplace', 'add', $src)) { Ok '분필팩 목록 위치 변경' } else { Fail '분필팩 목록 등록 실패'; return $false }
      }
    } elseif (Run 'codex' @('plugin', 'marketplace', 'add', $src)) { Ok '분필팩 목록 등록' }
    else { Fail '분필팩 목록 등록 실패'; return $false }
    foreach ($p in $plugins) { if (Run 'codex' @('plugin', 'add', "$p@$market")) { Ok $p } else { Fail "$p — 설치 실패" } }
    return $true
  }

  # ── 추천 묶음 (catalog/recommended.json과 같게 유지) ─────
  function RecsClaude {
    if (InProfile 'teacher') {
      Write-Host '  [teacher] 한글·문서·자동화·하네스' -ForegroundColor DarkGray
      if (-not $skipHwpx) { CPlugin 'airmang/hwpx-plugins' 'hwpx-plugin@hwpx' '한글(HWPX) 편집 엔진 · airmang/hwpx-plugins' }
      CPlugin 'chrisryugj/kordoc' 'kordoc@kordoc' '한글·PDF 읽기·공문 프리셋 · chrisryugj/kordoc'
      if ($st.hasNpx) {
        McpAdd 'claude' 'kordoc' 'kordoc 문서 도구 17종(MCP)' @('npx', '-y', 'kordoc', 'mcp')
        McpAdd 'claude' 'playwright' '브라우저 자동화 RPA(MCP) · microsoft/playwright' @('npx', '-y', $playwrightMcp)
      } else { Skip 'kordoc MCP·브라우저 자동화 — Node.js가 없어 건너뜀' }
      if ($st.hasUvx) { McpAdd 'claude' 'markitdown' '파일 → 텍스트 변환(MCP) · microsoft/markitdown' @('uvx', 'markitdown-mcp'); WarmMarkitdown }
      else { Skip '파일 → 텍스트 변환(markitdown) — uv가 없어 건너뜀' }
      CPlugin 'revfactory/harness' 'harness@harness-marketplace' '하네스 팩토리 · revfactory/harness'
    }
    if (InProfile 'creator') {
      Write-Host '  [creator] 웹·디자인·영상' -ForegroundColor DarkGray
      CPlugin 'nextlevelbuilder/ui-ux-pro-max-skill' 'ui-ux-pro-max@ui-ux-pro-max-skill' 'UI·UX 디자인 · ui-ux-pro-max'
      CPlugin 'Leonxlnx/taste-skill' 'taste-skill@taste-skill' '디자인 감각 · taste-skill'
      CPlugin 'pbakaus/impeccable' 'impeccable@impeccable' '디자인 다듬기 · impeccable'
      CPlugin 'bradautomates/claude-video' 'watch@claude-video' '영상 보고 요약 · claude-video(watch)'
      SkillsAdd 'aldegad/sprite-gen' 'claude-code' '스프라이트 이미지 · sprite-gen'
    }
    if (InProfile 'dev') {
      Write-Host '  [dev] 개발자용' -ForegroundColor DarkGray
      CPlugin 'obra/superpowers-marketplace' 'superpowers@superpowers-marketplace' '개발 습관 스킬 · superpowers'
      CPlugin 'multica-ai/andrej-karpathy-skills' 'andrej-karpathy-skills@karpathy-skills' '카파시식 코딩 지침'
      CPlugin 'JuliusBrussee/caveman' 'caveman@caveman' '토큰 절약 · caveman'
      if (Has 'codex') { CPlugin 'openai/codex-plugin-cc' 'codex@openai-codex' 'Claude에서 Codex에게 맡기기 · codex-plugin-cc' }
      else { Skip 'codex-plugin-cc — Codex가 없어 건너뜀' }
      SkillsAdd 'Panniantong/Agent-Reach' 'claude-code' '웹·SNS 읽기 · Agent-Reach (도구 설치는 에이전트가 안내)'
      CMarket 'affaan-m/ECC' 'ecc' 'Everything Claude Code(ECC)'
      CMarket 'wshobson/agents' 'claude-code-workflows' '개발 워크플로 모음 · wshobson/agents'
      CMarket 'google/skills' 'google-plugins' 'Google Cloud 스킬 · google/skills'
      CMarket 'thedotmack/claude-mem' 'thedotmack' '세션 기억 · claude-mem'
    }
  }
  function RecsCodex {
    if (InProfile 'teacher') {
      Write-Host '  [teacher] 한글·문서·자동화·하네스' -ForegroundColor DarkGray
      if (-not $skipHwpx) {
        if ($isWin) { Skip '한글(HWPX) 편집 엔진 · hwpx-plugin — Windows용 Codex에서는 실행되지 않아 건너뜀 (한글 양식 보고서·kordoc이 대신 맡음)' }
        else { XPlugin 'airmang/hwpx-plugins' 'hwpx-plugin@hwpx' '한글(HWPX) 편집 엔진 · airmang/hwpx-plugins' }
      }
      if ($st.hasNpx) {
        McpAdd 'codex' 'kordoc' 'kordoc 문서 도구 17종(MCP) · chrisryugj/kordoc' @('npx', '-y', 'kordoc', 'mcp')
        McpAdd 'codex' 'playwright' '브라우저 자동화 RPA(MCP) · microsoft/playwright' @('npx', '-y', $playwrightMcp)
      } else { Skip 'kordoc·브라우저 자동화 — Node.js가 없어 건너뜀' }
      if ($st.hasUvx) { McpAdd 'codex' 'markitdown' '파일 → 텍스트 변환(MCP) · microsoft/markitdown' @('uvx', 'markitdown-mcp'); WarmMarkitdown }
      else { Skip '파일 → 텍스트 변환(markitdown) — uv가 없어 건너뜀' }
      SkillsAdd 'revfactory/harness' 'codex' '하네스 팩토리 · revfactory/harness'
    }
    if (InProfile 'creator') {
      Write-Host '  [creator] 웹·디자인·영상' -ForegroundColor DarkGray
      SkillsAdd 'nextlevelbuilder/ui-ux-pro-max-skill' 'codex' 'UI·UX 디자인 · ui-ux-pro-max'
      SkillsAdd 'Leonxlnx/taste-skill' 'codex' '디자인 감각 · taste-skill'
      SkillsAdd 'pbakaus/impeccable' 'codex' '디자인 다듬기 · impeccable'
      XPlugin 'bradautomates/claude-video' 'watch@claude-video' '영상 보고 요약 · claude-video(watch)'
      SkillsAdd 'aldegad/sprite-gen' 'codex' '스프라이트 이미지 · sprite-gen'
    }
    if (InProfile 'dev') {
      Write-Host '  [dev] 개발자용' -ForegroundColor DarkGray
      SkillsAdd 'obra/superpowers' 'codex' '개발 습관 스킬 · superpowers'
      SkillsAdd 'multica-ai/andrej-karpathy-skills' 'codex' '카파시식 코딩 지침'
      SkillsAdd 'JuliusBrussee/caveman' 'codex' '토큰 절약 · caveman'
      SkillsAdd 'Panniantong/Agent-Reach' 'codex' '웹·SNS 읽기 · Agent-Reach (도구 설치는 에이전트가 안내)'
      XMarket 'affaan-m/ECC' 'ecc' 'Everything Claude Code(ECC)'
      XMarket 'wshobson/agents' 'claude-code-workflows' '개발 워크플로 모음 · wshobson/agents'
      XMarket 'google/skills' 'google-plugins' 'Google Cloud 스킬 · google/skills'
      XMarket 'thedotmack/claude-mem' 'claude-mem-local' '세션 기억 · claude-mem'
    }
  }

  # ── 실행 ─────────────────────────────────────────────────
  if ($recs) { Say ('추천 묶음: ' + ($profileList -join ',')) } else { Say '추천 묶음: 설치 안 함' }
  Say ''
  Head '[분필팩 준비]'
  $pack = PreparePack
  if (-not $pack.ok) {
    Say ''; Warn '분필팩을 준비하지 못해 멈춥니다.'
    if ($oldOutEnc) { try { [Console]::OutputEncoding = $oldOutEnc } catch { } }
    return
  }
  $source = $pack.source; $sourceIsRepo = [bool]$pack.repo; $sourceFallback = [bool]$pack.fallback
  Say ''
  if ($st.hasClaude) {
    Head ('[Claude Code] ' + (FirstLine 'claude' @('--version')))
    if ((BunpilClaude $source $sourceIsRepo $sourceFallback) -and $recs) { RecsClaude }
    Say ''
  }
  if ($st.hasCodex) {
    Head ('[Codex] ' + (FirstLine 'codex' @('--version')))
    if ((BunpilCodex $source $sourceIsRepo $sourceFallback) -and $recs) { RecsCodex }
    Say ''
  }
  if ($recs -and (InProfile 'teacher')) {
    Head '[공통]'
    HwpxNew
    PptxMaker
    Say ''
  }

  if ($nalssam) { NalssamGuide; Say '' }

  Head '다음 단계'
  if ($st.pathChanged) { Write-Host '  ※ 새로 설치한 명령이 잡히도록 지금 PowerShell 창을 닫고 새 창을 여세요.' -ForegroundColor Yellow }
  if ($st.hasClaude) {
    Say '  Claude Code'
    Say '   1. 작업 폴더를 만들고 실행:  mkdir -Force ~\분필작업 > $null; cd ~\분필작업; claude'
    Say '   2. 처음이면 브라우저에서 로그인 → 대화창에 "설정 시작해줘"'
    Say '   3. 노션·패들렛·캔바 연결: 대화창에서  /mcp  → 서비스 선택 → 로그인'
  }
  if ($st.hasCodex) {
    Say '  Codex'
    Say '   1. 작업 폴더를 만들고 실행:  mkdir -Force ~\분필작업 > $null; cd ~\분필작업; codex'
    Say '   2. 처음이면 "Sign in with ChatGPT"로 로그인 → /hooks 에서 분필 가드 신뢰(trust)'
    Say '   3. 대화창에 "설정 시작해줘"  ·  노션 연결:  codex mcp login notion'
  }
  if ($recs -and (-not $st.hasNpx -or -not $st.hasUvx)) {
    if ($withTools) { Say '  Node.js·uv를 준비하지 못해 일부 도구를 건너뛰었습니다. 인터넷 연결을 확인하고 같은 명령을 다시 실행하세요.' }
    else { Say '  건너뛴 도구를 채우려면 앞에 $env:BUNPIL_WITH_TOOLS="1"; 을 붙여 다시 실행하세요.' }
  }
  if ($recs -and -not $st.hasGit) {
    if ($isWin) { Say '  Git을 설치하면 건너뛴 추천 도구도 설치됩니다:  winget install --id Git.Git -e   (설치 후 새 창에서 같은 명령 다시 실행)' }
    else { Say '  Git을 설치하면 건너뛴 추천 도구도 설치됩니다. 설치 후 같은 명령을 다시 실행하세요.' }
  }
  Say "  업데이트는 같은 명령을 다시 실행하면 됩니다. 자세한 안내: $site"
  Say ''
  if ($st.errors -gt 0) { Warn "일부 항목($($st.errors)건)이 실패했습니다. 위 메시지를 확인하고 다시 실행해 보세요." }
  else { Ok "분필팩 설치 완료. 학생 이름은 '학생A'처럼 바꿔 쓰세요. 결과물은 모두 초안입니다." }
  if ($oldOutEnc) { try { [Console]::OutputEncoding = $oldOutEnc } catch { } }
} $bunpilScriptDir $bunpilPresetArg
} finally {
  if ($bunpilOldEnc) { try { [Console]::OutputEncoding = $bunpilOldEnc } catch { } }
  Remove-Variable -Name bunpilPreset, bunpilPresetArg, bunpilScriptDir, bunpilOldEnc -ErrorAction SilentlyContinue
}
