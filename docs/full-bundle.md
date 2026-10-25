# full 묶음 — 날쌤 환경 그대로

날쌤의 Claude 앱(claude.ai)에 켜 둔 플러그인과 커넥터를 한 번에 설치하는 묶음이다. 2026년 10월 25일 기준 목록이다. 강의에서 본 환경을 최대한 비슷하게 만드는 것이 목적이라, 교사 업무와 관계없는 금융·기업용 서비스도 그대로 들어 있다.

- 설치: 사이트의 "설치 문장 만들기"에서 **full**을 더하거나, 터미널에서 `--profile full`(Windows는 `$env:BUNPIL_PROFILE="full";`)을 쓴다. teacher와 함께 쓰려면 `--profile teacher,full`이다.
- 걸리는 시간: 플러그인 50여 개를 각 원 저장소에서 받아 10분 안팎이다.
- 설치와 연결은 다르다. 플러그인은 설치되자마자 스킬이 쓰이지만, 서비스에 접속하는 MCP는 처음 쓸 때 그 서비스에 로그인해야 한다. 계정이 없는 서비스는 꺼 두어도 된다(Code 탭 입력창 옆 **+** → **Plugins** → **Manage plugins**, 터미널은 `/plugin`).
- 분필팩은 이 도구들을 복사하지 않는다. 각 원 저장소(마켓플레이스)에서 설치만 하고, 라이선스는 각 저장소를 따른다.

## 1. Anthropic 공식 업무 플러그인 (18종)

마켓플레이스 [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) (Apache-2.0). Claude Code와 Codex 모두에 설치된다.

| 플러그인 | 하는 일 |
|---|---|
| productivity | 할 일·일정 정리, 업무 기억 |
| enterprise-search | 메일·문서·채팅을 한 번에 검색 |
| cowork-plugin-management | 플러그인 만들기·고치기 |
| sales | 영업 준비·후속 연락·파이프라인 |
| finance | 회계·결산·재무제표 |
| data | SQL, 데이터 탐색, 시각화·대시보드 |
| legal | 계약 검토, NDA 분류, 준법 점검 |
| marketing | 콘텐츠·캠페인·성과 보고 |
| customer-support | 문의 분류, 답변 초안, 지식 문서 |
| product-management | 기능 명세, 로드맵, 사용자 조사 정리 |
| bio-research | 생명과학 문헌·유전체 분석 도구 연결 |
| engineering | 스탠드업, 코드 리뷰, 장애 대응, 기술 문서 |
| human-resources | 채용, 온보딩, 평가, 보상 분석 |
| design | 디자인 비평, 디자인 시스템, UX 문구, 접근성 |
| operations | 업무 절차 문서, 변경 관리, 위험 평가 |
| small-business | 소상공인 업무 흐름(현금 흐름, 청구, 마케팅) |
| brand-voice | 브랜드 말투 지침 만들기·점검 |
| pdf-viewer | PDF 보기·주석·서명·양식 채우기 |

## 2. 서비스 연동 플러그인 (28종)

같은 마켓플레이스에 등록된 각 회사의 공식 플러그인이다. 라이선스는 각 원 저장소를 따른다. 대부분 그 서비스 계정이 있어야 쓰인다.

| 플러그인 | 서비스 | 쓰려면 |
|---|---|---|
| canva | Canva 디자인 만들기·편집·크기 바꾸기 | Canva 계정 |
| figma | Figma 디자인 읽기·쓰기, 디자인→코드 | Figma 계정 |
| adobe-for-creativity | Adobe 사진·영상·디자인 일괄 편집 | Adobe 계정 |
| miro | Miro 보드 읽기·만들기 | Miro 계정 |
| zoom-plugin | Zoom 회의 검색·녹화·요약 | Zoom 계정 |
| learn-with-coursera | Coursera 강좌·학습 자료 검색 | Coursera 계정(검색은 없이도) |
| airtable | Airtable 데이터베이스 | Airtable 계정 |
| monday-com | monday.com 업무 관리 | monday.com 계정 |
| zapier | Zapier로 8,000여 개 앱 자동화 | Zapier 계정 |
| desktop-commander | 내 컴퓨터의 터미널·파일 작업 | - |
| exa | Exa 웹 검색·조사 | Exa 계정 |
| brightdata-plugin | Bright Data 웹 수집 | Bright Data 계정 |
| searchfit-seo | 웹사이트 SEO 점검·콘텐츠 계획 | - |
| postiz | SNS 게시 예약(28개 플랫폼) | Postiz 계정 |
| product-tracking-skills | 서비스 사용 분석 설계 | - |
| base44 | Base44 앱 만들기 | Base44 계정 |
| datadog | Datadog 로그·지표 조회 | Datadog 계정 |
| datarobot-agent-skills | DataRobot 머신러닝 | DataRobot 계정 |
| unity | Unity 게임 개발 | Unity |
| noibu | Noibu 쇼핑몰 오류·전환 분석 | Noibu 계정 |
| grasp | Grasp 기업·거래 조사 | Grasp 계정 |
| bigdata-com | Bigdata.com 금융 조사 | Bigdata.com 계정 |
| daloopa | Daloopa 재무 데이터 | Daloopa 계정 |
| lseg | LSEG 채권·금리·환율 분석 | LSEG 계정 |
| sp-global | S&P Global 기업 자료 | S&P Global 계정 |
| carta-crm | Carta CRM | Carta 계정 |
| carta-investors | Carta 투자사 자료 | Carta 계정 |
| claude-for-financial-advisors | 자산관리 상담 업무 흐름 | 회사 시스템 계정 |

## 3. 그 밖의 플러그인

| 플러그인 | 저장소 | 비고 |
|---|---|---|
| stakeholder-brief, jasoseo | [leeandev/stop-slop-ko](https://github.com/leeandev/stop-slop-ko) (MIT) | 청중 맞춤 공유 문서, 인터뷰로 쓰는 자소서. 같은 저장소의 stop-slop-ko는 teacher 묶음에 들어 있다 |
| contentasoft-cad-converter | [contentasoftware/contentasoft-cad-converter-plugin](https://github.com/contentasoftware/contentasoft-cad-converter-plugin) (MIT) | 3D CAD 변환. Windows의 Claude Code에만 설치한다 |

## 4. 커넥터 (원격 MCP)

플러그인에 들어 있지 않은 커넥터는 각 서비스가 공개한 원격 MCP 주소로 Claude Code와 Codex에 연결한다. 주소는 2026년 10월 25일에 각 서비스 문서와 서버의 로그인 정보로 확인했다. 한 주소를 모든 선생님이 함께 쓰고, 처음 쓸 때 각자 자기 계정으로 로그인한다(Claude Code는 `/mcp`, Codex는 `codex mcp login <이름>`).

| 이름 | 서비스 | 주소 | 비고 |
|---|---|---|---|
| vercel | Vercel 웹 배포·관리 | `https://mcp.vercel.com` | |
| supabase | Supabase 데이터베이스 | `https://mcp.supabase.com/mcp` | 베타 |
| cloudflare | Cloudflare 개발 플랫폼 | `https://mcp.cloudflare.com/mcp` | 예전 Workers Bindings 주소 대신 공식 API 서버 |
| higgsfield | Higgsfield 이미지·영상 AI | `https://mcp.higgsfield.ai/mcp` | |
| hyperframes | HyperFrames(HeyGen) HTML 모션그래픽 | `https://mcp.heygen.com/mcp/hyperframes/` | 끝의 `/`까지 그대로 |
| elevenlabs | ElevenLabs 음성·나레이션 | `https://api.elevenlabs.io/v1/mcp` | 로그인 방식(CIMD)을 지원하는 프로그램에서만 로그인됨 |
| artlist | artlist 음악·효과음·영상 AI | `https://mcp.artlist.io/mcp` | 서비스 안내에는 "Claude에서만 동작"이라고 되어 있음 |
| playmcp | 카카오 PlayMCP | `https://playmcp.kakao.com/mcp` | |
| windsor-ai | Windsor.ai 광고·SNS 성과 데이터 | `https://mcp.windsor.ai/` | |
| threejs-viewer | Three.js 3D 장면 보기 | `https://example-server.modelcontextprotocol.io/threejs/mcp` | MCP 공식 예제(데모) 서버, 로그인 없음 |

Linear는 design·engineering 플러그인에, Zoom·Miro·Figma·Canva·Airtable·monday.com·Zapier·Coursera는 각 플러그인에 연결이 들어 있어 따로 등록하지 않는다. Notion·Padlet·Canva는 분필팩 커넥터 팩에도 있다.

## 5. Claude 앱에서만 켜는 커넥터

아래 커넥터는 모든 선생님이 함께 쓸 수 있는 공용 주소가 없어 설치기가 연결하지 않는다. Claude 앱의 설정 → 커넥터(Code 탭은 입력창 옆 **+** → **Connectors**)에서 켠다.

| 커넥터 | 이유 |
|---|---|
| Gmail, Google 캘린더·드라이브·문서·스프레드시트·슬라이드 | Google의 공식 MCP는 개발자 미리보기라 학교·개인마다 Google Cloud 로그인 클라이언트를 따로 만들어야 한다 |
| Microsoft 365 | Claude 앱 전용 서버이고, 기관(테넌트)이 따로 허용해야 한다 |
| Expedia | 공개 문서가 없어 Claude 앱 밖에서 쓰는 방법을 확인하지 못했다 |
| Coursera | 강좌 검색은 learn-with-coursera 플러그인이 맡는다. Coursera MCP는 Claude 앱 밖의 로그인을 받지 않는다 |
| Notion | 분필팩 커넥터 팩(bunpil-connect)에 이미 들어 있다 |

## 겹치는 것

- Canva·Notion·Padlet은 분필팩 커넥터 팩(bunpil-connect)에도 연결이 들어 있다. Claude Code는 플러그인마다 연결을 따로 두므로 둘 다 있어도 충돌하지 않는다.
- 여러 업무 플러그인이 Slack·Notion·Asana·Atlassian 같은 연결을 함께 가지고 있다. 쓰지 않는 서비스는 로그인하지 않으면 그대로 비활성 상태로 남는다.
