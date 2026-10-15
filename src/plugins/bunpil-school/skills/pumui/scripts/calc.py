#!/usr/bin/env python3
"""품의 산출내역 계산기 (표준 라이브러리만 사용).

사용법:
    python3 calc.py items.csv [--budget 500000] [--asset-threshold <학교 기준 금액>]
    (옵션 값은 예시다. --asset-threshold는 학교 기준 금액을 확인한 뒤 지정한다.)

입력 CSV 열: 품명,규격,단가,수량[,배송비]   (첫 줄은 머리글)
  - 숫자에 쉼표·'원'이 있어도 된다. UTF-8(BOM 포함) 또는 CP949.
  - 단가나 수량이 비었거나 숫자가 아니면 그 줄은 합계에서 빼고 '확인 필요'로 표시하고, 종료 코드 1로 끝난다(의도된 동작, 오류 아님).

출력: 산출내역 줄 `품명 규격 @단가 × 수량 = 금액`, 소계, 배송비, 합계,
      예산 대조(--budget), 자산/소모품 구분 확인 대상(--asset-threshold).
"""
import argparse
import csv
import re
import sys


def read_text(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise SystemExit("파일 인코딩을 읽을 수 없다. UTF-8 CSV로 저장해 다시 시도하라.")


def to_int(value):
    """'15,000원' -> 15000. 비었거나 숫자가 아니면 None."""
    if value is None:
        return None
    s = re.sub(r"[,\s원]", "", str(value))
    if s == "":
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    if f < 0 or f != int(f):
        return None
    return int(f)


def won(n):
    return f"{n:,}원"


def main(argv=None):
    ap = argparse.ArgumentParser(description="품의 산출내역 계산기")
    ap.add_argument("csv_path")
    ap.add_argument("--budget", type=int, help="배정 예산(원)")
    ap.add_argument("--asset-threshold", type=int,
                    help="이 금액 이상 단가 품목을 자산/소모품 구분 확인 대상으로 표시(학교 기준 확인 필요)")
    args = ap.parse_args(argv)

    rows = list(csv.DictReader(read_text(args.csv_path).splitlines()))
    need = {"품명", "규격", "단가", "수량"}
    if not rows or not need.issubset(rows[0].keys()):
        raise SystemExit("머리글이 '품명,규격,단가,수량[,배송비]'이어야 한다.")

    lines, problems, flags = [], [], []
    subtotal = shipping = 0
    for i, r in enumerate(rows, start=2):  # 머리글이 1행
        name = (r.get("품명") or "").strip()
        spec = (r.get("규격") or "").strip()
        if not name:
            continue
        label = f"{name} {spec}".strip()
        price, qty = to_int(r.get("단가")), to_int(r.get("수량"))
        ship = to_int(r.get("배송비")) or 0
        if price is None or qty is None:
            miss = "단가" if price is None else "수량"
            problems.append(f"{i}행 {label}: {miss} 누락 또는 숫자 아님 → 합계에서 제외, 확인 필요")
            lines.append(f"{label} @? × ? = 확인 필요")
            continue
        amount = price * qty
        subtotal += amount
        shipping += ship
        lines.append(f"{label} @{won(price)} × {qty} = {won(amount)}")
        if args.asset_threshold and price >= args.asset_threshold:
            flags.append(f"{label}: 단가 {won(price)} → 자산/소모품 구분 확인")

    total = subtotal + shipping
    print("[산출내역 (초안)]")
    for n, line in enumerate(lines, 1):
        print(f"{n}. {line}")
    print()
    print(f"소계: {won(subtotal)}")
    print(f"배송비: {won(shipping)}")
    print(f"합계: {won(total)}")
    if args.budget is not None:
        diff = args.budget - total
        if diff >= 0:
            print(f"예산 대조: 예산 {won(args.budget)} - 합계 {won(total)} = 잔액 {won(diff)} (예산 범위 이내)")
        else:
            print(f"예산 대조: 예산 {won(args.budget)} - 합계 {won(total)} = 초과 {won(-diff)} (예산 초과, 품목 조정 필요)")
    if flags:
        print("\n[자산/소모품 구분 확인 대상]")
        for f in flags:
            print(f"- {f}")
    if problems:
        print("\n[확인 필요]")
        for p in problems:
            print(f"- {p}")
        print("※ 위 품목은 합계에 포함되지 않았다.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
