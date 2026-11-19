"""report_kit 화면 규칙 — 매체별 추이 지표 메뉴, 계층 표가 처음 펼쳐 보이는 열."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "plugins", "laighthouse-analytics-prod", "shared", "assets"))
import report_kit as kit  # noqa: E402

KEYS = {"cost": "광고비", "impression": "노출", "click": "클릭", "revenue": "매출"}


class MediaTrendMenuTest(unittest.TestCase):
    def spec(self, rows, metrics):
        env = {"dimensions": ["date", "media"], "metrics": metrics, "metric_units": {}, "rows": rows}
        return kit.media_trend_from_envelopes(["7/1", "7/2"], ["2026-07-01", "2026-07-02"], [env], KEYS)

    def test_metrics_without_values_are_dropped_but_roles_stay(self):
        # video_x는 0뿐, 조회수는 null뿐 → 메뉴에서 뺀다. 매출은 0뿐이어도 역할 지표라 남긴다.
        rows = [{"date": d, "media": "M", "광고비": 100, "노출": 1000, "클릭": 10, "매출": 0, "video_x": 0, "조회수": None}
                for d in ("2026-07-01", "2026-07-02")]
        spec = self.spec(rows, ["광고비", "노출", "클릭", "매출", "video_x", "조회수"])
        self.assertEqual({m["key"] for m in spec["metrics"]}, {"광고비", "노출", "클릭", "매출"})

    def test_metric_with_a_value_on_one_day_stays(self):
        rows = [{"date": "2026-07-01", "media": "M", "광고비": 100, "노출": 1, "클릭": 1, "매출": 1, "video_x": 0},
                {"date": "2026-07-02", "media": "M", "광고비": 100, "노출": 1, "클릭": 1, "매출": 1, "video_x": 7}]
        spec = self.spec(rows, ["광고비", "노출", "클릭", "매출", "video_x"])
        self.assertIn("video_x", [m["key"] for m in spec["metrics"]])


class TreeDefaultColumnsTest(unittest.TestCase):
    def test_first_six_filled_metrics_by_priority(self):
        # 우선순위: 광고비·매출·roas·클릭·ctr·(전환 없음)·노출·cpc → 값 있는 앞의 6개. 값 없는 video_x는 숨긴다.
        metrics = ["광고비", "노출", "클릭", "매출", "cpc", "ctr", "roas", "video_x"]
        row = {"month": "2026-07", "media": "M", "광고비": 100, "노출": 1000, "클릭": 10, "매출": 500,
               "cpc": 10.0, "ctr": 1.0, "roas": 500.0, "video_x": None}
        env = {"dimensions": ["month", "media"], "metrics": metrics, "metric_units": {}, "rows": [row]}
        tree = kit.build_tree([env], "2026-06", "2026-07", KEYS)
        shown = [m["key"] for m in tree["metrics"] if m["show"]]
        self.assertEqual(sorted(shown), sorted(["광고비", "매출", "roas", "클릭", "ctr", "노출"]))
        self.assertFalse(next(m for m in tree["metrics"] if m["key"] == "video_x")["show"])


if __name__ == "__main__":
    unittest.main()
