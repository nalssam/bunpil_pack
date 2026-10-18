# 변경 기록

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
