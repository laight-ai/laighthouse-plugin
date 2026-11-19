"""계층 표(report_kit.build_tree)의 비율 폴백 — 하위 레벨을 기본 지표만 받았을 때 ROAS·CTR·CPC를 채우는 규칙."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "plugins", "laighthouse-analytics-prod", "shared", "assets"))
import report_kit as kit  # noqa: E402

KEYS = {"cost": "광고비", "impression": "노출", "click": "클릭", "revenue": "매출"}
CUR = "2026-11"


def env(dims, rows, metrics):
    return {"dimensions": ["month"] + dims, "metrics": metrics, "metric_units": {},
            "rows": [dict(month=CUR, **r) for r in rows]}


def tree(media_row, campaign_row, ratio_metrics):
    base = ["광고비", "노출", "클릭", "매출"]
    media = env(["media"], [dict(media="M", **media_row)], base + ratio_metrics)
    camp = env(["media", "campaign_name"], [dict(media="M", campaign_name="C", **campaign_row)], base)
    t = kit.build_tree([media, camp], "2026-10", CUR, KEYS)
    keys = [m["key"] for m in t["metrics"]]
    campaign = t["nodes"][0][3][0]
    return {k: campaign[1][i] for i, k in enumerate(keys)}


class DeriveRatiosTest(unittest.TestCase):
    def test_percent_scale_learned_from_media_row(self):
        # 매체 행: 서버 roas 400(%) = 매출 2,000 / 광고비 500 × 100 → 캠페인 행도 % 배율로 채운다
        c = tree({"광고비": 500, "노출": 1000, "클릭": 50, "매출": 2000, "roas": 400.0, "ctr": 5.0, "cpc": 10.0},
                 {"광고비": 200, "노출": 400, "클릭": 10, "매출": 300}, ["roas", "ctr", "cpc"])
        self.assertAlmostEqual(c["roas"], 150.0)   # 300 / 200 × 100
        self.assertAlmostEqual(c["ctr"], 2.5)      # 10 / 400 × 100
        self.assertAlmostEqual(c["cpc"], 20.0)     # 200 / 10 (배수)

    def test_multiple_scale_brand(self):
        # roas를 배수(4.0)로 내는 브랜드는 배수로 채운다 — %로 채우면 100배로 틀린다
        c = tree({"광고비": 500, "노출": 1, "클릭": 1, "매출": 2000, "roas": 4.0},
                 {"광고비": 200, "노출": 1, "클릭": 1, "매출": 300}, ["roas"])
        self.assertAlmostEqual(c["roas"], 1.5)

    def test_server_value_is_kept(self):
        base = ["광고비", "노출", "클릭", "매출", "roas"]
        media = env(["media"], [{"media": "M", "광고비": 500, "노출": 1, "클릭": 1, "매출": 2000, "roas": 400.0}], base)
        camp = env(["media", "campaign_name"],
                   [{"media": "M", "campaign_name": "C", "광고비": 200, "노출": 1, "클릭": 1, "매출": 300, "roas": 123.0}], base)
        t = kit.build_tree([media, camp], "2026-10", CUR, KEYS)
        i = [m["key"] for m in t["metrics"]].index("roas")
        self.assertEqual(t["nodes"][0][3][0][1][i], 123.0)

    def test_no_reference_value_means_no_fill(self):
        # 서버 roas 값이 0뿐이면 배율을 알 수 없어 채우지 않는다
        c = tree({"광고비": 500, "노출": 1, "클릭": 1, "매출": 0, "roas": 0},
                 {"광고비": 200, "노출": 1, "클릭": 1, "매출": 300}, ["roas"])
        self.assertIsNone(c["roas"])

    def test_zero_denominator_is_left_empty(self):
        c = tree({"광고비": 500, "노출": 1, "클릭": 1, "매출": 2000, "roas": 400.0},
                 {"광고비": 0, "노출": 1, "클릭": 1, "매출": 300}, ["roas"])
        self.assertIsNone(c["roas"])


if __name__ == "__main__":
    unittest.main()
