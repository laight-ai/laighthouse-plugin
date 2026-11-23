#!/usr/bin/env python3
"""Claude Code판 스킬(plugins/laighthouse-analytics-prod/skills/)을 GPT판(laighthouse-analytics-gpt/skills/)으로 복사한다.

스킬 본문과 스크립트는 Claude Code판이 단일 소스다 — laighthouse-analytics-gpt/skills/는 이 스크립트가 만드는 사본이므로
직접 고치지 않는다. Claude Code판을 고친 뒤(공통 레포 스킬이면 sync.py로 가져온 뒤) 다시 실행한다:

    python3 laighthouse-analytics-gpt/sync_from_claude.py           # 사본을 다시 만든다
    python3 laighthouse-analytics-gpt/sync_from_claude.py --check   # 사본이 어긋났으면 목록을 보이고 1로 끝난다

하는 일:
- scripts/bundle_skills.py로 Claude Code판 스킬 폴더의 shared/ 사본을 먼저 원본에 맞춘다 — 스킬 폴더가 자기완결이라
  (Cowork·웹 Chat 모두 스킬 폴더 하나만 올린다) GPT판은 그 폴더를 그대로 쓴다.
- skills/<스킬>/ → laighthouse-analytics-gpt/skills/<스킬>/ (통째로 교체, __pycache__ 제외)
- agents-meta/<스킬>.yaml → skills/<스킬>/agents/openai.yaml (ChatGPT 스킬 메타)
- 외부 요인 보고서 스킬은 첫 제목 아래에 ChatGPT/Codex 환경 안내(NOTE)를 넣는다
- 훅(hooks/*.py·.md)은 레포 루트 common.json의 GPT target으로 laighthouse-plugin-common에서 받는다(여기서 다루지 않는다)
"""
import argparse
import filecmp
import os
import re
import shutil
import sys
import tempfile

GPT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(GPT)
SRC = os.path.join(ROOT, "plugins", "laighthouse-analytics-prod", "skills")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import bundle_skills  # noqa: E402

NOTE = {
    "external": """> 🧩 **ChatGPT/Codex 환경**
> - 응답 저장 훅(`hooks/save_responses.py`·`capture_*.py`)은 ChatGPT 데스크톱 Work 모드·Codex에서 `/hooks`로 신뢰했을 때만 돈다.
>   그때는 아래 절차 그대로 동작한다(큰 응답은 저장 안내 한 줄로만 보인다).
> - 스크립트 경로(`assets/…`)는 이 스킬 폴더 기준이다. 결과 파일은 사용자가 내려받을 수 있는 위치(작업 환경의 출력 폴더)에 저장한다.
> - 웹 Chat(스킬 업로드)에는 훅이 없다. `prepare.py`가 `missing`을 내면 받은 응답마다 쓰기 가능한 폴더 `<RESP>`에
>   `<번호>_<도구>.json` 파일로 `{"tool_name": "<도구>", "saved_at": <번호>, "tool_input": {<보낸 인자 그대로>}, "response": "<응답 원문 그대로>"}`를
>   저장하고 `prepare.py … --responses <RESP>`로 다시 실행한다. 응답 원문을 고치거나 줄이지 않는다.

""",
}


def add_note(path, note):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"^---\n.*?\n---\n", text, re.S)          # 앞머리(frontmatter) 뒤
    head, body = (text[:m.end()], text[m.end():]) if m else ("", text)
    h = re.search(r"^# .*\n", body, re.M)                    # 첫 제목이 있으면 그 아래, 없으면 앞머리 바로 아래
    if h:
        body = body[:h.end()] + "\n" + note + body[h.end():].lstrip("\n")
    else:
        body = "\n" + note + body.lstrip("\n")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(head + body)


def build_skill(name, out):
    """skills/<name>을 out/<name>으로 만든다."""
    dst = os.path.join(out, name)
    shutil.copytree(os.path.join(SRC, name), dst, ignore=IGNORE)
    meta = os.path.join(GPT, "agents-meta", f"{name}.yaml")
    if os.path.exists(meta):
        os.makedirs(os.path.join(dst, "agents"), exist_ok=True)
        shutil.copyfile(meta, os.path.join(dst, "agents", "openai.yaml"))
    note = NOTE.get(bundle_skills.family(name))
    if note:
        add_note(os.path.join(dst, "SKILL.md"), note)


def skill_names():
    return sorted(n for n in os.listdir(SRC) if os.path.isdir(os.path.join(SRC, n)))


def differences(a, b):
    """두 폴더 트리의 다른 파일(상대 경로) 목록."""
    out = []
    cmp = filecmp.dircmp(a, b, ignore=["__pycache__"])
    stack = [("", cmp)]
    while stack:
        rel, c = stack.pop()
        out += [os.path.join(rel, f) for f in c.left_only + c.right_only + c.diff_files + c.funny_files]
        stack += [(os.path.join(rel, d), sub) for d, sub in c.subdirs.items()]
    return sorted(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Claude Code판 스킬을 GPT판으로 복사한다")
    ap.add_argument("--check", action="store_true", help="사본이 맞는지만 확인한다")
    args = ap.parse_args(argv)
    missing_meta = [n for n in skill_names() if not os.path.exists(os.path.join(GPT, "agents-meta", f"{n}.yaml"))]
    if missing_meta:
        raise SystemExit(f"agents-meta에 없는 스킬: {', '.join(missing_meta)} — laighthouse-analytics-gpt/agents-meta/<스킬>.yaml을 만든다")
    if not args.check:
        bundle_skills.bundle()   # Claude Code판 스킬 폴더의 shared/ 사본부터 맞춘다
    with tempfile.TemporaryDirectory() as tmp:
        for name in skill_names():
            build_skill(name, tmp)
        dst = os.path.join(GPT, "skills")
        if args.check:
            diff = differences(tmp, dst) if os.path.isdir(dst) else ["skills/"]
            for d in diff:
                print("differs:", d.replace(os.sep, "/"))
            if diff:
                print("GPT판 사본이 어긋났다 — python3 laighthouse-analytics-gpt/sync_from_claude.py 를 실행한다", file=sys.stderr)
                return 1
            return 0
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(tmp, dst)
    for name in skill_names():
        print("skill", name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
