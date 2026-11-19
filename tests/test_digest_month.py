"""monthly-report·mtd-report digest.py 회귀 테스트 — 작은 month 응답(envelope)으로 소진율·광고비비중·신규 판정·
세부 단위 행 고르기를 확인한다. 기대값은 아래 행 값으로 손으로 계산했다(당월 2026-07, 전월 2026-06).

  매체 | 전월 (광고비, 노출, 클릭) | 당월            | 매체 월예산
  M1   | 1,000 / 100,000 / 1,000  | 900 / 90,000 / 450 | 1,000
  M2   | -                        | 100 / 10,000 / 50  | 없음
  브랜드 월예산 1,200 → 소진율 (900 + 100) / 1,200 = 83.3%
  광고비비중: M1 900 / 1,000 = 90.0%, M2 10.0%   M1 소진율 900 / 1,000 = 90.0%
  전체 CPC: 당월 1,000 / 500 = ₩2.0 (원자 합의 비율), 전월 1,000 / 1,000 = ₩1.0 → +100.0%
  전체 CTR: 당월 500 / 100,000 = 0.50%, 전월 1,000 / 100,000 = 1.00% → -0.50%p

  캠페인(모두 M1) — 상위 10개씩 고른다:
  c00~c09: 당월 광고비 200, 190, …, 110 (광고비 상위 10), 전월은 당월 - (1~10) → 변동 1~10
  c10    : 당월 50, 전월 1,040 → 변동 990 (변동 1위)
  c11, c12: 당월 = 전월 = 10, 20 → 변동 0
  광고비 상위 10 = c00~c09, 변동 상위 10 = c10 + c00~c09 중 9개 → 합집합 c00~c10 (11개), 나머지 2개 생략
"""
import importlib.util
import json
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "plugins", "laighthouse-analytics-prod", "skills")
KEYS = {"cost": "광고비", "impression": "노출", "click": "클릭"}
CUR, PREV = "2026-07", "2026-06"

MEDIA = [("M1", PREV, 1000, 100000, 1000), ("M1", CUR, 900, 90000, 450), ("M2", CUR, 100, 10000, 50)]
CAMPAIGNS = ([(f"c{i:02d}", 200 - 10 * i, 200 - 10 * i - (i + 1)) for i in range(10)]
             + [("c10", 50, 1040), ("c11", 10, 10), ("c12", 20, 20)])


def load(skill):
    spec = importlib.util.spec_from_file_location(f"{skill}_digest", os.path.join(SKILLS, skill, "assets", "digest.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def envelope(dims, rows):
    return {"dimensions": ["month"] + dims, "metrics": ["광고비", "노출", "클릭"], "metric_units": {}, "rows": rows}


class MonthDigestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        media = envelope(["media"], [{"month": m, "media": n, "광고비": c, "노출": i, "클릭": k} for n, m, c, i, k in MEDIA])
        camp_rows = []
        for name, cur, prev in CAMPAIGNS:
            camp_rows.append({"month": CUR, "media": "M1", "campaign_name": name, "광고비": cur, "노출": 1000, "클릭": 10})
            camp_rows.append({"month": PREV, "media": "M1", "campaign_name": name, "광고비": prev, "노출": 1000, "클릭": 10})
        camp = envelope(["media", "campaign_name"], camp_rows)
        paths = []
        for n, env in (("six.json", media), ("level2.json", camp)):
            paths.append(os.path.join(d, n))
            with open(paths[-1], "w", encoding="utf-8") as f:
                json.dump(env, f, ensure_ascii=False)
        self.base = os.path.join(d, "base.json")
        with open(self.base, "w", encoding="utf-8") as f:
            json.dump({"target_date": "2026-07-20", "metric_keys": KEYS, "currency": "₩",
                       "summary_input": {"levels": paths, "periods": {"cur": CUR, "base": PREV},
                                         "budget": {"cost": 1200}, "media_budget": {"M1": {"cost": 1000}}}},
                      f, ensure_ascii=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_budget_and_media_share(self):
        g = load("monthly-report").build(self.base)
        self.assertEqual(g["예산"], {"월예산": "₩1,200", "소진율": "83.3%"})
        m = {r["이름"]: r for r in g["매체"]}
        self.assertEqual([r["이름"] for r in g["매체"]], ["M1", "M2"])   # 당월 광고비 순
        self.assertEqual((m["M1"]["광고비비중"], m["M1"]["월예산"], m["M1"]["소진율"]), ("90.0%", "₩1,000", "90.0%"))
        self.assertEqual(m["M2"]["광고비비중"], "10.0%")
        self.assertNotIn("소진율", m["M2"])                              # 매체 예산이 없으면 키가 없다

    def test_new_media_is_marked_new(self):
        m2 = next(r for r in load("monthly-report").build(self.base)["매체"] if r["이름"] == "M2")
        self.assertEqual(m2["전월"]["광고비"], "-")
        self.assertEqual(m2["전월 대비"]["광고비"], "신규")

    def test_ratios_come_from_atom_sums(self):
        t = load("monthly-report").build(self.base)["전체"]
        self.assertEqual((t["당월"]["CPC"], t["전월"]["CPC"], t["전월 대비"]["CPC"]), ("₩2.0", "₩1.0", "+100.0%"))
        self.assertEqual((t["당월"]["CTR"], t["전월 대비"]["CTR"]), ("0.50%", "-0.50%p"))
        self.assertNotIn("CPV", t["당월"])                               # 조회수 지표가 없으면 CPV를 만들지 않는다

    def test_top_rows_cost_plus_movers(self):
        g = load("monthly-report").build(self.base)
        names = [r["이름"] for r in g["매체-캠페인"]]
        self.assertEqual(names, [f"M1 / c{i:02d}" for i in range(10)] + ["M1 / c10"])
        self.assertIn("나머지 2개", g["매체-캠페인 생략"])
        c10 = g["매체-캠페인"][-1]
        self.assertEqual((c10["당월"]["광고비"], c10["전월"]["광고비"], c10["전월 대비"]["광고비"]), ("₩50.0", "₩1,040", "-95.2%"))

    def test_mtd_labels_and_month_progress(self):
        g = load("mtd-report").build(self.base)
        self.assertEqual(g["기간"], {"당월": "2026-07-01~2026-07-20", "전월 동기": "2026-06-01~2026-06-20"})
        self.assertIn("전월 동기 대비", g["전체"])
        self.assertEqual(g["예산"]["월 진행률"], "64.5%")                 # 20 / 31


if __name__ == "__main__":
    unittest.main()
