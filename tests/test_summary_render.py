"""Summary(s2) 렌더링 — section-2 문서의 출력 규칙: 본문은 <strong>만 허용(다른 태그는 글자로), head는 굵게,
Daily는 가이드대로 6개까지, 월간·MTD는 [소진]·[효율] 그룹."""
import json
import os
import subprocess
import sys
import unittest

SKILLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "plugins", "laighthouse-analytics-prod", "skills")
# 빌더는 import 할 때 stdout을 UTF-8로 다시 감싼다 — 테스트 프로세스를 건드리지 않게 하위 프로세스에서 부른다
CALL = """
import json, os, sys
sys.path.insert(0, sys.argv[1])
import build_report as m
r = getattr(m, sys.argv[2])(json.loads(sys.stdin.buffer.read().decode("utf-8")))
os.write(1, json.dumps(r, ensure_ascii=False).encode("utf-8"))
"""
BAD = "광고비 <strong>-97.8%</strong> 급락 <img src=x onerror=alert(1)>"


def render(skill, func, s2):
    assets = os.path.join(SKILLS, skill, "assets")
    p = subprocess.run([sys.executable, "-c", CALL, assets, func], cwd=assets, capture_output=True,
                       input=json.dumps(s2, ensure_ascii=False).encode("utf-8"))
    if p.returncode:
        raise AssertionError(p.stderr.decode("utf-8", "replace"))
    return json.loads(p.stdout.decode("utf-8"))


class DailyBulletsTest(unittest.TestCase):
    def test_only_strong_is_kept_and_head_is_bold(self):
        out = render("daily-report", "build_bullets",
                     {"bullets": [{"head": "NVSHOP / <캠페인>", "text": BAD, "tone": "red"}]})
        self.assertIn("<strong>-97.8%</strong>", out)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", out)
        self.assertNotIn("<img", out)
        self.assertIn("NVSHOP / &lt;캠페인&gt;</strong>", out)

    def test_at_most_six_bullets(self):
        out = render("daily-report", "build_bullets",
                     {"bullets": [{"text": f"불릿{i}", "tone": "neutral"} for i in range(8)]})
        self.assertIn("불릿5", out)
        self.assertNotIn("불릿6", out)


class CreativeBulletsTest(unittest.TestCase):
    def test_only_strong_is_kept(self):
        out = render("creative-report", "build_bullets", {"bullets": [{"head": "전체", "text": BAD, "tone": "red"}]})
        self.assertIn("<strong>-97.8%</strong>", out)
        self.assertNotIn("<img", out)


class MonthGroupsTest(unittest.TestCase):
    def test_groups_render_title_lead_media_and_escape(self):
        s2 = {"groups": [{"title": "소진", "lead": "총 광고비 <strong>₩1,000</strong>",
                          "media": [{"name": "NVSHOP", "desc": "설명",
                                     "bullets": [{"label": "캠페인A", "text": BAD, "tone": "red", "unit": "캠페인"}]}]}]}
        for skill in ("monthly-report", "mtd-report"):
            with self.subTest(skill=skill):
                out = render(skill, "build_groups", s2)
                self.assertIn("[소진]", out)
                self.assertIn("<strong>₩1,000</strong>", out)
                self.assertIn("NVSHOP", out)
                self.assertIn("캠페인A", out)
                self.assertNotIn("<img", out)

    def test_empty_groups_render_nothing(self):
        self.assertIsNone(render("monthly-report", "build_groups", {"groups": []}))


if __name__ == "__main__":
    unittest.main()
