"""daily-report digest.py 회귀 테스트 — 작은 day 응답(envelope)으로 급변 구분과 세부 단위 행 고르기를 확인한다.

기대값은 아래 행 값으로 손으로 계산했다(기준일 D0 = 07-20, 전일 D1 = 07-19, 모두 매체 M1).

  캠페인 | D1 광고비 | D0 광고비 | 구분
  A      | 1,000     | 1,100     | 없음 (+10%, CPM +10%, CTR 그대로)
  B      | -         | 500       | 신규 집행
  C      | 800       | -         | 집행 중단
  D      | 100       | 200       | 광고비 급등 (+100%)
  E      | 2,000     | 1,000     | 광고비 급락 (-50%)
  F      | 300       | 300       | 효율 급변 (클릭 10 → 20, CTR 1% → 2%: +100%)
  G      | 50        | 50        | 없음
"""
import importlib.util
import json
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIGEST = os.path.join(ROOT, "plugins", "laighthouse-analytics-prod", "skills", "daily-report", "assets", "digest.py")
D0, D1 = "2026-07-20", "2026-07-19"
KEYS = {"cost": "광고비", "impression": "노출", "click": "클릭"}

# 캠페인: (이름, D1 (광고비, 노출, 클릭) 또는 None, D0 ... 또는 None)
CAMPAIGNS = [
    ("A", (1000, 10000, 100), (1100, 10000, 100)),
    ("B", None, (500, 5000, 50)),
    ("C", (800, 8000, 80), None),
    ("D", (100, 1000, 10), (200, 2000, 20)),
    ("E", (2000, 20000, 200), (1000, 10000, 100)),
    ("F", (300, 1000, 10), (300, 1000, 20)),
    ("G", (50, 500, 5), (50, 500, 5)),
]


def load_digest():
    spec = importlib.util.spec_from_file_location("daily_digest", DIGEST)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def metric_row(dims, day, vals):
    cost, imp, click = vals
    return {**dims, "date": day, "광고비": cost, "노출": imp, "클릭": click}


def envelope(dims, rows):
    return {"source": "elt", "time_grain": "day", "dimensions": dims + ["date"],
            "metrics": ["광고비", "노출", "클릭"], "rows": rows}


class DailyDigest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.digest = load_digest()
        media_rows = [metric_row({"media": "M1"}, D1, (2000, 10000, 100)),
                      metric_row({"media": "M1"}, D0, (3000, 20000, 300)),
                      metric_row({"media": None}, D0, (999, 999, 999))]   # Organic — 빠져야 한다
        camp_rows = []
        for name, v1, v0 in CAMPAIGNS:
            for day, v in ((D1, v1), (D0, v0)):
                if v:
                    camp_rows.append(metric_row({"media": "M1", "campaign_name": name}, day, v))
        paths = [self.write("media.json", envelope(["media"], media_rows)),
                 self.write("camp.json", envelope(["media", "campaign_name"], camp_rows))]
        self.base = self.write("base.json", {"summary_input": {"levels": paths, "periods": {"cur": D0, "base": D1}},
                                             "metric_keys": KEYS, "currency": "₩"})

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, obj):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        return path

    def build(self, top):
        self.digest.LEVELS = (("매체-캠페인", ["media", "campaign_name"], top),)
        return self.digest.build(self.base)

    def test_total_excludes_organic_and_formats_change(self):
        total = self.build(10)["전체"]
        self.assertEqual(total["기준일"]["광고비"], "₩3,000")
        self.assertEqual(total["전일"]["광고비"], "₩2,000")
        self.assertEqual(total["전일 대비"]["광고비"], "+50.0%")
        self.assertEqual(total["전일 대비"]["CTR"], "+0.50%p")      # 1.50% - 1.00%
        self.assertEqual(total["기준일"]["CPM"], "₩150")             # 3,000 / 20,000 × 1,000
        self.assertEqual(total["전일 대비"]["CPM"], "-25.0%")         # 150 vs 200

    def test_classifies_new_stopped_and_spikes(self):
        rows = {r["이름"]: r for r in self.build(10)["매체-캠페인"]}
        kinds = {name.split(" / ")[1]: r.get("구분") for name, r in rows.items()}
        self.assertEqual(kinds, {"A": None, "B": "신규 집행", "C": "집행 중단", "D": "광고비 급등",
                                 "E": "광고비 급락", "F": "효율 급변", "G": None})
        self.assertEqual(rows["M1 / B"]["전일"], "-")
        self.assertEqual(rows["M1 / C"]["기준일"], "-")
        self.assertEqual(rows["M1 / F"]["전일 대비"]["CTR"], "+1.00%p")

    def test_picks_top_cost_and_top_move(self):
        out = self.build(2)
        # 기준일 광고비 상위 2: A(1,100)·E(1,000) / 광고비 변동 상위 2: E(1,000)·C(800) → 합쳐 기준일 광고비 순
        self.assertEqual([r["이름"] for r in out["매체-캠페인"]], ["M1 / A", "M1 / E", "M1 / C"])
        self.assertIn("나머지 4개", out["매체-캠페인 생략"])


if __name__ == "__main__":
    unittest.main()
