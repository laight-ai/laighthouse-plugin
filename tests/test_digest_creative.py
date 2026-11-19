"""creative-report 소재 Summary 근거(digest.build) — 노션 "소재 Summary" 가이드가 쓰는 판정(광고비 비중·신규/중단·
최소 표본을 채운 소재끼리의 우수/저조·앞뒤 절반 일별 추이)을 손으로 계산한 값과 비교한다."""
import json
import os
import tempfile
import unittest

import importlib.util

_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "plugins", "laighthouse-analytics-prod", "skills", "creative-report", "assets", "digest.py")
_spec = importlib.util.spec_from_file_location("creative_digest", _PATH)
digest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(digest)

KEYS = {"cost": "광고비", "impression": "노출", "click": "클릭", "revenue": "매출"}
DATES = ["2026-07-%02d" % d for d in range(14, 21)]


def ad(name, cost, imp, click, rev):
    return {"media": "M", "campaign_name": "C", "ad_group_name": "G", "ad_name": name,
            "광고비": cost, "노출": imp, "클릭": click, "매출": rev}


# 이번 기간 광고비 합 10,000 → 최소 표본: 노출 1,000 이상·광고비 100 이상 → A·B·C (D는 노출 500이라 제외)
CUR_ROWS = [ad("A", 6000, 10000, 100, 30000),   # ROAS 500%, CPC 60
            ad("B", 3000, 5000, 100, 3000),     # ROAS 100%, CPC 30 — 직전 기간에 없음(신규 집행)
            ad("C", 950, 50000, 10, 0),         # ROAS 0%,  CPC 95
            ad("D", 50, 500, 1, 5000)]          # ROAS 10000% — 표본 미달이라 우수에 나오면 안 된다
PREV_ROWS = [ad("A", 4000, 8000, 80, 8000),
             ad("C", 1000, 40000, 10, 0),
             ad("E", 2000, 3000, 30, 1000)]      # 이번 기간에 없음(집행 중단)
DAY_COSTS = [100, 100, 100, 200, 200, 200, 0]   # 앞 3일 평균 100, 뒤 4일 평균 150


class CreativeDigestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, obj):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        return path

    def build(self, with_prev=True, with_day=True, cur_rows=CUR_ROWS, prev_rows=PREV_ROWS):
        base = {"metric_keys": KEYS, "currency": "₩", "chosen_media": "M",
                "period": "2026-07-14~2026-07-20", "prev_period": "2026-07-07~2026-07-13",
                "tot_file": self.write("tot.json", {"rows": cur_rows})}
        if with_day:
            base["media_day_file"] = self.write("day.json", {"rows": [{"date": d, "media": "M", "광고비": c}
                                                                      for d, c in zip(DATES, DAY_COSTS)]})
        if with_prev:
            base["prev_file"] = self.write("prev.json", {"rows": prev_rows})
        return digest.build(self.write("base.json", base))

    def test_total_and_change_vs_previous_period(self):
        d = self.build()
        self.assertEqual(d["전체"]["광고비"], "₩10,000")
        self.assertEqual(d["전체"]["직전 대비"]["광고비"], "+42.9%")   # 10,000 vs 7,000
        self.assertNotIn("전환", d["전체"])                            # 전환 지표가 없는 브랜드

    def test_top_creatives_share_and_new(self):
        top = self.build()["매체"][0]["광고비 상위 소재"]
        self.assertEqual([t["소재"] for t in top[:2]], ["M / A", "M / B"])
        self.assertEqual(top[0]["광고비 비중"], "60.0%")
        self.assertEqual(top[0]["직전 대비"]["광고비"], "+50.0%")      # 6,000 vs 4,000
        self.assertEqual(top[1]["직전 대비"], "신규 집행")

    def test_best_worst_only_among_min_sample(self):
        m = self.build()["매체"][0]
        self.assertEqual(m["ROAS 우수"], [{"소재": "M / A", "ROAS": "500.0%", "광고비": "₩6,000"}])
        self.assertEqual(m["ROAS 저조"][0]["소재"], "M / C")
        self.assertEqual(m["CPC 우수"][0], {"소재": "M / B", "CPC": "₩30.0", "광고비": "₩3,000"})
        # ↑ 원화 100 미만은 소수 1자리(agency creative_common.money와 같은 표기 규칙)
        self.assertEqual(m["CPC 저조"][0]["소재"], "M / C")
        self.assertIn("소재 3개", m["최소 표본"])

    def test_spend_movers_include_new_and_stopped(self):
        moves = {x["소재"]: x for x in self.build()["광고비 변동 상위 소재"]}
        self.assertEqual(moves["M / B"]["변화"], "신규 집행")
        self.assertEqual(moves["M / E"]["변화"], "집행 중단")
        self.assertEqual(moves["M / E"]["광고비"], "₩2,000 → ₩0")
        self.assertEqual(moves["M / A"]["변화"], "+50.0%")

    def test_daily_trend_front_back_halves(self):
        t = self.build()["일별 추이"]
        self.assertEqual(t["앞 절반 일평균 광고비"], "₩100")
        self.assertEqual(t["뒤 절반 일평균 광고비"], "₩150")
        self.assertEqual(t["변화"], "+50.0%")
        self.assertEqual(t["가장 많이 쓴 날"], "2026-07-17 (₩200)")
        self.assertEqual(t["집행일 수"], "6일 / 7일")

    def test_no_daily_trend_without_media_day_response(self):
        # 매체 일별 응답이 없으면(에러·예전 흐름) 추이를 0원·0일 집행으로 지어내지 않고 키를 뺀다
        self.assertNotIn("일별 추이", self.build(with_day=False))

    def test_ctr_change_uses_two_decimals(self):
        # CTR 0.41% → 0.45%는 +0.04%p — 소수 1자리로 찍으면 +0.0%p가 된다
        d = self.build(cur_rows=[ad("A", 1000, 10000, 45, 0)], prev_rows=[ad("A", 1000, 10000, 41, 0)])
        self.assertEqual(d["전체"]["직전 대비"]["CTR"], "+0.04%p")

    def test_without_previous_period_skips_comparison(self):
        d = self.build(with_prev=False)
        self.assertEqual(d["직전 기간"], "없음(비교하지 않는다)")
        self.assertNotIn("직전 대비", d["전체"])
        self.assertNotIn("직전 대비", d["매체"][0]["광고비 상위 소재"][0])
        self.assertNotIn("광고비 변동 상위 소재", d)


if __name__ == "__main__":
    unittest.main()
