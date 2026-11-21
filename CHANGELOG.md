# 변경 기록

## 0.8.1 — 2026-11-21
- live-pptx 문서 정정(운영 사이트 독립 점검 반영): 확인한 것보다 단정적이던 문구를 바로잡았다. Office 2016은 확인하지 못했고(Office 2019 기관 설치판만 확인), Microsoft 365는 Windows 최신 채널 16.0.20625 한 빌드에서만 확인했다. 업데이트를 늦춘 Microsoft 365는 발표 전에 슬라이드 쇼로 한 번 눌러 보게 안내한다
- 눌러지지 않는 PC를 위한 브라우저 발표 파일: 변환할 때 `--save-html`로 그림·CSS·스크립트를 한 파일로 합친 `deck-browser.html`을 만들어 pptx와 함께 전달한다(그림을 따로 둔 `deck.html`만 옮기면 그림이 깨지던 문제)
- 시작 틀의 ↺(처음 상태로) 단추를 실제 PowerPoint(편집 화면, LTSC 2024)에서 눌러 확인했다: 정답 표시가 지워지고 그 장이 그대로 살아 있다
- 덱 규칙에 점수 세는 퀴즈·그림 크기·4:3·입력칸 제거 같은 가져온 HTML 바꾸기 요령 추가, 문제 해결 문서의 슬라이더·LTSC 쇼·크기 문구 정리
- 안내 페이지: 등록 명령이 하는 일을 먼저 읽어 볼 수 있는 링크, 확인하지 못한 것 목록 보강

## 0.8.0 — 2026-11-21
- 수업자료 팩에 **live-pptx**(살아있는 PPT) 스킬 추가: 슬라이드 안에서 HTML이 실제로 실행되는 PowerPoint 파일을 만든다. 퀴즈 보기를 누르고, 슬라이더를 움직이고, 타이머와 번호 뽑기를 쓸 수 있다
- 실제 PowerPoint(Windows)에서 확인한 범위: **Microsoft 365**는 편집 화면과 슬라이드 쇼에서 모두 눌러진다. Office LTSC 2021·2024는 편집 화면에서만 눌러지고 슬라이드 쇼는 화면만 보인다. Office 2019(기관 설치판)는 미리보기 그림과 안내 줄이 보인다. Office 2016, Mac, 웹용은 확인하지 못했다. 슬라이드 쇼에서 눌러 쓸 수 없는 컴퓨터에서는 함께 주는 `deck.html`을 브라우저로 띄운다
- 구성: 시작 틀(5학년 수학 "크기가 같은 분수" 6장), 변환기(`build_live_pptx.py` — 덱 폴더의 그림·CSS·JS 합치기, Edge·Chrome으로 미리보기 촬영, 발표자 노트, `--strict`), 점검(`qa_live_pptx.py`), 추가 기능 등록(`register_addin.py`, 관리자 권한 불필요)
- 사이트에 추가 기능 페이지와 안내 페이지 추가(`/live-html/`): 받은 파일에 노란 "추가 기능 오류" 줄이 뜨는 컴퓨터에서 한 줄로 등록·해제. 발표할 때 인터넷이 필요하다
- class-slides는 보통 수업 PPT, nalssam-pptx는 연수용, live-pptx는 눌러 보는 활동용으로 나눔. 분필팩 스킬 23종

## 0.7.1 — 2026-11-01
- 수업자료 팩에 **nalssam-pptx**(날쌤 스타일 연수 PPT) 스킬 추가: 「AI Agent 시대, 교실은 어떻게 달라지는가?」 덱의 모양을 python-pptx로 그대로 재현한다. 웜 오프화이트·네이비·틸·코랄, Pretendard 전체 임베드, 장표 유형 13가지, 대본은 메모란, 자동 점검(qa.py)과 렌더링 모아보기(render_check.py), 기존 덱 문구만 바꾸기(edit_helpers.py) 포함
- 강사 소개는 작업 폴더의 지침 파일(setup으로 만든 것)을 쓰고, 날쌤 본인 덱일 때만 날쌤 프로필을 쓴다
- class-slides는 학생 수업용, nalssam-pptx는 교사 연수·강의용으로 나눔. 분필팩 스킬 22종

## 0.7.0 — 2026-10-25
- **full 묶음 추가 (날쌤 환경 그대로)**: 날쌤의 Claude 앱에 켜 둔 플러그인·커넥터를 한 번에 설치한다. Anthropic 공식 업무 플러그인 18종과 서비스 연동 플러그인 28종(anthropics/knowledge-work-plugins), stakeholder-brief·jasoseo, 3D CAD 변환(Windows), 플러그인에 없는 커넥터 10개(원격 MCP). 목록은 docs/full-bundle.md
- Gmail·Google 문서·Microsoft 365·Expedia처럼 공용 연결 주소가 없는 커넥터는 설치하지 않고 Claude 앱에서 켜도록 안내
- Codex에서는 product-tracking-skills·sp-global을 건너뜀(원 저장소의 plugin.json 이름이 마켓 이름과 달라 Codex가 거부)
- teacher 묶음에 **stop-slop-ko**(leeandev/stop-slop-ko, MIT) 추가: 한국어 보고서·공문·메일의 "AI 티"(줄표, 가운뎃점 나열, 번역투)를 걷어낸다
- `--profile all`은 이제 teacher + creator + dev + studio + full

## 0.6.0 — 2026-10-18
- 독립 검토 반영: Windows→WSL2 studio 명령에 `--install-claude`(WSL 안에 Claude Code가 없어 실패하던 문제), Git·bash가 없어 studio를 못 깔면 "설치 완료"가 아니라 실패로 표시, `--bunpil-only`와 함께인 옛 `--nalssam`도 studio 설치, `--profile` 값의 공백·대소문자 차이 무시, 예전 `--profile nalssam`은 teacher+studio(예전과 같게), `--uninstall`이 `nalssam-*` Claude MCP 연결도 해제, 설치 만들기에서 OS·호스트 직접 선택이 상단 토글에 덮이던 문제, studio가 PATH 앞에 둔 python·node와 재설치 시 꺼 둔 플러그인 재활성 안내
- **날쌤팩을 분필팩 안으로 합침**: 따로 배포하던 날쌤팩(nalssam/nalssam-pack v1.0.1, MIT)의 설치 엔진을 `studio/` 폴더로 가져와 **studio 묶음**으로 만듦. 이제 저장소·설치 명령·웹사이트가 `nalssam/bunpil_pack` 하나. `--profile studio`를 쓰고, 옛 `--nalssam` · `BUNPIL_NALSSAM=1` · `--profile nalssam`은 같은 뜻으로 계속 받아들임. 이미 설치한 환경과 이어지도록 명령 이름(`nalssam-pack`)과 설치 기록 폴더(`~/.local/share/nalssam-pack`)는 그대로 둠
- `--profile all`은 teacher + creator + dev + studio(수 GB). Windows는 studio를 바로 설치하지 않고 WSL2 안내만 보여 줌(전과 같음)
- **설치 안내를 앱 채팅창 기준으로 전환**: Claude 앱의 Code 탭, ChatGPT 앱의 Codex 채팅창에 "안내 한 문단 + 명령 한 줄"을 붙여넣으면 AI가 대신 설치. 터미널·명령 프롬프트·PowerShell·VS Code는 "다른 방법"으로 내림. Windows용 채팅 명령은 `powershell -NoProfile -Command "…"` 형태라 PowerShell·명령 프롬프트·Git Bash 어디서 실행돼도 같음. 설치 문장은 `tools/make_site.py` 한 곳에서 만들어 사이트·README·설치 안내가 같음
- 웹사이트 개편: Claude 앱 Code 탭 / ChatGPT 앱 Codex / 앱 메뉴만 / 터미널·VS Code 경로별 6교시 설치 시간표, **묶음 고르기**(teacher · creator · dev · studio), **설치 문장 만들기**(채팅창 문장과 터미널 명령을 함께 생성), 환경별 차이 표 머리글(Chat · Cowork · Code 탭 · Codex), 문제 해결 개편
- README·docs/install.md를 같은 기준으로 다시 씀. 업데이트·지우기도 채팅창 문장으로 안내
- 설치 점검(checkup)·수업 슬라이드(class-slides) 스킬의 안내 문구를 "날쌤팩"에서 "studio 묶음"으로 바꾸고 앱·터미널 환경별로 구분
- studio 설치 후 점검은 채팅창에서 "스튜디오 설치 점검해줘"(터미널은 `nalssam-pack doctor --verify-mcp`)
- Claude 앱 안내를 공식 문서(2026-10-18 열람)에 맞춤: 입력창 옆 권한 선택은 **Manual**로 두기(Auto는 인터넷에서 받은 스크립트 실행을 막을 수 있음), Code 탭의 커넥터는 **+ → Connectors**, 플러그인 관리는 **+ → Plugins → Manage plugins**, Chat·Cowork는 사용자 지정

## 0.5.0 — 2026-10-18
- teacher 묶음에 웹사이트 내용 수집 **Firecrawl**(호스팅 MCP, 키 없이 쓰는 무료 구간 — 수집·검색·읽기) 연결
- teacher 묶음에 최신 뉴스·문서 검색 **Perplexity**(@perplexity-ai/mcp-server) — 유료 키라 `PERPLEXITY_API_KEY`가 있을 때만 연결하고, 없으면 건너뛰고 방법 안내
- creator 묶음에 **인스타그램 스킬 13종**(Jakeschincariol/instagram-agent-skill, MIT — 훅·릴스 대본·화면 자막·캡션) Claude Code·Codex 플러그인으로 설치
- creator 묶음에 이미지·영상 AI **Glif**(glifxyz/glif-mcp-server) 플러그인과 MCP 연결 — 처음 한 번 로그인
- 크롬 연결(Claude in Chrome): 확장 설치는 명령으로 할 수 없어 설치 뒤 '다음 단계'와 사이트 문제 해결에 안내
- creator 묶음에 모션그래픽: **Cinetic** 스킬(Leonxlnx/cinetic, macOS·Linux·WSL2, `skills add`)과 **Prompt Motion**(prompt-motion.com 사례·프롬프트 모음, 링크 안내)
- 새 스킬 **class-video**(수업 영상 만들기, bunpil-class): 스토리보드 승인 → Manim 설명 영상 + edge-tts 한국어 음성, 소개 영상은 Cinetic, 안 되면 HTML+ffmpeg. 준비 점검·개인정보·원작자 권리 안내 포함, 평가 사례 5건
- 중복 정리: Playwright(teacher)·codex-plugin-cc(dev)는 이미 있어 그대로 두고, nalssam 묶음의 Cinetic은 creator 한 줄로 합침(--nalssam이면 날쌤팩이 설치)
- 수정: Perplexity 키를 Claude Code에 등록할 때 인자 순서 오류
- 설치 점검(checkup)이 firecrawl·perplexity·glif를 인식

## 0.4.0 — 2026-10-16
- teacher 묶음에 한국어 발표 자료 엔진 **pptx-maker**(ZZombie04/pptx_maker, MIT) 추가 — 고정 커밋을 `uv tool install`로 설치하고 `pptx-maker setup`으로 Claude Code·Codex에 MCP·스킬 연결(Windows 포함)
- 수업 슬라이드 스킬(class-slides)이 pptx-maker를 먼저 사용(초등 `class_kids`·중등 `class_teen` 용도, 점검·채점 90점 이상)
- **날쌤팩 연동**: `--nalssam`(macOS·Linux·WSL2)으로 날쌤팩 v1.0.1을 함께 설치 — Claude Code가 있으면 `--claude`, 겹치는 추천 도구는 날쌤팩의 고정 버전을 쓰고 분필팩은 건너뜀, 날쌤팩 공통 MCP 중 없는 것(REA·Motion 등)을 Claude Code에 `nalssam-` 이름으로 연결. Windows PowerShell에서는 WSL2 안내
- 추천 도구 표에 nalssam 묶음(Motion Director·Showreel·Cinetic·motion-graphics·REA·After Effects MCP·Claude 네이티브 플러그인 122개)
- 웹사이트: 날쌤팩 단락(분필팩과 비교, 설치 명령), 명령 만들기에 날쌤팩 선택, 문제 해결 2건 추가
- 설치 점검(checkup)이 pptx_maker와 날쌤팩 MCP 이름을 정상으로 인식

## 0.3.0 — 2026-10-15
- 웹사이트 공개: https://nalssam-bunpil.vercel.app — Claude·ChatGPT Codex 탭, 운영체제별 설치 시간표(교시별 진도 표시), 명령 만들기, 문제 해결 찾기, 연수용 큰 화면·QR
- 한 줄 설치 주소: `claude.sh`·`codex.sh`·`install.sh`·`uninstall.sh`(macOS·Linux), 같은 이름의 `.ps1`(Windows)
- 원클릭 내려받기: `bunpil-pack.zip`(Install-Windows.bat·Install-Mac.command 더블클릭 설치, 인터넷 없이 분필팩 5종 설치)
- 설치 스크립트가 분필팩을 `~/.bunpil`에 내려받아 로컬 마켓플레이스로 등록 — Git 없이 설치, 위치가 바뀌면 자동으로 다시 등록
- 없으면 설치: Claude Code·Codex CLI(공식 설치 프로그램), Node.js(공식 배포본, 관리자 권한 없이 `~/.bunpil/node`), uv, Git(Windows는 winget, 맥은 개발자 도구 설치 창)
- Git이 없으면 Git이 필요한 추천 도구만 '건너뜀'으로 처리하고 안내(실패로 세지 않음). 맥의 `/usr/bin/git` 자리표시자 구분
- 내려받기에 실패해도 이미 설치된 분필팩을 지우지 않음(있던 분필팩 폴더 재사용), 폴더 교체를 안전하게(옮기기 실패 시 멈춤)
- 업데이트 확인이 실패하면 ✓ 대신 경고로 표시
- 새 터미널에서도 명령을 찾도록 PATH 저장(macOS·Linux `~/.bunpil/env`, Windows 사용자 PATH)
- Windows용 개인정보 가드 훅: Git Bash 없이 PowerShell로 실행(exec 형식), 설치 시 자동으로 바꿔 끼움
- Windows MCP 등록 시 npx를 `cmd /c`로 감쌈, npm으로 Codex를 설치하면 실행 정책 안내·조정
- Windows: 사용자 PATH를 레지스트리 원문(REG_EXPAND_SZ) 그대로 다룸, 공식 설치 프로그램은 64비트 콘솔 PowerShell로 실행(ISE·32비트 창 대응)
- Windows 더블클릭 설치 파일과 Codex 훅에서 인코딩된 명령(-EncodedCommand)을 없애고 `-File`로 실행, Codex 훅은 cmd의 `%PLUGIN_ROOT%` 사용
- PowerShell 가드: 콘솔 없이 실행돼도 한글을 바르게 읽고(UTF-8 바이트), 출력 JSON은 ASCII로만 냄
- Windows용 Codex에서는 hwpx-plugin(bash 전용 MCP)을 건너뛰고 hwpx_new·kordoc이 대신 맡음
- 저장소 `nalssam/bunpil_pack`, 작성자 표기 `nalssam(날쌤) · 몽당분필`

## 0.2.0 — 2026-10-13
- 한 줄 설치에 날쌤 추천 묶음 반영: teacher(기본)·creator·dev 묶음, `--profile`로 선택
  - teacher: hwpx-plugins, kordoc(플러그인+MCP), hwpx_new(MCP), markitdown(MCP), playwright(MCP), revfactory/harness
  - creator: ui-ux-pro-max, taste-skill, impeccable, claude-video, sprite-gen
  - dev: superpowers, karpathy-skills, caveman, codex-plugin-cc, Agent-Reach, ECC·wshobson·google·claude-mem 마켓플레이스 등록
- 새 스킬 harness-gallery: revfactory/harness-100 한국어 예시를 골라 가져와 학교에 맞게 고치기
- hwpx-doc: 한글 도구 3종 역할 구분, checkup: 추천 묶음 점검

## 0.1.0 — 2026-10-13 (알파)
- 플러그인 5종, 스킬 19종, Claude 서브에이전트 6종
- Claude·Codex 마켓플레이스 동시 지원, Claude 앱 업로드용 zip
- 개인정보 가드 훅(sh·PowerShell), 합성 100문장 시험 통과
- 평가 사례 95건(스킬당 5건)
