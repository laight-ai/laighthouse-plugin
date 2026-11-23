"""laighthouse-analytics-gpt/skills/가 Claude Code판 스킬과 맞는지 — sync_from_claude.py --check."""
import os
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


def test_gpt_has_exactly_the_claude_skills_with_metadata():
    claude = sorted(n for n in os.listdir(CLAUDE_SKILLS) if os.path.isdir(os.path.join(CLAUDE_SKILLS, n)))
    gpt = sorted(n for n in os.listdir(GPT_SKILLS) if os.path.isdir(os.path.join(GPT_SKILLS, n)))
    assert gpt == claude
    for name in gpt:
        assert os.path.exists(os.path.join(GPT_SKILLS, name, "agents", "openai.yaml")), name
