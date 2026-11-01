# 이미지 3종 만드는 법
공통: 그림에 로고·상표·실존/브랜드 캐릭터 금지, 그림 속 글자는 짧은 제목·라벨만(긴 문장은 슬라이드 글자로). 사용자가 직접 만들어 준 이미지는 그대로 쓴다. 생성 전 `balance` 로 잔액을 보고, 10장 이상이면 소모량을 한 줄로 알린다.

**ⓐ 클레이 오브젝트 (개념 장표)** — Higgsfield `nano_banana_pro`, 4:3, 스타일 앵커 1장을 참조로.
- 앵커 확보 순서: ① 사용자가 올린 이전 날쌤 스타일 덱의 일러스트 1장(python-pptx `shape.image.blob`로 꺼냄) ② 날쌤 본인 작업이면 프로젝트 문서 `claude/nalssam_anchor_clay.b64.txt`(base64 → `base64 -d`) ③ 없으면 텍스트만(아래 대체 문구).
- 흐름: `media_upload`(filename, content_type) → 응답의 curl 대로 `PUT`(헤더 `Content-Type`, `If-None-Match: *`) → HTTP 200 확인 → `media_confirm`(type=image) → `generate_image_batch`(requests[] 최대 12: `model`, `prompt`, `aspect_ratio`, `medias:[{value:<media_id>, role:'image'}]`, role 은 서버가 보정) → `jobs_wait`(15초 이하, `all_terminal` 까지 반복) → 결과 URL 을 `curl -o` 로 즉시 저장(URL 은 영구가 아니다) → `python fixbg.py g*.png` → `*_fx.jpg` 를 덱에 넣는다.
- 프롬프트 틀: `Same illustration style as the reference image: soft 3D clay and matte ceramic objects, muted teal, deep navy, terracotta coral and cream palette, warm plain off-white background, soft studio light, gentle shadow, isolated object, no text, no letters, no logos. Subject: …` (앵커가 없으면 첫 구절을 빼고 `soft 3D paper-craft and glass orb render` 를 더한다)
- 주제는 장의 메시지를 사물 하나로: 말풍선+만년필(프롬프트) · 폴더 더미+유리구슬(컨텍스트) · 작업대의 하네스에 걸린 구슬(하네스) · 트랙 위 로봇(루프) · 지휘자와 로봇 셋(멀티에이전트) · 조종 콘솔(환경 설정) · 칠판 있는 교실(적용) · 계단 세 칸+트로피(단계) · 두 층 사무실의 로봇 넷(부서 운영).
- 생성물은 몽땅 모아보기로 보고, 어색한 것만 프롬프트를 고쳐 재생성(최대 2회).

**ⓑ 셰프 마스코트 스토리 장면 (전면 16:9)** — 원본은 사용자가 ChatGPT(gpt-image)로 직접 만든 장면이다. 새로 필요하면 사용자가 ChatGPT 로 만들게 하거나, Higgsfield `gpt_image_2_5`(16:9)로 만든다. 마스코트 참조 이미지(`claude/nalssam_anchor_chef.b64.txt` 또는 사용자 첨부)를 `medias` 로 넣으면 캐릭터가 이어진다.
- 은유 체계: 단일 에이전트 = 혼자 요리하는 셰프 · 멀티에이전트 = 주방 분업 · 프롬프트 = 레시피 카드 · 컨텍스트 = 요리책 + 알레르기 표시 · 하네스 = 조리도구 + 안전 체크리스트 · 루프 = 맛보고 고치기.
- 프롬프트 틀: `Cute original 3D toy-style mascot scene, 16:9. A round white-headed, mint-tinted little chef robot with a white chef hat, mint apron with a small chef-hat emblem, big glossy dark-green eyes, rosy cheeks. Warm cream restaurant kitchen, copper pendant lamps, green plants, glowing mint cable lines linking the stations. Orange pill-shaped label chips with short Korean words: '…'. Bold rounded dark-green Korean heading: '…'. Warm soft light, glossy vinyl-toy finish, no logos, no brand characters.` 그림 속 한글 철자를 반드시 확인하고, 틀리면 재생성하거나 글자를 빼고 슬라이드 글자로 얹는다.

**ⓒ 실제 화면 캡처** — Canva(`export-design` → PDF → `pdftoppm -r 150`/`pdfimages`), Padlet(MCP 로 내용 확인 → 공개 URL 을 Playwright 전체 페이지 스크린샷), Drive(`download_file_content`), 브라우저(크롬 연결), 사용자 컴퓨터의 파일. 학생 이름·얼굴·개인정보는 가리거나 크롭하고, 사이드바 글자가 섞이면 다시 크롭한다. 장표에는 `cards3` cover + `adj=5000, line=LINE`, 부제에 "실제 화면: …".

- 이미지 생성 도구(Higgsfield·ChatGPT 등)는 각자 계정이 있어야 한다. 계정이 없으면 "가진 이미지만" 방식으로 글자·도형만 써도 같은 스타일이 나온다(`cards3`에 경로 대신 `None`).
- 학생 얼굴이 나온 사진은 쓰지 않는다. 꼭 필요하면 보호자 동의를 확인하고 얼굴을 가린다.
