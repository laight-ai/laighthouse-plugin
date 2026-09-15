#!/usr/bin/env python3
"""mtd-summary 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

`assets/report-template.html`(섹션 1~5 마크업·스크립트가 전부 들어있는 단일 진실 공급원)에
값을 치환하고 `chart.umd.min.js`를 인라인해서 **최종 HTML 한 파일을 한 번의 호출로** 만든다.
모델은 HTML을 한 글자도 타이핑하지 않는다 — 아래 값 JSON만 heredoc으로 넘기면 된다.

사용법 (단 한 번의 Bash 호출, 응답을 받은 그 자리에서):
  python3 assets/build_report.py <<'PYEOF'
  { ...아래 입력 JSON... }
  PYEOF

입력 (stdin, JSON):
{
  "out": "~/Downloads/laighthouse-reports/{브랜드명}_mtd-summary_2026-05-15.html",  # 필수
  "title": "{브랜드명} Executive MTD 보고서",                                        # 필수
  "target_date": "2026-05-15",                                                  # 필수
  "skeleton": true,          # 선택 — true면 모든 섹션을 "데이터 준비 중"으로 채운 스켈레톤 생성
                             #        (실행 순서의 필수 체크포인트용. s1~s5는 무시된다)
  "metric_keys": {           # 역할 → 실제 지표 키 (shared/references/generic-report-pattern.md 3절)
    "cost": "광고비", "impression": "노출", "click": "클릭", "revenue": "매출_AB",
    "conversion": "예약완료_AB"   # 선택 — 없으면 section-5의 전환 컬럼을 숨긴다
  },                         # <th> 라벨에 그대로 쓴다. 생략 시 cost="광고비", revenue="매출"
  "currency": "₩",           # 선택 — 금액 접두 기호, 기본 "₩" (템플릿 JS 포맷터에도 주입)

  "s1": {                    # 목표 달성 현황 — 숫자(원본 수치) 또는 표시 문자열, 없으면 null
    "소진율": 33.13,          # 숫자면 % 소수점 1자리로 포맷, null이면 "N/A"
    "목표_예산": 168110000,   # 숫자면 통화기호+천단위 콤마로 포맷
    "소진액": 55700000,
    "매출_달성률": null,
    "목표_매출": null,
    "기간_매출": 123456789,
    "실제_ROAS": 221.7,
    "목표_ROAS": null,
    "footnote": true          # 목표(예산/매출) 없는 매체가 하나라도 있으면 true → 고정 각주 표시
  },
  "s2": {                    # Executive Summary — 불릿 카드 3~5개 (6개 이상이면 앞 5개만 사용)
    "bullets": [
      {"text": "Kakao 매출이 전월 대비 <strong>+22.4%</strong> 성장...", "color": "green"},
      {"text": "TikTok 매출이 전월 대비 -19.8% 감소...", "color": "red"},
      {"text": "브랜딩 캠페인 이월 영향 가능성...", "color": "neutral"}
    ]                         # color: "green"(성장/개선) | "red"(하락/점검) | "neutral"(중립 관찰)
                              # ("executive_summary": "줄1\n줄2" 문자열도 허용 — 전부 neutral 처리)
  },
  "s3": {                    # 월별 광고 성과 — 배열은 전부 6개(5개월 전 → 당월 순)
    "ad_cost": [..6개..], "revenue": [..6개..], "roas": [..6개, 광고비 0인 달은 null..],
    "labels": ["26년 3월", ...],  # 선택 — 생략하면 target_date 기준 "YY년 M월"(당월은 " (진행 중)") 자동 생성
    "zero_fill": true             # 선택 — 생략하면 ad_cost/revenue에 0이 있는지로 자동 판정
  },                              #        (0으로 채워진 월 있음 → 고정 각주 표시)
  "s4": {                    # 매출 추이 — 배열은 전부 6개(5개월 전 → 당월 순)
    "ad_revenue": [..6개..], "total_revenue": [..6개..],
    "labels": [...], "zero_fill": true   # 둘 다 선택 — 규칙은 s3과 동일
  },
  "s5": {                    # 매체 성과 비교 (M-1 vs M0) — 매체별 원본 수치만 넘기면 ROAS·변화량·
    "rows": [                # 화살표·색상·행 HTML 생성을 전부 빌더가 한다
      {"name": "Kakao",
       "m1": {"cost": 5000000, "revenue": 251835000, "conversion": 120},
       "m0": {"cost": 5100000, "revenue": 260000000, "conversion": 128}},
      {"name": "TikTok",  "m1": {...}, "m0": {...}},
      {"name": "Organic", "m1": {"revenue": 90000000, "conversion": 40}, "m0": {...}}  # cost 없음 → "-"
    ]                         # 디스커버리된 매체(응답 값 그대로) + Organic(있을 때만), 받은 순서대로 렌더링.
  }                           # 값 키는 역할명(cost/revenue/conversion) — metric_keys에 conversion이 없으면 생략.
                              # 값이 없으면 키 생략 또는 null → "-".
}

- s1~s5 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
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

DOT_COLORS = {"green": "#16a34a", "red": "#dc2626", "neutral": "#78716c"}

S5_TH_GROUP = ('<th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; '
               'padding-top:8px; padding-bottom:8px; vertical-align:middle;{border}">{label}</th>')
S5_TH_MONTH = ('<th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; '
               'padding-top:8px; padding-bottom:8px; vertical-align:middle;{border}">{label}</th>')
S5_TH_BORDER = " border-right:1px solid #e2e8f0;"

DEFAULT_METRIC_LABELS = {"cost": "광고비", "revenue": "매출"}
CURRENCY = "₩"


def fmt_won(v):
    return f"{CURRENCY}{round(v):,}"


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


def shift_month(y, m, delta):
    """(y, m)에서 delta개월 이동한 (y, m)."""
    idx = y * 12 + (m - 1) + delta
    return idx // 12, idx % 12 + 1


def build_month_labels(target):
    """5개월 전 → 당월, 'YY년 M월' 6개 (당월은 ' (진행 중)' 접미)."""
    labels = []
    for i in range(-5, 1):
        y, m = shift_month(target.year, target.month, i)
        label = f"{y % 100}년 {m}월"
        if i == 0:
            label += " (진행 중)"
        labels.append(label)
    return labels


def build_summary_items(s2):
    """불릿 카드 HTML — {bullets:[{text,color}]} 또는 {executive_summary:"줄\n줄"}."""
    bullets = s2.get("bullets")
    if bullets is None:
        bullets = [{"text": line.strip(), "color": "neutral"}
                   for line in (s2.get("executive_summary") or "").split("\n") if line.strip()]
    cards = []
    for b in bullets[:5]:  # 임원 보고 — 5개 초과분은 잘라낸다(모델이 이미 상위 5개만 고르는 게 원칙)
        color = b.get("color", "neutral")
        color = DOT_COLORS.get(color, color if str(color).startswith("#") else DOT_COLORS["neutral"])
        cards.append(
            '<div style="border:1px solid #e2e8f0; border-radius:8px; padding:16px 18px; '
            'display:flex; gap:10px; align-items:flex-start;">\n'
            f'        <span style="color:{color}; font-size:14px; line-height:1.6;">●</span>\n'
            f'        <span style="font-size:13px; color:#374151; line-height:1.6;">{b.get("text", "")}</span>\n'
            "      </div>"
        )
    return "\n      ".join(cards)


def has_zero_fill(section, keys):
    """zero_fill 명시가 없으면 배열에 0이 있는지로 자동 판정."""
    if "zero_fill" in section:
        return bool(section["zero_fill"])
    return any(v == 0 for k in keys for v in (section.get(k) or []))


# ── section 5: 값 포맷·변화량·행 HTML ──────────────────────────────────────

def s5_fmt(kind, v):
    if v is None:
        return "-"
    if kind == "money":
        return fmt_won(v)
    if kind == "count":
        return f"{round(v):,}"
    return fmt_pct(v)  # roas


def s5_delta(m0, m1, suffix):
    """M-1 대비 변화량 div HTML — 계산 불가면 빈 문자열.
    광고비/매출/전환은 상대 변화율(%), ROAS는 %p. 색상·화살표는 반올림된 표시값 기준
    (표시값 0.0이면 검정·화살표 없음 — 원본이 미세하게 ±여도 동일)."""
    if m0 is None or m1 is None:
        return ""
    if suffix == "%p":
        raw = m0 - m1
    else:
        if m1 == 0:
            return ""
        raw = (m0 - m1) / m1 * 100
    disp = round(raw, 1)
    if disp == 0:
        color, label = "#1e293b", f"(0.0{suffix})"
    elif disp > 0:
        color, label = "#dc2626", f"(▲ +{disp:.1f}{suffix})"
    else:
        color, label = "#2563eb", f"(▼ {disp:.1f}{suffix})"
    return f'\n            <div style="font-size:10.5px; text-align:center; color:{color};">{label}</div>'


def build_s5_thead(metric_keys, m1_label, m0_label):
    """metric_keys의 역할 라벨로 section-5 <thead> 생성. conversion 역할이 없으면 그 컬럼 생략."""
    groups = [metric_keys.get("cost") or DEFAULT_METRIC_LABELS["cost"],
              metric_keys.get("revenue") or DEFAULT_METRIC_LABELS["revenue"]]
    if metric_keys.get("conversion"):
        groups.append(metric_keys["conversion"])
    groups.append("ROAS")
    row1 = ['<th rowspan="2" style="white-space:nowrap; text-align:center; vertical-align:middle;'
            f'{S5_TH_BORDER}">매체</th>']
    row2 = []
    for i, label in enumerate(groups):
        last = i == len(groups) - 1
        row1.append(S5_TH_GROUP.format(label=label, border="" if last else S5_TH_BORDER))
        row2.append(S5_TH_MONTH.format(label=m1_label, border=""))
        row2.append(S5_TH_MONTH.format(label=m0_label, border="" if last else S5_TH_BORDER))
    sep = "\n            "
    return ("<tr>" + sep + sep.join(row1) + "\n          </tr>\n          <tr>" + sep
            + sep.join(row2) + "\n          </tr>")


def _num(d, key):
    v = (d or {}).get(key)
    return v if isinstance(v, (int, float)) else None


def build_s5_rows(rows, has_conversion):
    """매체별 원본 수치 → ROAS 계산·변화량·<tr> HTML. 행은 입력 순서 그대로."""
    out = []
    for r in rows:
        m1, m0 = r.get("m1") or {}, r.get("m0") or {}
        m1c, m0c = _num(m1, "cost"), _num(m0, "cost")
        m1r, m0r = _num(m1, "revenue"), _num(m0, "revenue")
        m1b, m0b = _num(m1, "conversion"), _num(m0, "conversion")
        m1roas = (m1r / m1c * 100) if (m1c not in (None, 0) and m1r is not None) else None
        m0roas = (m0r / m0c * 100) if (m0c not in (None, 0) and m0r is not None) else None
        cells = [
            f'<td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{r.get("name", "")}</td>',
            f'<td style="white-space:nowrap; text-align:center;">{s5_fmt("money", m1c)}</td>',
            f'<td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">{s5_fmt("money", m0c)}{s5_delta(m0c, m1c, "%")}</td>',
            f'<td style="white-space:nowrap; text-align:center;">{s5_fmt("money", m1r)}</td>',
            f'<td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">{s5_fmt("money", m0r)}{s5_delta(m0r, m1r, "%")}</td>',
        ]
        if has_conversion:
            cells += [
                f'<td style="white-space:nowrap; text-align:center;">{s5_fmt("count", m1b)}</td>',
                f'<td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">{s5_fmt("count", m0b)}{s5_delta(m0b, m1b, "%")}</td>',
            ]
        cells += [
            f'<td style="white-space:nowrap; text-align:center;">{s5_fmt("roas", m1roas)}</td>',
            f'<td style="white-space:nowrap; text-align:center;">{s5_fmt("roas", m0roas)}{s5_delta(m0roas, m1roas, "%p")}</td>',
        ]
        out.append("<tr>\n            " + "\n            ".join(cells) + "\n          </tr>")
    return "\n          ".join(out)


def main():
    global CURRENCY
    payload = json.load(sys.stdin)
    target = date.fromisoformat(payload["target_date"])
    m1_y, m1_m = shift_month(target.year, target.month, -1)
    skeleton = bool(payload.get("skeleton"))
    metric_keys = payload.get("metric_keys") or {}
    CURRENCY = payload.get("currency") or CURRENCY

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    status = {}

    def section_data(key):
        return None if skeleton else payload.get(key)

    mtd_footnote = (f"* 이번달({target.year % 100}년 {target.month}월)의 데이터는 1일부터 "
                    f"기준일인 {target.month}월 {target.day}일까지의 수치입니다.")

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
    if s2 and (s2.get("bullets") or s2.get("executive_summary")):
        status["s2"] = "ok"
        html = html.replace("__S2_ITEMS_HTML__", build_summary_items(s2))
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
        html = html.replace("__S3_FOOTNOTE_CURRENT_MONTH__", mtd_footnote)
        html = html.replace("__S3_FOOTNOTE_ZERO_FILL_HTML__",
                            f"<div>{S3_ZERO_FILL}</div>" if has_zero_fill(s3, ("ad_cost", "revenue")) else "")
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        s3_chart = {"labels": [], "ad_cost": [], "revenue": [], "roas": []}
    html = html.replace("__S3_CHART_DATA_JSON__", js_json(s3_chart))

    # ── section 4
    s4 = section_data("s4")
    if s4 and s4.get("total_revenue"):
        status["s4"] = "ok"
        s4_chart = {
            "labels": s4.get("labels") or build_month_labels(target),
            "ad_revenue": s4.get("ad_revenue", []),
            "total_revenue": s4["total_revenue"],
        }
        html = html.replace("__S4_FOOTNOTE_MTD__", mtd_footnote)
        html = html.replace("__S4_FOOTNOTE_ZERO_FILL_HTML__",
                            f"<div>{S4_ZERO_FILL}</div>" if has_zero_fill(s4, ("ad_revenue", "total_revenue")) else "")
    else:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)
        s4_chart = {"labels": [], "ad_revenue": [], "total_revenue": []}
    html = html.replace("__S4_CHART_DATA_JSON__", js_json(s4_chart))

    # ── section 5
    s5 = section_data("s5")
    if s5 and s5.get("rows"):
        status["s5"] = "ok"
        html = html.replace("__S5_THEAD_HTML__", build_s5_thead(metric_keys, f"{m1_m}월", f"{target.month}월"))
        html = html.replace("__S5_ROWS_HTML__", build_s5_rows(s5["rows"], bool(metric_keys.get("conversion"))))
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", payload["title"])
    html = html.replace("__CURRENCY__", CURRENCY)
    html = html.replace("__REPORT_DATE_LABEL__",
                        f"{target.year}년 {target.month}월 1일 ~ {target.month}월 {target.day}일")
    html = (html.replace("__M1_YY__", str(m1_y % 100)).replace("__M1_MM__", str(m1_m))
                .replace("__M0_YY__", str(target.year % 100)).replace("__M0_MM__", str(target.month))
                .replace("__TD_DD__", str(target.day)))

    # ── 치환 누락 검증 (chart.js 인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__S1_", "__S2_ITEMS_HTML__",
        "__S3_", "__S4_", "__S5_THEAD_HTML__", "__S5_ROWS_HTML__", "__CURRENCY__",
        "__M1_", "__M0_", "__TD_DD__",
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
