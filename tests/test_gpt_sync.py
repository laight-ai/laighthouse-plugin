"""laighthouse-analytics-gpt/skills/가 Claude Code판 스킬과 맞는지 — sync_from_claude.py --check."""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SYNC = os.path.join(ROOT, "laighthouse-analytics-gpt", "sync_from_claude.py")
GPT_SKILLS = os.path.join(ROOT, "laighthouse-analytics-gpt", "skills")
CLAUDE_SKILLS = os.path.join(ROOT, "plugins", "laighthouse-analytics-prod", "skills")


def test_gpt_copies_match_claude_skills():
    r = subprocess.run([sys.executable, SYNC, "--check"], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, ("GPT판 사본이 어긋났다 — python3 laighthouse-analytics-gpt/sync_from_claude.py 를 실행한다\n"
                               + r.stdout + r.stderr)


def test_gpt_note_only_on_external_skills_right_under_title():
    # 외부 요인 스킬에만 ChatGPT/Codex 안내가 한 번, 앞머리 뒤 첫 제목 바로 아래에 들어간다
    for name in sorted(os.listdir(GPT_SKILLS)):
        with open(os.path.join(GPT_SKILLS, name, "SKILL.md"), encoding="utf-8") as f:
            text = f.read().replace("\r\n", "\n")
        count = text.count("ChatGPT/Codex 환경")
        external = name in ("naver-blog", "naver-news", "naver-search", "weather-impact")
        assert count == (1 if external else 0), name
        if external:
            body = text.split("\n---\n", 1)[1].lstrip("\n")
            first = body.split("\n", 1)[0]
            after_title = body.split("\n", 1)[1].lstrip("\n") if first.startswith("# ") else body
            assert after_title.startswith("> 🧩 **ChatGPT/Codex 환경**"), name


def save_matchers(hooks_json):
    with open(hooks_json, encoding="utf-8") as f:
        hooks = json.load(f)["hooks"]["PostToolUse"]
    return [e["matcher"] for e in hooks if any("save_responses.py" in h["command"] for h in e["hooks"])]


def test_save_hook_stores_what_remaining_skills_read_in_both_editions():
    # 외부 요인 스킬은 저장 훅이 남긴 get_external_context(날씨는 get_ad_performance도) 응답을 prepare.py로 읽는다
    for hooks_json in (os.path.join(ROOT, "plugins", "laighthouse-analytics-prod", "hooks", "hooks.json"),
                       os.path.join(ROOT, "laighthouse-analytics-gpt", "hooks", "hooks.json")):
        matchers = save_matchers(hooks_json)
        for tool in ("mcp__laighthouse__get_external_context", "mcp__laighthouse__get_ad_performance"):
            assert any(re.search(m, tool) for m in matchers), (hooks_json, tool)
