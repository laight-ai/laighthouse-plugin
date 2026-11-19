"""prepare.py 라운드 흐름 회귀 테스트 — 저장 훅이 남긴 응답 폴더를 임시로 만들어 실제 prepare.py를 돌린다.

- 훅 판별: 오래된 응답만 있으면 note(폴백)로 가되, 지표 키를 묻는 중(ask_user)이면 note로 덮지 않는다.
- creative 전체 일별: 라운드 A의 매체 일별에서만 만들고, 상위 소재만 받은 라운드 C로 대신하지 않는다.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "plugins", "laighthouse-analytics-prod", "skills")
BRAND = "테스트브랜드"
T = "2026-11-18"
DAYS = [f"2026-11-{d}" for d in range(12, 19)]
METRICS = ["광고비", "노출", "클릭", "매출"]


def envelope(grain, dims, rows, metrics=METRICS):
    return json.dumps({"source": "elt", "tenant": BRAND, "time_grain": grain, "dimensions": dims,
                       "metrics": metrics, "metric_units": {}, "row_count": len(rows), "rows": rows},
                      ensure_ascii=False)


class PrepareRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = os.path.join(self.tmp.name, "laighthouse_mcp_responses", "session1")
        os.makedirs(self.folder)
        self.n = 0

    def tearDown(self):
        self.tmp.cleanup()

    def save(self, tool, tool_input, response, age_secs=0):
        self.n += 1
        rec = {"tool_name": f"mcp__laighthouse__{tool}", "tool_input": dict(brand_name=BRAND, **tool_input),
               "saved_at": time.time() - age_secs, "response": response}
        with open(os.path.join(self.folder, f"{self.n:03d}.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False)

    def perf(self, start, end, grain, group_by, rows, filters=None, metrics=METRICS, age_secs=0, day_offset=None):
        ti = {"start_date": start, "end_date": end, "time_grain": grain, "group_by": group_by}
        if day_offset is not None:
            ti["day_offset"] = day_offset
        if filters:
            ti["filters"] = filters
        dims = (["date"] if grain == "day" else []) + group_by
        self.save("get_ad_performance", ti, envelope(grain, dims, rows, metrics), age_secs)

    def run_prepare(self, skill, *args):
        env = dict(os.environ, TMP=self.tmp.name, TEMP=self.tmp.name, TMPDIR=self.tmp.name, PYTHONIOENCODING="utf-8")
        env.pop("LAIGHTHOUSE_PREPARE_FRESH_SECS", None)
        r = subprocess.run([sys.executable, os.path.join(SKILLS, skill, "assets", "prepare.py"),
                            "--brand", BRAND, "--target-date", T, *args],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)


class HookDetectionTest(PrepareRun):
    """daily-report 라운드 A 응답으로 저장 훅이 지금 동작하는지 판별한다."""

    UNKNOWN = ["spend_x", "imps_x", "taps_x"]   # 광고비·노출·클릭 역할을 정할 수 없는 지표 이름
    ANSWER = '{"cost": "spend_x", "impression": "imps_x", "click": "taps_x"}'

    def save_round_a(self, metrics, age_secs):
        media_row = {"media": "M", **{m: 100 for m in metrics}}
        self.perf("2026-11-01", T, "month", ["media"], [dict(media_row, month="2026-11")], metrics=metrics, age_secs=age_secs)
        self.perf("2026-11-12", T, "day", ["media"], [dict(media_row, date=d) for d in DAYS], metrics=metrics, age_secs=age_secs)
        self.perf("2026-11-12", T, "total", ["media"], [media_row], metrics=metrics, age_secs=age_secs)

    def age_saved_responses(self, secs):
        for name in os.listdir(self.folder):
            path = os.path.join(self.folder, name)
            with open(path, encoding="utf-8") as f:
                rec = json.load(f)
            rec["saved_at"] -= secs
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False)

    def test_stale_responses_mean_no_hook(self):
        # 예전 세션 응답만 남아 있다 → 큰 호출을 보내지 말라는 note
        self.save_round_a(METRICS, age_secs=3600)
        out = self.run_prepare("daily-report")
        self.assertIn("note", out)
        self.assertNotIn("missing", out)

    def test_late_answer_to_metric_key_question_still_asks_for_round_b(self):
        # 방금 받은 라운드 A로 지표 키를 묻고 → 한 시간 뒤 답해 --metric-keys로 다시 돌려도 라운드 B를 요청한다
        self.save_round_a(self.UNKNOWN, age_secs=0)
        asked = self.run_prepare("daily-report")
        self.assertIn("ask_user", asked)
        self.age_saved_responses(3600)
        out = self.run_prepare("daily-report", "--metric-keys", self.ANSWER)
        self.assertNotIn("note", out)
        self.assertIn(["media", "campaign_name"], [m.get("group_by") for m in out["missing"]])

    def test_stale_responses_with_metric_keys_but_no_question_mean_no_hook(self):
        # 이 보고서에서 질문을 낸 적이 없는데 --metric-keys만 넘어오고 응답은 예전 것뿐 → 훅 있음으로 보지 않는다
        self.save_round_a(self.UNKNOWN, age_secs=3600)
        out = self.run_prepare("daily-report", "--metric-keys", self.ANSWER)
        self.assertIn("note", out)

    def test_stale_responses_do_not_raise_a_question(self):
        # 예전 응답만으로는 지표 키를 묻지 않고 폴백 절차로 보낸다
        self.save_round_a(self.UNKNOWN, age_secs=3600)
        out = self.run_prepare("daily-report")
        self.assertIn("note", out)
        self.assertNotIn("ask_user", out)


class CurrentRunOnlyTest(PrepareRun):
    """같은 인자의 예전 계층 응답(몇 시간 전)이 남아 있어도, 라운드 A를 새로 보낸 실행에서는 다시 요청한다."""

    LEVELS = (["media", "campaign_name"], ["media", "campaign_name", "ad_group_name"],
              ["media", "campaign_name", "ad_group_name", "ad_name"])

    def save_round_a(self, age_secs):
        row = {"media": "M", "광고비": 100, "노출": 1000, "클릭": 10, "매출": 500}
        self.perf("2026-11-01", T, "month", ["media"], [dict(row, month="2026-11")], age_secs=age_secs)
        self.perf("2026-11-12", T, "day", ["media"], [dict(row, date=d) for d in DAYS], age_secs=age_secs)
        self.perf("2026-11-12", T, "total", ["media"], [row], age_secs=age_secs)
        self.save("get_target_progress_v2", {"month": "2026-11", "as_of_date": T},
                  "No all budget/target available for 2026-11.", age_secs)
        self.save("list_promotions", {"start_date": "2026-11-11", "end_date": T}, "[]", age_secs)

    def save_round_b(self, age_secs):
        for dims in self.LEVELS:
            row = {"media": "M", "campaign_name": "C", "ad_group_name": "G", "ad_name": "A",
                   "광고비": 50, "노출": 500, "클릭": 5, "매출": 250}
            self.perf("2026-11-17", T, "day", dims,
                      [dict({k: row[k] for k in dims}, date=d, 광고비=50, 노출=500, 클릭=5, 매출=250)
                       for d in ("2026-11-17", T)], age_secs=age_secs)

    def test_old_round_b_is_requested_again(self):
        self.save_round_a(age_secs=5 * 3600)
        self.save_round_b(age_secs=5 * 3600)
        self.save_round_a(age_secs=0)       # 이번 실행
        out = self.run_prepare("daily-report")
        self.assertEqual([m["group_by"] for m in out["missing"]], [list(d) for d in self.LEVELS])

    def test_round_b_of_this_run_is_used(self):
        self.save_round_a(age_secs=0)
        self.save_round_b(age_secs=0)
        out = self.run_prepare("daily-report")
        self.assertEqual(out["missing"], [])
        self.assertIn("campaigns_top_by_cost", out["facts"])


class MonthlyPeriodTest(PrepareRun):
    """monthly-report는 지난 달을 말일까지 본다(day_offset 31) — 기준일의 일로 자르면 30일 기준일 때 31일이 빠진다."""

    def test_mid_month_requests_full_previous_months(self):
        out = self.run_prepare_at("monthly-report", "2026-11-30")
        six = [m for m in out["missing"] if m.get("group_by") == ["media"]]
        self.assertEqual(six[0].get("day_offset"), 31)

    def test_previous_month_period_runs_to_month_end(self):
        row = {"media": "M", "광고비": 100, "노출": 1000, "클릭": 10, "매출": 500}
        self.perf("2026-06-01", "2026-11-30", "month", ["media"],
                  [dict(row, month=f"2026-{m:02d}") for m in range(6, 12)], day_offset=31)
        out = self.run_prepare_at("monthly-report", "2026-11-30")
        self.assertEqual(out["facts"]["period"]["prev_month"], "2026-10-01~2026-10-31")

    def run_prepare_at(self, skill, t):
        env = dict(os.environ, TMP=self.tmp.name, TEMP=self.tmp.name, TMPDIR=self.tmp.name, PYTHONIOENCODING="utf-8")
        self.save("list_promotions", {"start_date": "2000-01-01", "end_date": "2000-01-01"}, "[]")   # 훅 동작 표시
        r = subprocess.run([sys.executable, os.path.join(SKILLS, skill, "assets", "prepare.py"),
                            "--brand", BRAND, "--target-date", t], capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)


class CreativeOverallSourceTest(PrepareRun):
    """매체 M의 전체 일별 CTR은 10%(클릭 100 / 노출 1,000), 상위 소재 A만 보면 50%(50 / 100)."""

    def save_rounds(self, with_media_day):
        dims4 = ["media", "campaign_name", "ad_group_name", "ad_name"]
        self.perf("2026-11-12", T, "total", ["media"],
                  [{"media": "M", "광고비": 700, "노출": 7000, "클릭": 700, "매출": 3500}])
        if with_media_day:
            self.perf("2026-11-12", T, "day", ["media"],
                      [{"date": d, "media": "M", "광고비": 100, "노출": 1000, "클릭": 100, "매출": 500} for d in DAYS])
        ad = {"media": "M", "campaign_name": "C", "ad_group_name": "G"}
        self.perf("2026-11-12", T, "total", dims4,
                  [dict(ad, ad_name="A", 광고비=400, 노출=5000, 클릭=300, 매출=2000),
                   dict(ad, ad_name="B", 광고비=300, 노출=2000, 클릭=400, 매출=1500)])
        # 라운드 C: 상위 소재만(필터 media·ad_name) — 전체 합이 아니다
        self.perf("2026-11-12", T, "day", dims4,
                  [dict(ad, date=d, ad_name="A", 광고비=10, 노출=100, 클릭=50, 매출=20) for d in DAYS],
                  filters={"media": ["M"], "ad_name": ["A", "B"]})

    def test_overall_uses_media_day_not_top_creatives(self):
        self.save_rounds(with_media_day=True)
        out = self.run_prepare("creative-report", "--media", "M")
        self.assertEqual(out["missing"], [])
        self.assertEqual(out["facts"]["overall_daily"]["ctr_series"], [10.0] * 7)

    def test_missing_media_day_leaves_overall_empty(self):
        # 매체 일별이 없으면 전체 일별을 비우고 다시 부르게 한다 — 상위 소재 합(50%)으로 채우지 않는다
        self.save_rounds(with_media_day=False)
        out = self.run_prepare("creative-report", "--media", "M")
        self.assertNotIn("overall_daily", out["facts"])
        self.assertIn({"tool": "get_ad_performance", "start_date": "2026-11-12", "end_date": T,
                       "time_grain": "day", "group_by": ["media"]}, out["missing"])


if __name__ == "__main__":
    unittest.main()
