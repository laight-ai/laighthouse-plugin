#!/usr/bin/env python3
"""monthly-summary 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

`assets/report-template.html`(섹션 1~5 마크업·스크립트가 전부 들어있는 단일 진실 공급원)에
값을 치환하고 `chart.umd.min.js`를 인라인해서 **최종 HTML 한 파일을 한 번의 호출로** 만든다.
모델은 HTML을 한 글자도 타이핑하지 않는다 — 아래 값 JSON만 heredoc으로 넘기면 된다.

사용법 (단 한 번의 Bash 호출, 응답을 받은 그 자리에서):
  python3 assets/build_report.py <<'PYEOF'
  { ...아래 입력 JSON... }
  PYEOF

입력 (stdin, JSON):
{
  "out": "~/Downloads/laighthouse-reports/브리즘_monthly-summary_2026-05-15.html",  # 필수
  "title": "브리즘 Executive 월간 보고서",                                          # 필수
  "target_date": "2026-05-15",                                                     # 필수
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
                             #        (실행 순서의 필수 체크포인트용. s1~s5는 무시된다)

  "s1": {                    # 목표 달성 현황 — 숫자(원본 수치) 또는 표시 문자열, 없으면 null
    "소진율": 33.13,          # 숫자면 % 소수점 1자리로 포맷, null이면 "N/A"
    "목표_예산": 168110000,   # 숫자면 ₩+천단위 콤마로 포맷
    "소진액": 55700000,
    "매출_달성률": null,
    "목표_매출": null,
    "기간_매출": 123456789,
    "실제_ROAS": 221.7,
    "목표_ROAS": null,
    "footnote": true          # 목표(예산/매출) 없는 매체가 하나라도 있으면 true → 고정 각주 표시
  },
  "s2": {                    # Executive Summary — 불릿 카드 (5개 초과 시 앞 5개만 렌더링)
    "bullets": [
      {"text": "Google Ads 매출이 전월 대비 <strong>+22.4%</strong> 성장...", "tone": "up"},
      {"text": "Meta Ads 매출이 전월 대비 -19.8% 감소...", "tone": "down"},
      {"text": "광고 매출 비중이 분기 단위로도 확대되는 추세...", "tone": "neutral"}
    ]                          # tone: "up"(초록 ●) / "down"(빨강 ●) / "neutral"(회갈색 ●, 기본값)
                               # (대신 "executive_summary": "줄1\n줄2" 문자열도 허용 — 전부 neutral)
  },
  "s3": {                    # 월별 광고 성과 — 배열은 전부 6개(5개월 전 → 당월 순)
    "ad_cost": [..6개..], "revenue": [..6개..], "roas": [..6개, 광고비 0인 달은 null..],
    "labels": ["26년 3월", ...]   # 선택 — 생략하면 target_date 기준 "{YY}년 {M}월" 자동 생성
                                  #        (당월에는 " (진행 중)" 자동 부착)
  },
  "s4": {                    # 매출 추이 — 배열은 전부 6개(5개월 전 → 당월 순)
    "ad_revenue": [..6개..], "total_revenue": [..6개..],
    "labels": [...]               # 선택 — s3과 동일한 규칙으로 자동 생성
  },
  "s5": {                    # 매체 성과 비교 (M-1 vs M0) — 5개 항목 고정, 순서 무관
    "rows": [                # (빌더가 M0 매출 내림차순 정렬·ROAS/변화량/화살표/색상 계산)
      {"name": "Naver Ads",
       "m1": {"cost": 1000000, "revenue": 50000000, "reservation": 120},
       "m0": {"cost": 1100000, "revenue": 52000000, "reservation": 130}},
      {"name": "Organic",
       "m1": {"cost": null, "revenue": 30000000, "reservation": 80},   # 광고비 개념 없는 항목은
       "m0": {"cost": null, "revenue": 28000000, "reservation": 75}}   # cost: null → "-" 표시
    ]
  }
}

- s1~s5 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
- s5의 ROAS는 빌더가 계산한다(매출 ÷ 광고비 × 100, 광고비 null/0이면 "-").
- 출력(stdout): {"out": 절대경로, "bytes": 크기, "sections": {"s1": "ok"|"placeholder", ...}}
"""
import io
import json
import os
import sys
from datetime import date

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(ASSETS_DIR, "report-template.html")
CHART_JS = os.path.join(ASSETS_DIR, "chart.umd.min.js")

PLACEHOLDER_CARD = '<div class="card"><p style="color:#94a3b8;font-size:13px;">데이터 준비 중</p></div>'
S1_FOOTNOTE = ('<p style="font-size:11px; color:#94a3b8; margin-top:8px;">'
               "* 매체별 예산 및 목표 매출이 등록되지 않은 경우, 현황이 제대로 표시되지 않을 수 있습니다.</p>")
S3_ZERO_FILL = "* 광고비 또는 매출 데이터가 정상적으로 연동되지 않은 경우, 제대로 표시되지 않을 수 있습니다."
S4_ZERO_FILL = "* 매출 데이터가 정상적으로 연동되지 않은 경우, 제대로 표시되지 않을 수 있습니다."

MONEY_FIELDS = {"목표_예산", "소진액", "목표_매출", "기간_매출"}
PCT_FIELDS = {"소진율", "매출_달성률", "실제_ROAS", "목표_ROAS"}

# s2 불릿 앞머리 점(●) 색 — 성장/개선=초록, 하락/점검=빨강, 중립 관찰=회갈색
TONE_COLORS = {"up": "#16a34a", "down": "#dc2626", "neutral": "#78716c"}

# s5 변화량 색 — 네 지표 전부 "증가=빨강/감소=파랑/무변화(표시값 0.0)=검정"
DELTA_UP = "#dc2626"
DELTA_DOWN = "#2563eb"
DELTA_ZERO = "#1e293b"


def fmt_won(v):
    return f"₩{round(v):,}"


def fmt_pct(v):
    return f"{v:.1f}%"


def fmt_value(field, v):
    """숫자면 필드 종류에 맞게 포맷, 문자열이면 그대로, None이면 N/A."""
    if v is None:
        return "N/A"
    if isinstance(v, str):
        return v
    if field in MONEY_FIELDS:
        return fmt_won(v)
    if field in PCT_FIELDS:
        return fmt_pct(v)
    return str(v)


def js_json(value):
    """<script> 안에 삽입할 JSON — </script> 조기 종료 방지."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


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
    return (f"* 이번달({target.year % 100}년 {target.month}월)의 데이터는 1일부터 기준일인 "
            f"{target.month}월 {target.day}일까지의 수치입니다.")


def has_zero_fill(*arrays):
    return any(v is None or v == 0 for arr in arrays for v in (arr or []))


def build_bullets(s2):
    """s2 입력(bullets 배열 또는 executive_summary 문자열) → 불릿 카드 HTML."""
    bullets = s2.get("bullets")
    if not bullets and s2.get("executive_summary"):
        bullets = [{"text": line.strip(), "tone": "neutral"}
                   for line in s2["executive_summary"].split("\n") if line.strip()]
    if not bullets:
        return None
    cards = []
    for b in bullets[:5]:  # 5개 초과면 상위(앞) 5개만 — 모델이 임팩트 순으로 정렬해 넘긴다
        color = b.get("color") or TONE_COLORS.get(b.get("tone", "neutral"), TONE_COLORS["neutral"])
        cards.append(
            '<div style="border:1px solid #e2e8f0; border-radius:8px; padding:16px 18px; '
            'display:flex; gap:10px; align-items:flex-start;">\n'
            f'        <span style="color:{color}; font-size:14px; line-height:1.6;">●</span>\n'
            f'        <span style="font-size:13px; color:#374151; line-height:1.6;">{b.get("text", "")}</span>\n'
            "      </div>")
    return "\n      ".join(cards)


# ── s5: 매체 성과 비교 표 ──────────────────────────────────────────────────

def roas_of(month):
    cost = month.get("cost")
    revenue = month.get("revenue")
    if cost is None or not cost or revenue is None:
        return None
    return revenue / cost * 100


def fmt_s5(kind, v):
    if v is None:
        return "-"
    if kind == "money":
        return fmt_won(v)
    if kind == "int":
        return f"{round(v):,}"
    return fmt_pct(v)  # roas


def delta_html(m1, m0, unit):
    """M0 값 아래 변화량 div. unit '%'=상대 변화율, '%p'=포인트 차. 계산 불가면 ''."""
    if m1 is None or m0 is None:
        return ""
    if unit == "%":
        if not m1:
            return ""
        raw = (m0 - m1) / m1 * 100
    else:
        raw = m0 - m1
    shown = round(raw, 1)
    if shown == 0:
        color, label = DELTA_ZERO, f"0.0{unit}"
    else:
        color = DELTA_UP if shown > 0 else DELTA_DOWN
        arrow = "▲" if raw > 0 else "▼"
        label = f"{arrow} {'+' if shown > 0 else ''}{shown:.1f}{unit}"
    return (f'\n            <div style="font-size:10.5px; text-align:center; '
            f'color:{color};">({label})</div>')


def build_s5_rows(rows):
    """rows(5개 항목) → M0 매출 내림차순 정렬 + ROAS/변화량 계산 + <tr> HTML."""
    def m0_revenue(r):
        v = r.get("m0", {}).get("revenue")
        return v if isinstance(v, (int, float)) else float("-inf")

    out = []
    for r in sorted(rows, key=m0_revenue, reverse=True):
        m1, m0 = r.get("m1", {}), r.get("m0", {})
        m1_roas, m0_roas = roas_of(m1), roas_of(m0)
        cells = [
            f'<td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{r.get("name", "")}</td>',
            f'<td style="white-space:nowrap; text-align:center;">{fmt_s5("money", m1.get("cost"))}</td>',
            ('<td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">'
             f'{fmt_s5("money", m0.get("cost"))}{delta_html(m1.get("cost"), m0.get("cost"), "%")}'
             "</td>"),
            f'<td style="white-space:nowrap; text-align:center;">{fmt_s5("money", m1.get("revenue"))}</td>',
            ('<td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">'
             f'{fmt_s5("money", m0.get("revenue"))}{delta_html(m1.get("revenue"), m0.get("revenue"), "%")}'
             "</td>"),
            f'<td style="white-space:nowrap; text-align:center;">{fmt_s5("int", m1.get("reservation"))}</td>',
            ('<td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">'
             f'{fmt_s5("int", m0.get("reservation"))}{delta_html(m1.get("reservation"), m0.get("reservation"), "%")}'
             "</td>"),
            f'<td style="white-space:nowrap; text-align:center;">{fmt_s5("roas", m1_roas)}</td>',
            ('<td style="white-space:nowrap; text-align:center;">'
             f'{fmt_s5("roas", m0_roas)}{delta_html(m1_roas, m0_roas, "%p")}'
             "</td>"),
        ]
        out.append("<tr>\n          " + "\n          ".join(cells) + "\n        </tr>")
    return "\n        ".join(out)


def main():
    payload = json.load(sys.stdin)
    target = date.fromisoformat(payload["target_date"])
    m1_y, m1_m = month_add(target.year, target.month, -1)
    skeleton = bool(payload.get("skeleton"))

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    status = {}

    def section_data(key):
        return None if skeleton else payload.get(key)

    # ── section 1
    s1 = section_data("s1")
    if s1:
        status["s1"] = "ok"
        for field in ["소진율", "목표_예산", "소진액", "매출_달성률", "목표_매출", "기간_매출", "실제_ROAS", "목표_ROAS"]:
            html = html.replace(f"__S1_{field}__", fmt_value(field, s1.get(field)))
        html = html.replace("__S1_MM__", str(target.month)).replace("__S1_DD__", str(target.day))
        html = html.replace("__S1_FOOTNOTE_HTML__", S1_FOOTNOTE if s1.get("footnote") else "")
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
    if s3 and s3.get("ad_cost"):
        status["s3"] = "ok"
        s3_chart = {
            "labels": s3.get("labels") or build_month_labels(target),
            "ad_cost": s3["ad_cost"],
            "revenue": s3.get("revenue", []),
            "roas": s3.get("roas", []),
        }
        html = html.replace("__S3_FOOTNOTE_CURRENT_MONTH__", mtd_footnote(target))
        html = html.replace("__S3_FOOTNOTE_ZERO_FILL__",
                            S3_ZERO_FILL if has_zero_fill(s3["ad_cost"], s3.get("revenue")) else "")
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        s3_chart = {"labels": [], "ad_cost": [], "revenue": [], "roas": []}
    html = html.replace("__S3_CHART_DATA_JSON__", js_json(s3_chart))

    # ── section 4
    s4 = section_data("s4")
    if s4 and (s4.get("ad_revenue") or s4.get("total_revenue")):
        status["s4"] = "ok"
        s4_chart = {
            "labels": s4.get("labels") or build_month_labels(target),
            "ad_revenue": s4.get("ad_revenue", []),
            "total_revenue": s4.get("total_revenue", []),
        }
        html = html.replace("__S4_FOOTNOTE_MTD__", mtd_footnote(target))
        html = html.replace("__S4_FOOTNOTE_ZERO_FILL__",
                            S4_ZERO_FILL if has_zero_fill(s4.get("ad_revenue"), s4.get("total_revenue")) else "")
    else:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)
        s4_chart = {"labels": [], "ad_revenue": [], "total_revenue": []}
    html = html.replace("__S4_CHART_DATA_JSON__", js_json(s4_chart))

    # ── section 5
    s5 = section_data("s5")
    if s5 and s5.get("rows"):
        status["s5"] = "ok"
        html = html.replace("__S5_ROWS_HTML__", build_s5_rows(s5["rows"]))
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", payload["title"])
    html = html.replace("__REPORT_DATE_LABEL__",
                        f"{target.year}년 {target.month}월 1일 ~ {target.month}월 {target.day}일")
    html = (html.replace("__M1_MM__", str(m1_m))
                .replace("__M0_MM__", str(target.month))
                .replace("__M0_YY__", str(target.year % 100)))

    # ── 치환 누락 검증 (chart.js 인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__S1_", "__S2_BULLETS_HTML__",
        "__S3_", "__S4_", "__S5_ROWS_HTML__", "__M1_", "__M0_",
    ] if t in html]
    if leftovers:
        raise SystemExit(f"치환 누락: {leftovers}")

    # ── chart.js 인라인 (마지막 — 내용이 커서 치환 검증 후에 붙인다)
    with open(CHART_JS, encoding="utf-8") as f:
        html = html.replace("__CHART_JS_INLINE__", f.read())

    out_path = os.path.abspath(os.path.expanduser(payload["out"]))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    json.dump({"out": out_path, "bytes": os.path.getsize(out_path), "sections": status},
              sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
