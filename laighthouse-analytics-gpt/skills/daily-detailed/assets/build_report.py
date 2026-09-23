#!/usr/bin/env python3
"""daily-detailed 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

`assets/report-template.html`(섹션 1~4 마크업·스크립트가 전부 들어있는 단일 진실 공급원)에
값을 치환하고 `chart.umd.min.js`와 공용 킷(`shared/assets/report_kit.*`)을 인라인해서
**최종 HTML 한 파일을 한 번의 호출로** 만든다. 모델은 HTML을 한 글자도 타이핑하지 않는다 —
아래 값 JSON만 heredoc으로 넘기면 된다. 모드 분기(매출 있음/없음, Organic 있음/없음)와 계층 표
생성은 전부 공용 킷이 한다(`shared/references/generic-report-pattern.md` 7·8절).

사용법 (단 한 번의 Bash 호출, 응답을 받은 그 자리에서):
  python3 assets/build_report.py <<'PYEOF'
  { ...아래 입력 JSON... }
  PYEOF

입력 (stdin, JSON):
{
  "out": "~/Downloads/laighthouse-reports/{브랜드명}_daily-detailed_2026-08-10.html",  # 필수
  "title": "{브랜드명} 데일리 보고서",                                                  # 필수
  "target_date": "2026-08-10",                                                     # 필수 (D-0)
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
  "metric_keys": {...},      # discover.py 출력 그대로 (revenue 없으면 매출 없음 모드)
  "has_organic": true,       # discover.py 출력 그대로
  "currency": "₩",           # discover.py 출력 그대로

  "s1": {"목표_예산": .., "소진액": .., "목표_매출": .., "기간_매출": .., "기간_노출": .., "기간_클릭": ..},
                             # shared/references/target-achievement.md — 원본 숫자, 없으면 null
  "s2": {"executive_summary": "문장1\n문장2\n⚠ 주의 문장..."},   # \n 구분, ⚠ 시작 줄은 주황색
  "s3": {                    # 최근 7일 — 배열 7개(기준일-6일 ~ 기준일), 광고 매체 행(media non-null) 합
    "cost": [..], "revenue": [..],           # 매출 있음
    "impression": [..], "click": [..],       # 매출 없음 (cost도 함께)
    "promotions": [{"title": "여름 세일", "date_begin": "2026-08-01", "date_end": "2026-08-31"}]
  },
  "s4": {                    # 계층 표 — 레벨별 get_ad_performance 응답(D-1~D0 포함, metrics 생략)
    "json_files": ["<캡처 스텁 경로>", ...],   # 스텁으로 온 응답
    "json": ["<원본 봉투 문자열>", ...]          # 원본으로 온 응답 (섞어도 된다)
  }
}

- s1~s4 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
- 출력(stdout): {"out": 절대경로, "bytes": 크기, "mode": {...}, "sections": {...}, "tree_nodes": N}
"""
import io
import json
import os
import sys
from datetime import date, timedelta

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(ASSETS_DIR, "report-template.html")
CHART_JS = os.path.join(ASSETS_DIR, "chart.umd.min.js")


def _load_kit():
    for cand in (os.path.join(ASSETS_DIR, "..", "shared", "assets"),          # ChatGPT 번들
                 os.path.join(ASSETS_DIR, "..", "..", "..", "shared", "assets")):  # 플러그인 루트
        if os.path.exists(os.path.join(cand, "report_kit.py")):
            sys.path.insert(0, os.path.normpath(cand))
            import report_kit
            return report_kit
    raise SystemExit("report_kit.py를 찾을 수 없다 (shared/assets)")


kit = _load_kit()

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]
PLACEHOLDER_CARD = '<div class="card"><p style="color:#94a3b8;font-size:13px;">데이터 준비 중</p></div>'
S3_NO_REVENUE_NOTE = ('<p style="font-size:11px; color:#94a3b8; margin-top:8px;">'
                      "* 매출 지표가 없는 브랜드라 클릭·CTR 기준으로 표시합니다. 광고비·노출·CPC는 "
                      "막대에 마우스를 올리면 확인할 수 있습니다.</p>")


def swap_section(html, key, replacement):
    begin = f"<!--SECTION:{key}:BEGIN-->"
    end = f"<!--SECTION:{key}:END-->"
    i = html.index(begin)
    j = html.index(end) + len(end)
    return html[:i] + replacement + html[j:]


def build_labels(target):
    return [f"{d.month}/{d.day}({WEEKDAY_KO[d.weekday()]})"
            for d in (target - timedelta(days=6 - i) for i in range(7))]


def build_promotions(promos, target):
    """list_promotions 원본(date_begin/date_end) 또는 사전 계산본을 받아
    인덱스 계산·클램프·범위 밖 제외·range_label 생성까지 처리한다."""
    if not promos:
        return []
    first = target - timedelta(days=6)
    out = []
    for p in promos:
        if "start_idx" in p and "end_idx" in p:
            out.append({"title": p.get("title", ""), "start_idx": max(0, min(6, p["start_idx"])),
                        "end_idx": max(0, min(6, p["end_idx"])),
                        "range_label": p.get("range_label", "")})
            continue
        begin = date.fromisoformat(str(p["date_begin"])[:10])
        end = date.fromisoformat(str(p["date_end"])[:10])
        raw_s = (begin - first).days
        raw_e = (end - first).days
        if raw_e < 0 or raw_s > 6:
            continue  # 차트 범위와 전혀 안 겹침
        if begin.month == end.month:
            range_label = f"{begin.month}/{begin.day}~{end.day}"
        else:
            range_label = f"{begin.month}/{begin.day}~{end.month}/{end.day}"
        out.append({"title": p.get("title", ""), "start_idx": max(0, raw_s),
                    "end_idx": min(6, raw_e), "range_label": range_label})
    return out


def build_summary_items(text):
    items = []
    for line in (text or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        style = ' style="color:#d97706;"' if line.startswith("⚠") else ""
        items.append(f"<li{style}>{line}</li>")
    return "\n      ".join(items)


def tree_note(d1, target):
    return (f"* 각 값 아래 증감은 {d1.month}월 {d1.day}일 대비 {target.month}월 {target.day}일 변화입니다 "
            "(비율 지표는 %p). 시작은 매체 단위이며 ▶를 눌러 캠페인·광고그룹·광고로 펼칠 수 있습니다. "
            "지표 헤더를 누르면 정렬되고(기본: 광고비 내림차순), '지표 선택'으로 표시할 컬럼을 고를 수 있습니다.")


def main():
    payload = json.load(sys.stdin)
    target = date.fromisoformat(payload["target_date"])
    d1 = target - timedelta(days=1)
    skeleton = bool(payload.get("skeleton"))
    currency = payload.get("currency") or "₩"
    metric_keys = payload.get("metric_keys") or {}
    modes = kit.Modes(metric_keys, payload.get("has_organic"))

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    status = {}
    tree_nodes = 0

    def section_data(key):
        return None if skeleton else payload.get(key)

    # ── section 1
    s1 = section_data("s1")
    if s1:
        status["s1"] = "ok"
        html = html.replace("__S1_GRID_HTML__", kit.s1_grid_html(s1, modes, currency))
        html = html.replace("__S1_FOOTNOTE_HTML__", kit.s1_footnote_html(s1))
        html = html.replace("__S1_MM__", str(target.month)).replace("__S1_DD__", str(target.day))
    else:
        status["s1"] = "placeholder"
        html = swap_section(html, "s1", PLACEHOLDER_CARD)

    # ── section 2
    s2 = section_data("s2")
    if s2 and s2.get("executive_summary"):
        status["s2"] = "ok"
        html = html.replace("__S2_ITEMS_HTML__", build_summary_items(s2["executive_summary"]))
    else:
        status["s2"] = "placeholder"
        html = swap_section(html, "s2", PLACEHOLDER_CARD)

    # ── section 3
    s3 = section_data("s3")
    if s3 and (s3.get("cost") or s3.get("ad_cost") or s3.get("click")):
        status["s3"] = "ok"
        s3_spec = kit.perf_chart_spec(s3.get("labels") or build_labels(target), s3, modes)
        s3_promos = build_promotions(s3.get("promotions"), target)
        html = html.replace("__S3_FOOTNOTE_HTML__", "" if modes.has_revenue else S3_NO_REVENUE_NOTE)
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        s3_spec, s3_promos = None, []
    html = html.replace("__S3_CHART_SPEC_JSON__", kit.js_json(s3_spec))
    html = html.replace("__S3_PROMOTIONS_JSON__", kit.js_json(s3_promos))

    # ── section 4 (계층 표)
    s4 = section_data("s4")
    tree = None
    if s4 and (s4.get("json_files") or s4.get("json")):
        tree = kit.build_tree(kit.load_envelopes(s4), d1.isoformat(), target.isoformat(),
                              metric_keys, has_organic=modes.has_organic)
        if tree["nodes"]:
            status["s4"] = "ok"

            def count(nodes):
                return sum(1 + count(n[3]) for n in nodes)
            tree_nodes = count(tree["nodes"])
        else:
            tree = None
    if tree is None:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)
    html = html.replace("__S4_TREE_JSON__", kit.js_json(tree))
    html = html.replace("__S4_NOTE_JSON__", kit.js_json(tree_note(d1, target)))

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", payload["title"])
    html = html.replace("__CURRENCY_JSON__", kit.js_json(currency))
    html = html.replace("__REPORT_DATE_LABEL__", f"{target.year}년 {target.month}월 {target.day}일 기준")
    html = (html.replace("__D1_MM__", str(d1.month)).replace("__D1_DD__", str(d1.day))
                .replace("__D0_MM__", str(target.month)).replace("__D0_DD__", str(target.day)))

    # ── 치환 누락 검증 (인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__S1_", "__S2_", "__S3_", "__S4_",
        "__CURRENCY", "__D1_", "__D0_",
    ] if t in html]
    if leftovers:
        raise SystemExit(f"치환 누락: {leftovers}")

    # ── 공용 킷·chart.js 인라인 (마지막 — 내용이 커서 치환 검증 후에 붙인다)
    html = kit.inline_assets(html)
    with open(CHART_JS, encoding="utf-8") as f:
        html = html.replace("__CHART_JS_INLINE__", f.read())

    out_path = os.path.abspath(os.path.expanduser(payload["out"]))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    json.dump({"out": out_path, "bytes": os.path.getsize(out_path),
               "mode": {"has_revenue": modes.has_revenue, "has_organic": modes.has_organic,
                        "has_conversion": modes.has_conversion},
               "sections": status, "tree_nodes": tree_nodes}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
