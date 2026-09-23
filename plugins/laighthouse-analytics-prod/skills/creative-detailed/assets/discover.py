#!/usr/bin/env python3
"""디스커버리 해석기 — 매체 목록·Organic 여부·지표 역할 키·통화를 한 번에 정한다.

사용법 (실행 순서 2단계, 디스커버리 응답을 받은 그 자리에서 1회):
  python3 assets/discover.py <<'PYEOF'
  <get_ad_performance(time_grain "total", group_by ["media"], metrics 생략) 응답 원문 그대로>
  PYEOF
  (캡처 스텁으로 왔으면 {"json_files": ["<스텁 경로>"]})

출력(stdout JSON) — 규칙은 shared/references/generic-report-pattern.md 2·3절:
  media_list   매체 값(응답 문자열 그대로, 응답 순서)      has_organic  media=null 행 존재 여부
  metric_keys  역할→실제 키 (revenue/conversion은 있을 때만) has_revenue  매출 있음 모드 여부
  currency     광고비 지표의 metric_units 값(없으면 "₩")     metric_names 봉투 metrics 전체
  missing      못 찾은 필수 역할(cost/impression/click) → 사용자에게 한 번에 질문
  ambiguous    접두 일치 후보가 여럿인 역할 → 사용자에게 한 번에 질문
"""
import io
import os
import sys

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
for cand in (os.path.join(HERE, "..", "shared", "assets"),          # ChatGPT 번들
             os.path.join(HERE, "..", "..", "..", "shared", "assets")):  # 플러그인 루트
    if os.path.exists(os.path.join(cand, "report_kit.py")):
        sys.path.insert(0, os.path.normpath(cand))
        break
else:
    raise SystemExit("report_kit.py를 찾을 수 없다 (shared/assets)")
import report_kit  # noqa: E402

report_kit.discover_main(sys.stdin, sys.stdout)
