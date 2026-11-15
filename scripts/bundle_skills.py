#!/usr/bin/env python3
"""플러그인 공용 폴더(shared/)에서 스킬마다 필요한 파일만 골라 `skills/<스킬>/shared/`에 복사한다.

왜 필요한가: Claude Desktop Cowork는 플러그인 스킬 폴더를 하나씩 따로
`/mnt/skills/plugins/<플러그인>:<스킬>`에 올린다. 플러그인 루트의 `shared/`는 어디에도 올라가지 않으므로
스킬 폴더 밖을 가리키는 스크립트·문서는 Cowork에서 깨진다. 그래서 각 스킬 폴더가 자기 안에
`shared/assets`·`shared/references` 사본을 갖고, 스크립트는 이 사본을 먼저 찾는다.

원본은 언제나 플러그인 루트의 `shared/`다. 스킬 폴더 안 `shared/`는 이 스크립트가 만드는 사본이므로
손으로 고치지 않는다. `shared/`를 고친 뒤에는 다시 실행해 사본을 맞춘다:

    python3 scripts/bundle_skills.py           # 사본을 다시 만든다
    python3 scripts/bundle_skills.py --check   # 어긋난 사본(differs/missing/extra)을 보여 주고 1로 끝난다

스킬마다 넣는 파일은 아래 BUNDLES에 명시한다. 스킬을 새로 만들면 여기에 항목을 더한다
(공용 파일이 필요 없으면 빈 튜플).
"""
import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugins", "laighthouse-analytics-prod")
SHARED = os.path.join(PLUGIN, "shared")
SKILLS = os.path.join(PLUGIN, "skills")

# prepare_kit.py가 report_kit을 import한다.
KIT = ("assets/prepare_kit.py", "assets/report_kit.py")
# 템플릿에 __REPORT_KIT_CSS__/__REPORT_KIT_JS__가 있는 스킬만 report_kit.inline_assets가 읽는다.
KIT_INLINE = ("assets/report_kit.css", "assets/report_kit.js")
# generic-report-pattern.md가 mcp-tools.md·media-trend.md를 가리킨다.
REPORT_REFS = ("references/generic-report-pattern.md", "references/mcp-tools.md", "references/media-trend.md")
TARGET_REFS = ("references/target-achievement.md",)
# range_report.py가 import하는 모듈 전부 + page.py가 인라인하는 Chart.js
RANGE_REPORT = tuple("assets/external_context/" + f for f in (
    "blog_trend.py", "buzz.py", "chart.umd.min.js", "check_citations.py", "news_trend.py", "page.py",
    "range_report.py", "responses.py", "saved.py", "search_aggregate.py", "search_db.py", "trend_config.py",
    "trend_core.py", "trend_report.py"))
EXTERNAL_REFS = ("references/mcp-tools.md",)

BUNDLES = {
    "creative-detailed": KIT + REPORT_REFS,
    "creative-summary": KIT + REPORT_REFS,
    "daily-detailed": KIT + KIT_INLINE + REPORT_REFS + TARGET_REFS,
    "daily-summary": KIT + KIT_INLINE + REPORT_REFS + TARGET_REFS,
    "monthly-detailed": KIT + KIT_INLINE + REPORT_REFS + TARGET_REFS,
    "monthly-summary": KIT + KIT_INLINE + REPORT_REFS + TARGET_REFS,
    "mtd-detailed": KIT + KIT_INLINE + REPORT_REFS + TARGET_REFS,
    "mtd-summary": KIT + KIT_INLINE + REPORT_REFS + TARGET_REFS,
    "media-mix-result": KIT,   # 저장 훅 응답 읽기(prepare_kit)만
    "naver-blog": RANGE_REPORT + EXTERNAL_REFS,
    "naver-news": RANGE_REPORT + EXTERNAL_REFS,
    "naver-search": RANGE_REPORT + EXTERNAL_REFS,
    "weather-impact": RANGE_REPORT + ("assets/external_context/weather_trend.py",) + EXTERNAL_REFS,
    "skill-catalog": (),
}


def skill_names():
    return sorted(n for n in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, n)))


def existing_copies(skill):
    """skills/<스킬>/shared/ 아래 파일(상대 경로). __pycache__·*.pyc는 무시한다."""
    base = os.path.join(SKILLS, skill, "shared")
    found = set()
    for dirpath, dirnames, files in os.walk(base):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for f in files:
            if not f.endswith(".pyc"):
                found.add(os.path.relpath(os.path.join(dirpath, f), base).replace(os.sep, "/"))
    return found


def drift():
    """어긋난 사본 목록 [(종류, 경로)] — 종류는 differs/missing/extra, 경로는 플러그인 폴더 기준."""
    unknown = set(skill_names()) - set(BUNDLES)
    if unknown:
        raise SystemExit(f"BUNDLES에 없는 스킬: {', '.join(sorted(unknown))} — scripts/bundle_skills.py에 항목을 더한다")
    out = []
    for skill in skill_names():
        want = set(BUNDLES[skill])
        have = existing_copies(skill)
        for rel in sorted(want | have):
            dst = f"skills/{skill}/shared/{rel}"
            if rel not in have:
                out.append(("missing", dst))
            elif rel not in want:
                out.append(("extra", dst))
            else:
                with open(os.path.join(SHARED, rel), "rb") as a, open(os.path.join(PLUGIN, dst), "rb") as b:
                    if a.read() != b.read():
                        out.append(("differs", dst))
    return out


def bundle():
    drift()   # BUNDLES에 없는 스킬이 있으면 여기서 멈춘다
    for skill in skill_names():
        dst = os.path.join(SKILLS, skill, "shared")
        shutil.rmtree(dst, ignore_errors=True)
        for rel in BUNDLES[skill]:
            target = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(os.path.join(SHARED, rel), target)
        print(f"{skill}: {len(BUNDLES[skill])}개")


def main(argv=None):
    ap = argparse.ArgumentParser(description="스킬 폴더마다 필요한 shared/ 사본을 넣는다")
    ap.add_argument("--check", action="store_true", help="사본이 원본과 같은지만 확인한다")
    args = ap.parse_args(argv)
    if not args.check:
        bundle()
        return 0
    problems = drift()
    for kind, path in problems:
        print(f"{kind}: {path}")
    if problems:
        print("사본이 shared/와 어긋났다 — python3 scripts/bundle_skills.py 를 실행해 다시 만든다", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
