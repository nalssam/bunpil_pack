#!/usr/bin/env python3
"""개인정보 가드 합성 102문장 시험.
차단 20(하이픈 등록번호) · 경고 30(13자리·바코드·휴대전화·반번호) · 통과 52.
파일 쓰기 모드: 하이픈 등록번호는 차단 대신 확인 요청(ask).
기본은 guard.sh. 환경변수 PWSH=<pwsh 경로>를 주면 guard.ps1도 같은 문장으로 시험하고,
출력 JSON이 ASCII로만 되어 있는지(콘솔 인코딩과 무관하게 읽히는지) 확인한다.
"""
import os
import json
import random
import subprocess
import sys
from pathlib import Path

random.seed(7)
HOOKS = Path(__file__).resolve().parent.parent / "src/plugins/bunpil-start/hooks"
PWSH = os.environ.get("PWSH")
CMDS = {"sh": ["sh", str(HOOKS / "guard.sh")]}
if PWSH:
    CMDS["ps1"] = [PWSH, "-NoProfile", "-NonInteractive", "-File", str(HOOKS / "guard.ps1")]
names = ["김가명", "이가상", "박예시", "최시험", "정연습"]


def rrn(sep="-"):
    return f"{random.randint(0,25):02d}{random.randint(1,12):02d}{random.randint(1,28):02d}{sep}{random.choice('1234')}{random.randint(0,999999):06d}"


block = [f"학생 {random.choice(names)} 주민번호 {rrn()} 확인" for _ in range(20)]
warn = ["바코드 8801043014809 상품 10개 품의", f"학생 번호 {rrn('')} 정리"]
warn += [f"학부모 연락처 010-{random.randint(1000,9999)}-{random.randint(1000,9999)}로 안내 문자 써줘" for _ in range(13)]
warn += [f"{random.randint(1,6)}학년 {random.randint(1,9)}반 {random.randint(1,30)}번 {random.choice(names)} 결석계 정리" for _ in range(15)]
clean_t = ["주문번호 202610130001 배송", "택배 송장 6892 1234 5678", "4학년 과학 물의 상태 변화 학습지 만들어줘",
           "공문 마감일 2026. 10. 30. 확인", "학교 대표번호 031-123-4567로 문의", "예산 1,250,000원 산출내역",
           "학번 체계 설명해줘", "3학년 국어 지도안", "5학년 2반 학급 규칙 포스터", "문항 20개 중 15번 해설",
           "2026학년도 1학기 평가 계획", "도서 ISBN 9788936434120 확인", "시간표 9:00~9:40", "정답률 87.5%",
           "교실 번호 302호", "전화 02-2100-6000 교육청", "사업자등록번호 123-45-67890"]
clean = [clean_t[i % len(clean_t)] + ("" if i < len(clean_t) else f" (메모 {i})") for i in range(52)]


bad_json = []


def run(cmd, text, mode="prompt"):
    if mode == "prompt":
        payload = {"prompt": text}
    elif mode == "write-codex":
        payload = {"tool_name": "apply_patch", "tool_input": {"command": text}}
    else:
        payload = {"tool_input": {"content": text}}
    p = subprocess.run(cmd + [mode], input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                       capture_output=True)
    out = p.stdout.decode("utf-8", "replace")
    if p.returncode == 2:
        if "분필 가드" not in p.stderr.decode("utf-8", "replace"):
            bad_json.append(("stderr", text))
        return "block"
    if out.strip():
        try:
            d = json.loads(out)
        except ValueError:
            bad_json.append(("json", text))
            return "bad"
        if cmd[0] != "sh" and not p.stdout.isascii():
            bad_json.append(("ascii", text))
        decision = d.get("hookSpecificOutput", {}).get("permissionDecision")
        if decision in ("ask", "deny"):
            return decision
        return "warn"
    return "clean"


# Codex 파일 쓰기(apply_patch): 더하는 줄만 본다. 지우는 줄의 번호는 막지 않는다
r = rrn()
codex_cases = [
    (f"*** Begin Patch\n*** Add File: 명단.md\n+# 명단\n+학생A {r}\n*** End Patch\n", "deny"),
    (f"*** Begin Patch\n*** Update File: 명단.md\n@@\n-학생A {r}\n+학생A (번호 지움)\n*** End Patch\n", "clean"),
    ("*** Begin Patch\n*** Update File: 안내.md\n@@\n 안내\n+연락처 010-1234-5678\n*** End Patch\n", "warn"),
    ("*** Begin Patch\n*** Add File: 학습지.md\n+4학년 분수 학습지\n*** End Patch\n", "clean"),
]

failed = False
for name, cmd in CMDS.items():
    got = [run(cmd, patch, "write-codex") for patch, _ in codex_cases]
    want = [w for _, w in codex_cases]
    print(f"[{name}] Codex 쓰기 — {sum(g == w for g, w in zip(got, want))}/{len(want)} 맞음 {got}")
    failed = failed or got != want
    res = {"block": [run(cmd, t) for t in block], "warn": [run(cmd, t) for t in warn],
           "clean": [run(cmd, t) for t in clean]}
    ok = {k: sum(1 for r in v if r == k) for k, v in res.items()}
    writes = [run(cmd, t, "write") for t in block[:5]]
    print(f"[{name}] 입력 — 차단 {ok['block']}/{len(block)} · 경고 {ok['warn']}/{len(warn)} · 통과 {ok['clean']}/{len(clean)}"
          f" · 쓰기 확인 요청 {writes.count('ask')}/5")
    miss = [(t, r) for k, ts in (("block", block), ("warn", warn), ("clean", clean)) for t, r in zip(ts, res[k]) if r != k]
    for t, r in miss:
        print("  불일치:", r, "|", t)
    failed = failed or bool(miss) or writes.count("ask") != 5
for kind, t in bad_json:
    print("  출력 형식 문제:", kind, "|", t)
sys.exit(1 if failed or bad_json else 0)
