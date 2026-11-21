# 화면이 움직이지 않을 때 · 다른 컴퓨터에서 쓸 때

## 다른 컴퓨터에 등록하기 (스킬 없이 한 줄)

교실 PC나 동료 컴퓨터에는 분필팩이 없어도 된다. 아래 한 줄을 실행하고 **PowerPoint를 완전히 종료했다가 다시 연다.** 현재 사용자 계정에만 등록되고 관리자 권한이 필요 없다.

| 컴퓨터 | 등록 | 지우기 |
|---|---|---|
| Windows (PowerShell 또는 명령 프롬프트) | `powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/live-html/register.ps1 \| iex"` | `powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/live-html/unregister.ps1 \| iex"` |
| Mac (터미널) | `curl -fsSL https://nalssam-bunpil.vercel.app/live-html/register.sh \| sh` | `curl -fsSL https://nalssam-bunpil.vercel.app/live-html/register.sh \| sh -s -- --remove` |

안내 페이지: https://nalssam-bunpil.vercel.app/live-html/

등록이 하는 일: 추가 기능 설정 파일(`manifest.xml`, 주소만 적힌 작은 파일)을 내려받아 Windows는 `%LOCALAPPDATA%\LiveHTML`에 두고 레지스트리 `HKCU\Software\Microsoft\Office\16.0\WEF\Developer`에 그 경로를 적는다. Mac은 `~/Library/Containers/com.microsoft.Powerpoint/Data/Documents/wef`에 둔다. 프로그램을 설치하지 않는다.

## 증상별 확인

| 보이는 것 | 원인 | 할 일 |
|---|---|---|
| 그림만 보이고 눌러도 반응이 없다 | 추가 기능이 등록되지 않았다 | 위 한 줄로 등록하고 PowerPoint를 다시 연다. `register_addin.py --status`로 확인 |
| 위쪽에 노란 줄 "보호된 보기"가 있다 | 내려받거나 메신저로 받은 파일 | **편집 사용**을 누른다 |
| "추가 기능 오류 — 추가 기능을 로드할 수 없습니다. 네트워크/인터넷 연결을 확인…" | 추가 기능 페이지를 불러오지 못했다 | 인터넷 연결 확인 후 **다시 시도**. 학교망이 `nalssam-bunpil.vercel.app`, `appsforoffice.microsoft.com`을 막는지 정보 담당 선생님께 확인 |
| "이 추가 기능은 더 이상 사용할 수 없습니다" | 등록 기록이나 설정 파일이 지워졌다 | 다시 등록하고 PowerPoint를 다시 연다 |
| 아래에 "웹 엔진이 오래되어 HTML을 실행할 수 없습니다" | Office 2016·2019 | Microsoft 365 또는 Office 2021 이상이 깔린 컴퓨터에서 연다. 안 되면 미리보기 그림으로 발표하거나 `deck.html`을 브라우저로 띄운다 |
| 편집 화면에서는 되는데 슬라이드 쇼에서 빈 화면 | 오래된 빌드의 그래픽 가속 문제 | 파일 → 옵션 → 고급 → "슬라이드 쇼 하드웨어 그래픽 가속 사용 안 함"을 켠다. PowerPoint를 업데이트한다 |
| 발표자 보기 화면에서 눌러도 안 된다 | 발표자 보기는 조작할 수 없다 | 청중이 보는 화면에서 누른다. 한 화면으로 발표할 때는 슬라이드 쇼 → "발표자 보기 사용"을 끈다 |
| 화면을 누른 뒤 키보드로 넘어가지 않는다 | 키보드가 HTML 쪽에 있다 | ← → PageUp PageDown은 그대로 넘어간다. 입력칸·슬라이더를 쓰던 중이면 화면의 빈 곳을 한 번 누른 뒤 누른다 |
| 등록이 되지 않거나 다시 열어도 그림만 보인다 | 학교 PC 정책이 웹 추가 기능을 막는다 | 정보 담당 선생님께 "Office 웹 추가 기능(개발자 등록) 허용"을 문의한다. 그동안은 그림 또는 브라우저로 발표 |
| 글꼴이 다르게 보인다 | 그 컴퓨터에 글꼴이 없다 | 덱의 글꼴 목록 뒤쪽(맑은 고딕 등)으로 표시된 것이다. 내용에는 영향 없다 |
| 슬라이드를 떠났다 돌아오니 처음 상태다 | 슬라이드마다 따로 실행된다 | 정상이다. 한 활동은 한 장에서 끝낸다 |

## 쓸 수 있는 곳과 없는 곳

| 환경 | 동작 |
|---|---|
| Windows·Mac의 Microsoft 365, Office 2021·2024 | 움직인다(등록 필요) |
| Office 2016·2019 | 그림만 |
| 웹용 PowerPoint | 기본은 그림. 홈 → 추가 기능 → 기타 설정 → 내 추가 기능 업로드(Upload My Add-in)에서 `manifest.xml`을 올린 뒤 슬라이드에 "Live HTML"을 직접 넣고 HTML 파일을 고르면 그 장은 움직인다. 브라우저마다 다시 올려야 한다 |
| 휴대폰·태블릿 앱, 한쇼, 구글 슬라이드, 키노트 | 그림만 |
| PDF 저장, 인쇄, 동영상 내보내기 | 그림으로 나온다 |

## 덱을 고칠 때

pptx 안의 HTML을 직접 고치지 않는다. `deck.html`을 고친 뒤 다시 변환하면 된다(등록은 다시 하지 않아도 된다). PowerPoint에서 슬라이드 순서를 바꾸거나 일부를 지워도 되고, 보통 슬라이드를 사이에 끼워도 된다. HTML 한 장만 바꾸고 싶으면 편집 화면에서 그 슬라이드 오른쪽 위 톱니바퀴(⚙)를 눌러 HTML 파일과 보여 줄 번호를 다시 고른다.

## 개인정보와 보안

- HTML은 pptx 파일 안에 저장되고, 추가 기능 페이지는 그것을 꺼내 화면에 그릴 뿐 어디로도 보내지 않는다. 다만 pptx를 받은 사람은 안의 HTML을 볼 수 있다.
- 추가 기능 페이지(`https://nalssam-bunpil.vercel.app/live-html/app.html`)와 Microsoft의 Office 구성 요소(`appsforoffice.microsoft.com`)를 불러올 때 일반적인 웹 접속 기록이 그 서버에 남는다.
- 덱은 격리된 틀에서 실행되어 컴퓨터의 파일이나 다른 슬라이드에 접근하지 못한다.
- 출처를 모르는 사람이 준 살아있는 PPT는 일반 웹 페이지처럼 화면에 무엇이든 그릴 수 있으므로, 믿을 수 있는 사람이 만든 파일만 연다.
