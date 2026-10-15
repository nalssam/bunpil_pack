# 분필팩 개인정보 가드 (Windows PowerShell 5.1+). 규칙은 guard.sh와 같다.
# 이 파일은 빌드 때 BOM 붙은 UTF-8로 저장된다(PowerShell 5.1이 한글을 바르게 읽도록).
param([string]$Mode = "prompt")
if ($env:BUNPIL_GUARD -eq "off") { exit 0 }

# 훅은 창 없이(콘솔 없이) 실행될 수 있어 콘솔 인코딩 설정에 기대지 않는다.
# 입력은 바이트로 읽어 UTF-8로 풀고, 출력 JSON은 한글을 \uXXXX로 바꿔 ASCII로만 내보낸다.
$inputText = ''
try {
  $ms = New-Object System.IO.MemoryStream
  [Console]::OpenStandardInput().CopyTo($ms)
  $inputText = (New-Object System.Text.UTF8Encoding($false)).GetString($ms.ToArray()).TrimStart([char]0xFEFF)
} catch {
  try { $inputText = [Console]::In.ReadToEnd() } catch { $inputText = '' }
}
function Write-Json($obj) {
  $json = $obj | ConvertTo-Json -Compress -Depth 4
  $json = [regex]::Replace($json, '[^\x00-\x7F]', { param($m) '\u{0:x4}' -f [int][char]$m.Value })
  $b = [System.Text.Encoding]::ASCII.GetBytes($json + "`n")
  $o = [Console]::OpenStandardOutput(); $o.Write($b, 0, $b.Length); $o.Flush()
}
function Write-Err([string]$msg) {
  $b = (New-Object System.Text.UTF8Encoding($false)).GetBytes($msg + "`n")
  $o = [Console]::OpenStandardError(); $o.Write($b, 0, $b.Length); $o.Flush()
}

$rrnHyphen = '(^|[^0-9])[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])-[1-8][0-9]{6}([^0-9]|$)'
$rrnPlain = '(^|[^0-9])[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[1-8][0-9]{6}([^0-9]|$)'
$phone = '(^|[^0-9])01[016789][- .]?[0-9]{3,4}[- .]?[0-9]{4}([^0-9]|$)'
$classNo = '[0-9] ?학년 ?[0-9]{1,2} ?반 ?[0-9]{1,2} ?번'

if ($inputText -match $rrnHyphen) {
  if ($Mode -eq "write") {
    $ask = @{
      systemMessage = "[분필 가드] 쓰려는 내용에 주민등록번호 형식이 있습니다. 실제 번호라면 거절하세요."
      hookSpecificOutput = @{
        hookEventName = "PreToolUse"
        permissionDecision = "ask"
        permissionDecisionReason = "분필 가드: 주민등록번호 형식(000000-0000000)이 파일에 들어갑니다. 실제 개인정보가 아니거나 지우는 수정일 때만 허용하세요."
      }
    }
    Write-Json $ask
    exit 0
  }
  Write-Err "[분필 가드] 주민등록번호 형식(000000-0000000)이 있어 입력을 막았습니다. 그 부분을 지우고 다시 보내 주세요. (끄기: BUNPIL_GUARD=off)"
  exit 2
}

$found = @()
if ($inputText -match $rrnPlain) { $found += "13자리 번호(주민번호일 수 있음)" }
if ($inputText -match $phone) { $found += "휴대전화 번호" }
if ($inputText -match $classNo) { $found += "학년·반·번호" }

if ($found.Count -gt 0) {
  $warn = $found -join ", "
  $hookEvent = if ($Mode -eq "write") { "PreToolUse" } else { "UserPromptSubmit" }
  $out = @{
    systemMessage = "[분필 가드] $warn 형식이 보입니다. 실제 개인정보라면 가명으로 바꿔 주세요."
    hookSpecificOutput = @{
      hookEventName = $hookEvent
      additionalContext = "분필 가드 경고: 입력 또는 쓰려는 내용에 $warn 형식의 정보가 있다. 실제 학생·학부모 정보일 수 있으므로 진행 전에 사용자에게 알리고 '학생A'처럼 가명 처리하자고 먼저 제안하라. 바코드·주문번호처럼 개인정보가 아니면 그대로 진행한다. 결과물에는 개인정보를 넣지 않는다."
    }
  }
  Write-Json $out
}
exit 0
