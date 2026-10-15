#!/usr/bin/env python3
"""calc.py 간단 시험. 실행: python3 test_calc.py"""
import contextlib
import io
import os
import tempfile
import unittest

import calc


def run(text, *extra, encoding="utf-8-sig"):
    with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as f:
        f.write(text.encode(encoding))
        path = f.name
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            code = calc.main([path, *extra])
    finally:
        os.unlink(path)
    return code, out.getvalue()


class CalcTest(unittest.TestCase):
    def test_basic_total_and_budget(self):
        code, out = run("품명,규격,단가,수량,배송비\n공책,A4,\"1,500원\",10,2500\n펜,0.5mm,800,20,\n", "--budget", "40000")
        self.assertEqual(code, 0)
        self.assertIn("공책 A4 @1,500원 × 10 = 15,000원", out)
        self.assertIn("펜 0.5mm @800원 × 20 = 16,000원", out)
        self.assertIn("합계: 33,500원", out)
        self.assertIn("잔액 6,500원", out)

    def test_over_budget(self):
        code, out = run("품명,규격,단가,수량\n의자,일반,50000,3\n", "--budget", "100000")
        self.assertIn("초과 50,000원", out)

    def test_missing_price_excluded(self):
        code, out = run("품명,규격,단가,수량\n의자,일반,,3\n책상,일반,10000,1\n")
        self.assertEqual(code, 1)
        self.assertIn("합계: 10,000원", out)
        self.assertIn("확인 필요", out)

    def test_cp949(self):
        code, out = run("품명,규격,단가,수량\n공책,A4,1000,2\n", encoding="cp949")
        self.assertIn("= 2,000원", out)

    def test_asset_flag(self):
        code, out = run("품명,규격,단가,수량\n노트북,x,900000,1\n", "--asset-threshold", "300000")
        self.assertIn("자산/소모품 구분 확인", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
