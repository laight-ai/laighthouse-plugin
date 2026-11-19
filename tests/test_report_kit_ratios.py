"""계층 표 비율 폴백(report_kit._derive_ratios) — 하위 레벨을 기본 지표만 받았을 때 ROAS·CTR·CPC를 채우는 규칙."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "plugins", "laighthouse-analytics-prod", "shared", "assets"))
import report_kit as kit  # noqa: E402

KEYS = {"cost": "광고비", "impression": "노출", "click": "클릭", "revenue": "매출"}
METRICS = ["광고비", "노출", "클릭", "매출", "roas", "ctr", "cpc"]


def slot(**v):
    return {"cur": dict(v), "base": {}}


class DeriveRatiosTest(unittest.TestCase):
    def test_percent_scale_learned_from_server_rows(self):
        # 매체 행: 서버 roas 400(%) = 매출 2,000 / 광고비 500 × 100 → 캠페인 행도 % 배율로 채운다
        values = {("M",): slot(광고비=500, 노출=1000, 클릭=50, 매출=2000, roas=400.0, ctr=5.0, cpc=10.0),
                  ("M", "C"): slot(광고비=200, 노출=400, 클릭=10, 매출=300)}
        kit._derive_ratios(values, METRICS, KEYS)
        c = values[("M", "C")]["cur"]
        self.assertAlmostEqual(c["roas"], 150.0)   # 300 / 200 × 100
        self.assertAlmostEqual(c["ctr"], 2.5)      # 10 / 400 × 100
        self.assertAlmostEqual(c["cpc"], 20.0)     # 200 / 10 (배수)

    def test_multiple_scale_brand(self):
        # roas를 배수(4.0)로 내는 브랜드는 배수로 채운다 — %로 채우면 100배로 틀린다
        values = {("M",): slot(광고비=500, 매출=2000, roas=4.0),
                  ("M", "C"): slot(광고비=200, 매출=300)}
        kit._derive_ratios(values, ["광고비", "매출", "roas"], KEYS)
        self.assertAlmostEqual(values[("M", "C")]["cur"]["roas"], 1.5)

    def test_server_values_are_kept(self):
        values = {("M",): slot(광고비=500, 매출=2000, roas=400.0),
                  ("M", "C"): slot(광고비=200, 매출=300, roas=123.0)}
        kit._derive_ratios(values, ["광고비", "매출", "roas"], KEYS)
        self.assertEqual(values[("M", "C")]["cur"]["roas"], 123.0)

    def test_no_reference_row_means_no_fill(self):
        # 서버 값이 어디에도 없으면 배율을 모르므로 채우지 않는다
        values = {("M", "C"): slot(광고비=200, 매출=300)}
        kit._derive_ratios(values, ["광고비", "매출", "roas"], KEYS)
        self.assertNotIn("roas", values[("M", "C")]["cur"])

    def test_zero_denominator_is_left_empty(self):
        values = {("M",): slot(광고비=500, 매출=2000, roas=400.0),
                  ("M", "C"): slot(광고비=0, 매출=300)}
        kit._derive_ratios(values, ["광고비", "매출", "roas"], KEYS)
        self.assertNotIn("roas", values[("M", "C")]["cur"])


if __name__ == "__main__":
    unittest.main()
