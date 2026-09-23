#!/usr/bin/env python3
"""daily-summary 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

`assets/report-template.html`(섹션 1~5 마크업·스크립트가 전부 들어있는 단일 진실 공급원)에
값을 치환하고 `chart.umd.min.js`와 공용 킷(`shared/assets/report_kit.*`)을 인라인해서
**최종 HTML 한 파일을 한 번의 호출로** 만든다. 모델은 HTML을 한 글자도 타이핑하지 않는다 —
아래 값 JSON만 heredoc으로 넘기면 된다. 모드 분기(매출 있음/없음, Organic 있음/없음)는
전부 공용 킷이 한다(`shared/references/generic-report-pattern.md` 7절).

사용법 (단 한 번의 Bash 호출, 응답을 받은 그 자리에서):
  python3 assets/build_report.py <<'PYEOF'
  { ...아래 입력 JSON... }
  PYEOF

입력 (stdin, JSON):
{
  "out": "~/Downloads/laighthouse-reports/{브랜드명}_daily-summary_2026-05-15.html",  # 필수
  "title": "{브랜드명} Executive 데일리 보고서",                                       # 필수
  "target_date": "2026-05-15",                                                    # 필수 (D-0)
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
  "metric_keys": {           # 역할 → 실제 지표 키 (generic-report-pattern.md 3절)
    "cost": "<광고비 키>", "impression": "<노출 키>", "click": "<클릭 키>",
    "revenue": "<매출 키>",       # 선택 — 없으면 "매출 없음 모드"(매출·ROAS → 노출·클릭·CTR·CPC)
    "conversion": "<전환 키>"     # 선택 — 없으면 전환 컬럼 생략
  },
  "has_organic": true,       # 디스커버리에 media=null 행이 있었는지 (매출 없음 모드에선 무시)
  "currency": "₩",           # 선택 — 금액 기호, 기본 "₩"

  "s1": {                    # 목표 달성 현황 — 원본 숫자, 없으면 null (포맷·파생 비율은 킷이 계산)
    "목표_예산": 168110000, "소진액": 55700000,
    "목표_매출": null, "기간_매출": 123456789,          # 매출 있음 모드
    "기간_노출": 1234567, "기간_클릭": 23456            # 매출 없음 모드
  },
  "s2": {"bullets": [{"text": "...<strong>+22.4%</strong>...", "tone": "green|red|neutral"}]},
  "s3": {                    # 최근 7일 — 배열 7개(기준일-6일 ~ 기준일), 광고 매체 행(media non-null) 합
    "cost": [..], "revenue": [..],                  # 매출 있음
    "impression": [..], "click": [..],              # 매출 없음 (cost도 함께 — 툴팁·CPC용)
    "promotions": [{"title": "여름 세일", "date_begin": "2026-05-09", "date_end": "2026-05-11"}]
  },
  "s4": {                    # 매체별 추이 — 매출 있음: revenue 값, 매출 없음: click 값 (배열 7개)
    "series": [{"name": "<media 값 그대로>", "values": [..7개..]}, ...,
               {"name": "Organic", "values": [..]}],   # Organic은 has_organic일 때만
    "promotions": [...]
  },
  "s5": {                    # 매체별 성과 (D-1 vs D-0) — 역할별 원본 수치
    "rows": [{"name": "<media 값>", "d1": {"cost":..,"impression":..,"click":..,"revenue":..,"conversion":..},
                                    "d0": {...}},
             {"name": "Organic", "d1": {"revenue":..,"conversion":..}, "d0": {...}}]
  }
}

- s1~s5 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
- 출력(stdout): {"out": 절대경로, "bytes": 크기, "mode": {...}, "sections": {"s1": "ok"|"placeholder", ...}}
"""
import io
import json
import os
import shutil
import sys
from datetime import date, timedelta

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(ASSETS_DIR, "report-template.html")
CHART_JS = os.path.join(ASSETS_DIR, "chart.umd.min.js")
# 스킬 폴더 assets에 chart.umd.min.js가 없으면 자매 스킬 daily-detailed의 것을 복사해 온다.
CHART_JS_FALLBACK = os.path.normpath(os.path.join(
    ASSETS_DIR, "..", "..", "daily-detailed", "assets", "chart.umd.min.js"))


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

# section-2 불릿 점(●) 색상 — 성장/개선=초록, 하락/점검=빨강, 중립 관찰=회색-갈색
S2_TONE_COLORS = {"green": "#16a34a", "red": "#dc2626", "neutral": "#78716c"}


def swap_section(html, key, replacement):
    begin = f"<!--SECTION:{key}:BEGIN-->"
    end = f"<!--SECTION:{key}:END-->"
    i = html.index(begin)
    j = html.index(end) + len(end)
    return html[:i] + replacement + html[j:]


def week_dates(target):
    return [target - timedelta(days=6 - i) for i in range(7)]


def build_s3_labels(target):
    return [f"{d.month}/{d.day}({WEEKDAY_KO[d.weekday()]})" for d in week_dates(target)]


def build_s4_labels(target):
    # Chart.js가 배열 라벨을 두 줄로 렌더링하는 것을 이용 — 날짜(M/D) 아래에 (요일).
    return [[f"{d.month}/{d.day}", f"({WEEKDAY_KO[d.weekday()]})"] for d in week_dates(target)]


def s3_range_label(begin, end):
    if begin.month == end.month:
        return f"{begin.month}/{begin.day}~{end.day}"
    return f"{begin.month}/{begin.day}~{end.month}/{end.day}"


def s4_range_label(begin, end):
    if begin.month == end.month:
        return f"{begin.month}월 {begin.day}일~{end.day}일"
    return f"{begin.month}월 {begin.day}일~{end.month}월 {end.day}일"


def build_promotions(promos, target, label_fn):
    """list_promotions 원본(date_begin/date_end) 또는 사전 계산본을 받아
    인덱스 계산·클램프·범위 밖 제외·range_label 생성까지 처리한다.
    range_label은 클램핑 전의 원래 날짜로 만든다."""
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
        out.append({"title": p.get("title", ""), "start_idx": max(0, raw_s),
                    "end_idx": min(6, raw_e), "range_label": label_fn(begin, end)})
    return out


def build_bullets(s2):
    """s2 → 불릿 카드 HTML. bullets 배열(text/tone) 우선, executive_summary 문자열도 허용."""
    bullets = s2.get("bullets")
    if bullets is None and s2.get("executive_summary"):
        bullets = [{"text": line.strip(), "tone": "neutral"}
                   for line in s2["executive_summary"].split("\n") if line.strip()]
    items = []
    for b in bullets or []:
        color = S2_TONE_COLORS.get(b.get("tone", "neutral"), S2_TONE_COLORS["neutral"])
        items.append(
            '<div style="border:1px solid #e2e8f0; border-radius:8px; padding:16px 18px; '
            'display:flex; gap:10px; align-items:flex-start;">\n'
            f'        <span style="color:{color}; font-size:14px; line-height:1.6;">●</span>\n'
            f'        <span style="font-size:13px; color:#374151; line-height:1.6;">{b.get("text", "")}</span>\n'
            '      </div>')
    return "\n      ".join(items)


def main():
    payload = json.load(sys.stdin)
    target = date.fromisoformat(payload["target_date"])
    d1 = target - timedelta(days=1)
    skeleton = bool(payload.get("skeleton"))
    currency = payload.get("currency") or "₩"
    modes = kit.Modes(payload.get("metric_keys"), payload.get("has_organic"))

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    status = {}

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
    if s2 and (s2.get("bullets") or s2.get("executive_summary")):
        status["s2"] = "ok"
        html = html.replace("__S2_ITEMS_HTML__", build_bullets(s2))
    else:
        status["s2"] = "placeholder"
        html = swap_section(html, "s2", PLACEHOLDER_CARD)

    # ── section 3 (스크립트 데이터는 섹션 유무와 무관하게 항상 유효한 JSON으로 치환 —
    #    placeholder일 땐 canvas가 없어 스크립트가 스스로 no-op 한다)
    s3 = section_data("s3")
    if s3 and (s3.get("cost") or s3.get("ad_cost") or s3.get("click")):
        status["s3"] = "ok"
        s3_spec = kit.perf_chart_spec(s3.get("labels") or build_s3_labels(target), s3, modes)
        s3_promos = build_promotions(s3.get("promotions"), target, s3_range_label)
        html = html.replace("__S3_FOOTNOTE_HTML__", "" if modes.has_revenue else S3_NO_REVENUE_NOTE)
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        s3_spec, s3_promos = None, []
    html = html.replace("__S3_CHART_SPEC_JSON__", kit.js_json(s3_spec))
    html = html.replace("__S3_PROMOTIONS_JSON__", kit.js_json(s3_promos))

    # ── section 4
    s4 = section_data("s4")
    if s4 and s4.get("series"):
        status["s4"] = "ok"
        s4_spec = kit.media_trend_spec(s4.get("labels") or build_s4_labels(target), s4["series"], modes)
        s4_promos = build_promotions(s4.get("promotions"), target, s4_range_label)
        html = html.replace("__S4_TITLE__", kit.media_trend_title(modes))
        html = html.replace("__S4_FOOTNOTE_HTML__", kit.media_trend_footnote(modes))
    else:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)
        s4_spec, s4_promos = None, []
    html = html.replace("__S4_CHART_SPEC_JSON__", kit.js_json(s4_spec))
    html = html.replace("__S4_PROMOTIONS_JSON__", kit.js_json(s4_promos))

    # ── section 5
    s5 = section_data("s5")
    if s5 and s5.get("rows"):
        status["s5"] = "ok"
        html = html.replace("__S5_THEAD_HTML__", kit.compare_thead_html(
            modes, f"{d1.month}/{d1.day}", f"{target.month}/{target.day}"))
        html = html.replace("__S5_ROWS_HTML__", kit.compare_rows_html(s5["rows"], modes, currency))
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", payload["title"])
    html = html.replace("__CURRENCY_JSON__", kit.js_json(currency))
    html = html.replace("__REPORT_DATE_LABEL__", f"{target.year}년 {target.month}월 {target.day}일 기준")
    html = (html.replace("__D1_MM__", str(d1.month)).replace("__D1_DD__", str(d1.day))
                .replace("__D0_MM__", str(target.month)).replace("__D0_DD__", str(target.day)))

    # ── 치환 누락 검증 (인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__S1_", "__S2_", "__S3_", "__S4_", "__S5_",
        "__CURRENCY", "__D1_", "__D0_",
    ] if t in html]
    if leftovers:
        raise SystemExit(f"치환 누락: {leftovers}")

    # ── 공용 킷·chart.js 인라인 (마지막 — 내용이 커서 치환 검증 후에 붙인다)
    html = kit.inline_assets(html)
    if not os.path.exists(CHART_JS):
        if os.path.exists(CHART_JS_FALLBACK):
            shutil.copyfile(CHART_JS_FALLBACK, CHART_JS)
        else:
            raise SystemExit(f"chart.umd.min.js 없음: {CHART_JS} (fallback도 없음: {CHART_JS_FALLBACK})")
    with open(CHART_JS, encoding="utf-8") as f:
        html = html.replace("__CHART_JS_INLINE__", f.read())

    out_path = os.path.abspath(os.path.expanduser(payload["out"]))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    json.dump({"out": out_path, "bytes": os.path.getsize(out_path),
               "mode": {"has_revenue": modes.has_revenue, "has_organic": modes.has_organic,
                        "has_conversion": modes.has_conversion},
               "sections": status}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
