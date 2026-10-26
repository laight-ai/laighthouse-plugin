#!/usr/bin/env python3
"""저장된 MCP 응답 → 빌더 기본 입력(base.json) + 요약 근거(facts). 본체는 shared/assets/prepare_kit.py.

사용법 (SKILL.md의 MCP 호출을 한 메시지에 모두 보낸 직후, 1회):
  python3 assets/prepare.py --brand <브랜드> --target-date <YYYY-MM-DD>
출력(stdout JSON): base(경로) · facts · missing · errors · ask_user(있을 때만)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for cand in (os.path.join(HERE, "..", "shared", "assets"),          # ChatGPT 번들
             os.path.join(HERE, "..", "..", "..", "shared", "assets")):  # 플러그인 루트
    if os.path.exists(os.path.join(cand, "prepare_kit.py")):
        sys.path.insert(0, os.path.normpath(cand))
        break
else:
    raise SystemExit("prepare_kit.py를 찾을 수 없다 (shared/assets)")
import prepare_kit  # noqa: E402

prepare_kit.main(os.path.basename(os.path.dirname(HERE)), assets_dir=HERE)
