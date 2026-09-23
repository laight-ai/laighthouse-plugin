#!/usr/bin/env python3
"""monthly-summary 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

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
  "out": "~/Downloads/laighthouse-reports/{브랜드명}_monthly-summary_2026-05-15.html",  # 필수
  "title": "{브랜드명} Executive 월간 보고서",                                          # 필수
  "target_date": "2026-05-15",                                                     # 필수
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
                             #        (실행 순서의 필수 체크포인트용. s1~s5는 무시된다)
  "metric_keys": {           # 역할 → 실제 지표 키 (discover.py 출력 그대로)
    "cost": "<cost 키>", "impression": "<impression 키>", "click": "<click 키>",
    "revenue": "<revenue 키>",       # 선택 — 없으면 "매출 없음 모드"(매출·ROAS → 노출·클릭·CTR·CPC)
    "conversion": "<conversion 키>"  # 선택 — 없으면 전환 컬럼 생략
  },
  "has_organic": true,       # discover.py 출력 그대로 (매출 없음 모드에선 무시)
  "currency": "₩",           # discover.py 출력 그대로, 기본 "₩"

  "s1": {                    # 목표 달성 현황 — 원본 숫자, 없으면 null (포맷·파생 비율은 킷이 계산)
    "목표_예산": 168110000, "소진액": 55700000,
    "목표_매출": null, "기간_매출": 123456789,          # 매출 있음 모드
    "기간_노출": 1234567, "기간_클릭": 23456            # 매출 없음 모드
  },
  "s2": {                    # Executive Summary — 불릿 카드 (4개 초과 시 앞 4개만 렌더링)
    "bullets": [{"text": "...<strong>+22.4%</strong>...", "tone": "up|down|neutral"}]
                             # tone: up(초록 ●) / down(빨강 ●) / neutral(회갈색 ●, 기본값)
                             # (대신 "executive_summary": "줄1\n줄2" 문자열도 허용 — 전부 neutral)
  },
  "s3": {                    # 월별 광고 성과 — 배열 6개(5개월 전 → 당월), 광고 매체 행(media non-null) 합
    "cost": [..], "revenue": [..],                  # 매출 있음
    "impression": [..], "click": [..],              # 매출 없음 (cost도 함께 — 툴팁·CPC용)
    "labels": [...]          # 선택 — 생략하면 "{YY}년 {M}월"(당월 "(진행 중)") 자동 생성
  },
  "s4": {                    # 매체별 추이 — 매출 있음: revenue 값, 매출 없음: click 값 (배열 6개)
    "series": [{"name": "<media 값 그대로>", "values": [..6개..]}, ...,
               {"name": "Organic", "values": [..]}]    # Organic은 has_organic일 때만
  },
  "s5": {                    # 매체 성과 비교 (M-1 vs M0) — 역할별 원본 수치
    "rows": [{"name": "<media 값>", "m1": {"cost":..,"impression":..,"click":..,"revenue":..,"conversion":..},
                                    "m0": {...}},
             {"name": "Organic", "m1": {"revenue":..,"conversion":..}, "m0": {...}}]
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
from datetime import date

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

PLACEHOLDER_CARD = '<div class="card"><p style="color:#94a3b8;font-size:13px;">데이터 준비 중</p></div>'
S3_NO_REVENUE_NOTE = ("<div>* 매출 지표가 없는 브랜드라 클릭·CTR 기준으로 표시합니다. 광고비·노출·CPC는 "
                      "막대에 마우스를 올리면 확인할 수 있습니다.</div>")
S3_ZERO_FILL = "<div>* 광고 데이터가 정상적으로 연동되지 않은 월은 0으로 표시되며, 제대로 표시되지 않을 수 있습니다.</div>"
S4_ZERO_FILL = "<div>* 데이터가 정상적으로 연동되지 않은 월은 0으로 표시되며, 제대로 표시되지 않을 수 있습니다.</div>"

# s2 불릿 앞머리 점(●) 색 — 성장/개선=초록, 하락/점검=빨강, 중립 관찰=회갈색
# (daily-summary의 green/red 표기도 같은 뜻으로 받는다)
TONE_COLORS = {"up": "#16a34a", "green": "#16a34a", "down": "#dc2626", "red": "#dc2626",
               "neutral": "#78716c"}
MAX_BULLETS = 4   # section-2 문서: 불릿은 항상 4개(a~d)


def swap_section(html, key, replacement):
    begin = f"<!--SECTION:{key}:BEGIN-->"
    end = f"<!--SECTION:{key}:END-->"
    i = html.index(begin)
    j = html.index(end) + len(end)
    return html[:i] + replacement + html[j:]


def month_add(y, m, delta):
    idx = (y * 12 + (m - 1)) + delta
    return idx // 12, idx % 12 + 1


def build_month_labels(target):
    """5개월 전 → 당월 순 6개 라벨. 당월에는 ' (진행 중)' 부착."""
    labels = []
    for i in range(-5, 1):
        y, m = month_add(target.year, target.month, i)
        label = f"{y % 100}년 {m}월"
        if i == 0:
            label += " (진행 중)"
        labels.append(label)
    return labels


def mtd_footnote(target):
    return (f"<div>* 이번달({target.year % 100}년 {target.month}월)의 데이터는 1일부터 기준일인 "
            f"{target.month}월 {target.day}일까지의 수치이며, 이전 달도 같은 일자까지로 잘라 비교합니다.</div>")


def has_zero_fill(*arrays):
    return any(v is None or v == 0 for arr in arrays if arr for v in arr)


def build_bullets(s2):
    """s2 입력(bullets 배열 또는 executive_summary 문자열) → 불릿 카드 HTML."""
    bullets = s2.get("bullets")
    if not bullets and s2.get("executive_summary"):
        bullets = [{"text": line.strip(), "tone": "neutral"}
                   for line in s2["executive_summary"].split("\n") if line.strip()]
    if not bullets:
        return None
    cards = []
    for b in bullets[:MAX_BULLETS]:  # 초과분은 버린다 — 모델이 a)~d) 순서로 넘긴다
        color = TONE_COLORS.get(b.get("tone", "neutral"), TONE_COLORS["neutral"])
        cards.append(
            '<div style="border:1px solid #e2e8f0; border-radius:8px; padding:16px 18px; '
            'display:flex; gap:10px; align-items:flex-start;">\n'
            f'        <span style="color:{color}; font-size:14px; line-height:1.6;">●</span>\n'
            f'        <span style="font-size:13px; color:#374151; line-height:1.6;">{b.get("text", "")}</span>\n'
            "      </div>")
    return "\n      ".join(cards)


def main():
    payload = json.load(sys.stdin)
    target = date.fromisoformat(payload["target_date"])
    m1_y, m1_m = month_add(target.year, target.month, -1)
    skeleton = bool(payload.get("skeleton"))
    currency = payload.get("currency") or "₩"
    modes = kit.Modes(payload.get("metric_keys"), payload.get("has_organic"))

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    status = {}

    def section_data(key):
        return None if skeleton else payload.get(key)

    labels = None

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
    bullets_html = build_bullets(s2) if s2 else None
    if bullets_html:
        status["s2"] = "ok"
        html = html.replace("__S2_BULLETS_HTML__", bullets_html)
    else:
        status["s2"] = "placeholder"
        html = swap_section(html, "s2", PLACEHOLDER_CARD)

    # ── section 3 (스크립트 데이터는 섹션 유무와 무관하게 항상 유효한 JSON으로 치환 —
    #    placeholder일 땐 canvas가 없어 스크립트가 스스로 no-op 한다)
    s3 = section_data("s3")
    if s3 and (s3.get("cost") or s3.get("ad_cost") or s3.get("click")):
        status["s3"] = "ok"
        labels = s3.get("labels") or build_month_labels(target)
        s3_spec = kit.perf_chart_spec(labels, s3, modes)
        scale = s3.get("revenue") if modes.has_revenue else s3.get("click")
        notes = [mtd_footnote(target)]
        if not modes.has_revenue:
            notes.append(S3_NO_REVENUE_NOTE)
        if has_zero_fill(s3.get("cost") or s3.get("ad_cost"), scale):
            notes.append(S3_ZERO_FILL)
        html = html.replace("__S3_FOOTNOTE_HTML__", "\n      ".join(notes))
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        s3_spec = None
    html = html.replace("__S3_CHART_SPEC_JSON__", kit.js_json(s3_spec))

    # ── section 4 (매체별 추이 누적 막대)
    s4 = section_data("s4")
    if s4 and s4.get("series"):
        status["s4"] = "ok"
        s4_labels = s4.get("labels") or labels or build_month_labels(target)
        s4_spec = kit.media_trend_spec(s4_labels, s4["series"], modes)
        totals = [sum((s["data"][i] or 0) for s in s4_spec["series"] if i < len(s["data"]))
                  for i in range(len(s4_labels))]
        notes = [mtd_footnote(target)]
        trend_note = kit.media_trend_footnote(modes)
        if trend_note:
            notes.append(trend_note)
        if has_zero_fill(totals):
            notes.append(S4_ZERO_FILL)
        html = html.replace("__S4_TITLE__", kit.media_trend_title(modes))
        html = html.replace("__S4_FOOTNOTE_HTML__", "\n      ".join(notes))
    else:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)
        s4_spec = None
    html = html.replace("__S4_CHART_SPEC_JSON__", kit.js_json(s4_spec))

    # ── section 5 (매체 성과 비교 — 컬럼은 모드별로 킷이 고른다)
    s5 = section_data("s5")
    if s5 and s5.get("rows"):
        status["s5"] = "ok"
        html = html.replace("__S5_THEAD_HTML__", kit.compare_thead_html(
            modes, f"{m1_y % 100}년 {m1_m}월", f"{target.year % 100}년 {target.month}월"))
        html = html.replace("__S5_ROWS_HTML__", kit.compare_rows_html(
            s5["rows"], modes, currency, base_key="m1", cur_key="m0"))
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", payload["title"])
    html = html.replace("__CURRENCY_JSON__", kit.js_json(currency))
    html = html.replace("__REPORT_DATE_LABEL__",
                        f"{target.year}년 {target.month}월 1일 ~ {target.month}월 {target.day}일")
    html = (html.replace("__M1_MM__", str(m1_m))
                .replace("__M0_MM__", str(target.month))
                .replace("__M0_YY__", str(target.year % 100)))

    # ── 치환 누락 검증 (인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__S1_", "__S2_", "__S3_", "__S4_", "__S5_",
        "__CURRENCY", "__M1_", "__M0_",
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
