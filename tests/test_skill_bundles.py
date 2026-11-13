"""스킬 폴더가 혼자 올라가도(Cowork) 동작하는지 — scripts/bundle_skills.py가 넣은 shared/ 사본 검사.

Cowork는 스킬 폴더 하나만 `/mnt/skills/plugins/<플러그인>:<스킬>`로 올린다. 여기서는 스킬 폴더만 같은 이름의
임시 폴더로 복사해, 스크립트가 찾는 공용 킷·킷이 읽는 파일·문서가 가리키는 경로가 모두 그 안에서 풀리는지 본다.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PLUGIN_NAME = "laighthouse-analytics-prod"
SKILLS = os.path.join(ROOT, "plugins", PLUGIN_NAME, "skills")
BUNDLER = os.path.join(ROOT, "scripts", "bundle_skills.py")

# 스크립트 하나를 실제 실행처럼(스크립트 폴더가 sys.path[0]) 불러 공용 킷 탐색까지 돌린 뒤, 불러온 모듈이 전부
# 스킬 폴더 안에서 왔는지와 킷이 읽는 파일(report_kit.css/js, Chart.js)이 있는지 본다.
# main 가드가 없는 스크립트는 --help(argparse: prepare.py·외부 요인 래퍼)나 stdin의 빈 디스커버리 봉투(discover.py)로 바로 끝난다.
PROBE = r"""
import glob, os, runpy, sys
script, skill_root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(script))
sys.argv = [script, *sys.argv[3:]]
try:
    ns = runpy.run_path(script, run_name="__probe__")
except SystemExit as e:
    if e.code not in (0, None):
        raise
    ns = {}
if "_load_kit" in ns:
    ns["_load_kit"]()
prefixes = tuple(p for p in {sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix} if p)
for name, mod in list(sys.modules.items()):
    f = getattr(mod, "__file__", None)
    if f and not os.path.abspath(f).startswith(prefixes):
        assert os.path.abspath(f).startswith(skill_root + os.sep), f"{name}: 스킬 폴더 밖 {f}"
kit = sys.modules.get("report_kit")
for tpl in glob.glob(os.path.join(skill_root, "assets", "*.html")):
    with open(tpl, encoding="utf-8") as fh:
        html = fh.read()
    if "__REPORT_KIT_" in html:
        assert kit is not None, f"{tpl}: report_kit을 불러오지 않았다"
        assert "__REPORT_KIT_" not in kit.inline_assets(html), f"{tpl}: 킷 css/js를 넣지 못했다"
page = sys.modules.get("page")
if page is not None:
    assert os.path.exists(os.path.join(page.HERE, "chart.umd.min.js")), "page.py가 인라인할 Chart.js가 없다"
"""

PATH_MENTION = re.compile(r"shared/(?:references|assets)/[\w./-]+\.(?:md|py|css|js)\b")
TEXT_SUFFIXES = (".md", ".py", ".html", ".css")   # *.js는 내려받은 Chart.js(min)라 제외


def skill_names():
    return sorted(n for n in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, n)))


class TestBundleCheck(unittest.TestCase):
    def test_copies_match_shared(self):
        r = subprocess.run([sys.executable, BUNDLER, "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0,
                         "스킬 폴더의 shared/ 사본이 원본과 어긋났다 — python3 scripts/bundle_skills.py 를 실행해 다시 만든다\n"
                         + r.stdout + r.stderr)


class TestSkillAloneLikeCowork(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.env = dict(os.environ, TMPDIR=os.path.join(self.tmp, "t"), PYTHONDONTWRITEBYTECODE="1")
        os.makedirs(self.env["TMPDIR"])

    def mount(self, skill):
        """스킬 폴더만 `<tmp>/plugins/<플러그인>:<스킬>`로 복사한다(위로 올라가도 shared/가 없다)."""
        dst = os.path.join(self.tmp, "plugins", f"{PLUGIN_NAME}:{skill}")
        shutil.copytree(os.path.join(SKILLS, skill), dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        return os.path.realpath(dst)

    def run_py(self, *args, stdin=""):
        return subprocess.run([sys.executable, *args], input=stdin, capture_output=True, text=True,
                              cwd=self.tmp, env=self.env)

    def test_every_script_finds_its_kit_inside_the_skill(self):
        for skill in skill_names():
            root = self.mount(skill)
            for name in sorted(os.listdir(os.path.join(root, "assets")) if os.path.isdir(os.path.join(root, "assets")) else []):
                if not name.endswith(".py"):
                    continue
                with self.subTest(skill=skill, script=name):
                    args = [] if name == "discover.py" else ["--help"]   # discover.py는 인자를 입력 파일로 읽는다
                    r = self.run_py("-c", PROBE, os.path.join(root, "assets", name), root, *args,
                                    stdin='{"metrics": [], "rows": []}')
                    self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_report_prepare_runs_under_prefixed_folder_name(self):
        # Cowork 폴더 이름(`<플러그인>:<스킬>`)으로도 스킬을 알아보고, 저장 응답이 없으면 폴백 안내를 낸다
        for skill in ("creative-detailed", "creative-summary", "daily-detailed", "daily-summary",
                      "monthly-detailed", "monthly-summary", "mtd-detailed", "mtd-summary"):
            with self.subTest(skill=skill):
                root = self.mount(skill)
                r = self.run_py(os.path.join(root, "assets", "prepare.py"), "--brand", "t", "--target-date", "2026-11-10")
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn("note", json.loads(r.stdout))

    def test_text_paths_stay_inside_the_skill(self):
        for skill in skill_names():
            root = os.path.join(SKILLS, skill)
            for dirpath, dirnames, files in os.walk(root):
                dirnames[:] = [d for d in dirnames if d != "__pycache__"]
                for f in files:
                    if not f.endswith(TEXT_SUFFIXES):
                        continue
                    path = os.path.join(dirpath, f)
                    with open(path, encoding="utf-8") as fh:
                        text = fh.read()
                    rel = os.path.relpath(path, SKILLS)
                    with self.subTest(file=rel):
                        self.assertNotIn("../", text, "스킬 폴더 밖을 가리키는 상대 경로")
                        for m in sorted(set(PATH_MENTION.findall(text))):
                            self.assertTrue(os.path.exists(os.path.join(root, m)), f"{m}이 스킬 폴더에 없다")


if __name__ == "__main__":
    unittest.main()
