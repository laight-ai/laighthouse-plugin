#!/usr/bin/env python3
"""monthly-detailed 최종 보고서 조립기 — 미리 검증된 asset 스크립트.

`assets/report-template.html`(섹션 1~5 마크업·스크립트가 전부 들어있는 단일 진실 공급원)에
값을 치환하고 `chart.umd.min.js`를 인라인해서 **최종 HTML 한 파일을 한 번의 호출로** 만든다.
모델은 HTML을 한 글자도 타이핑하지 않는다 — 아래 값 JSON만 heredoc으로 넘기면 된다.

사용법 (단 한 번의 Bash 호출, 응답을 받은 그 자리에서):
  python3 assets/build_report.py <<'PYEOF'
  { ...아래 입력 JSON... }
  PYEOF

입력 (stdin, JSON):
{
  "out": "~/Downloads/laighthouse-reports/브리즘_monthly-detailed_2026-07-31.html",  # 필수
  "title": "브리즘 월간 보고서",                                                     # 필수
  "target_date": "2026-07-31",                                                      # 필수 (M0 기준일)
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
  "s2": { "executive_summary": "문장1\n문장2\n⚠ 주의 문장..." },  # \n 구분, ⚠ 시작 줄은 주황색
  "s3": {                    # 월별 광고 성과 — 배열은 전부 6개(5개월 전 → 당월 순)
    "ad_cost": [..6개..], "revenue": [..6개..], "roas": [..6개, 광고비 0인 달은 null..],
    "labels": ["26년 3월", ...],  # 선택 — 생략하면 target_date 기준 "{YY}년 {M}월" 자동 생성
                                  #        (당월은 " (진행 중)" 접미사까지 자동)
    "zero_fill": true             # 선택 — 생략하면 ad_cost/revenue에 0이 있는지로 자동 판정
  },                              #        (0으로 채워진 월이 있으면 고정 각주 두 번째 줄 표시)
  "s4": {                    # 매체 성과 비교 (M-1 vs M0) — 5개 항목의 월별 원본 수치.
    "channels": [            # 파생지표(CTR/CPA/ROAS)·변화량·화살표·색상·M0 매출 내림차순 정렬은
      {                      # 빌더가 계산한다. 그 달에 데이터가 아예 없으면 해당 월을 null로.
        "name": "Naver Ads", # Naver Ads/Google Ads/Meta Ads/Organic/Others 5개 고정
        "m1": {"cost": 100000, "impression": 5000, "click": 50, "revenue": 900000, "reservation": 3},
        "m0": {"cost": 120000, "impression": 6000, "click": 66, "revenue": 800000, "reservation": 2}
      },                     # Organic/Others는 광고비 개념이 없으므로 cost/impression/click을
      ...                    # 아예 넣지 않는다(→ 광고비/CTR/CPA/ROAS 전부 "-").
    ]
  },
  "s5": { "rows_file": "/tmp/s5.json" }   # monthly_campaign_rows.py 출력 파일 경로
                                          # (파일 대신 "rows": [...] 직접 전달도 허용)
}

- s1~s5 중 키 자체가 없거나 null인 섹션은 "데이터 준비 중" 카드로 렌더링된다(섹션 생략 없음).
- 출력(stdout): {"out": 절대경로, "bytes": 크기, "sections": {"s1": "ok"|"placeholder", ...}}
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
# 스킬 폴더에 chart.umd.min.js가 없으면 자매 스킬 daily-detailed의 동일 자산을 1회 복사해 쓴다.
CHART_JS_FALLBACK = os.path.join(
    os.path.dirname(os.path.dirname(ASSETS_DIR)), "daily-detailed", "assets", "chart.umd.min.js")

PLACEHOLDER_CARD = '<div class="card"><p style="color:#94a3b8;font-size:13px;">데이터 준비 중</p></div>'
S1_FOOTNOTE = ('<p style="font-size:11px; color:#94a3b8; margin-top:8px;">'
               "* 매체별 예산 및 목표 매출이 등록되지 않은 경우, 현황이 제대로 표시되지 않을 수 있습니다.</p>")
S3_ZERO_FILL_FOOTNOTE = "<div>* 광고비 또는 매출 데이터가 정상적으로 연동되지 않은 경우, 제대로 표시되지 않을 수 있습니다.</div>"

MONEY_FIELDS = {"목표_예산", "소진액", "목표_매출", "기간_매출"}
PCT_FIELDS = {"소진율", "매출_달성률", "실제_ROAS", "목표_ROAS"}

S4_CHANNELS = ["Naver Ads", "Google Ads", "Meta Ads", "Organic", "Others"]
# 각 지표의 색상 규칙: True면 "증가=빨강(긍정)", False면 "감소=빨강(긍정)" (CPA만 False)
POSITIVE_ON_INCREASE = {"cost": True, "ctr": True, "reservation": True,
                        "cpa": False, "revenue": True, "roas": True}
METRIC_ORDER = [("cost", "%"), ("ctr", "%p"), ("reservation", "%"),
                ("cpa", "%"), ("revenue", "%"), ("roas", "%p")]


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


def month_shift(y, m, delta):
    total = y * 12 + (m - 1) + delta
    return total // 12, total % 12 + 1


def build_month_labels(target):
    """5개월 전 → 당월, "{YY}년 {M}월" (당월은 " (진행 중)")."""
    labels = []
    for i in range(-5, 1):
        y, m = month_shift(target.year, target.month, i)
        label = f"{y % 100}년 {m}월"
        if i == 0:
            label += " (진행 중)"
        labels.append(label)
    return labels


def build_summary_items(text):
    items = []
    for line in (text or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        style = ' style="color:#d97706;"' if line.startswith("⚠") else ""
        items.append(f"<li{style}>{line}</li>")
    return "\n      ".join(items)


# ── section 4: 매체 성과 비교 (M-1 vs M0) — 파생지표·변화량·색상·정렬·행 HTML 생성 ──

def s4_compute(md):
    """월별 원본 수치 dict(또는 None) → (raw, disp) 6개 지표.
    cost가 없으면(Organic/Others 또는 그 달 데이터 없음) 광고비/CTR/CPA/ROAS는 "-"."""
    raw = {k: None for k, _ in METRIC_ORDER}
    disp = {k: "-" for k, _ in METRIC_ORDER}
    if md is None:
        return raw, disp
    cost = md.get("cost")
    revenue = md.get("revenue")
    reservation = md.get("reservation")
    if cost is not None:
        raw["cost"] = cost
        disp["cost"] = fmt_won(cost)
        impression = md.get("impression") or 0
        click = md.get("click") or 0
        if impression:
            raw["ctr"] = click / impression * 100
            disp["ctr"] = fmt_pct(raw["ctr"])
        else:
            disp["ctr"] = "N/A"
    if revenue is not None:
        raw["revenue"] = revenue
        disp["revenue"] = fmt_won(revenue)
    if reservation is not None:
        raw["reservation"] = reservation
        disp["reservation"] = str(int(reservation))
    if cost is not None and reservation is not None:
        if reservation:
            raw["cpa"] = cost / reservation
            disp["cpa"] = fmt_won(raw["cpa"])
        else:
            disp["cpa"] = "N/A"
    if cost is not None and revenue is not None:
        if cost:
            raw["roas"] = revenue / cost * 100
            disp["roas"] = fmt_pct(raw["roas"])
        else:
            disp["roas"] = "N/A"
    return raw, disp


def delta_relative(m0, m1):
    """% 변화 (광고비/예약 완료/CPA/매출): m0 없거나 m1이 없거나 0이면 비교 불가(None)."""
    if m0 is None or m1 in (None, 0):
        return None
    return (m0 - m1) / m1 * 100


def delta_point(m0, m1):
    """%p 변화 (CTR/ROAS): m0 또는 m1이 None이면 비교 불가(None). 0은 유효한 값."""
    if m0 is None or m1 is None:
        return None
    return m0 - m1


DELTA_FN = {"cost": delta_relative, "ctr": delta_point, "reservation": delta_relative,
            "cpa": delta_relative, "revenue": delta_relative, "roas": delta_point}


def s4_delta_html(delta, metric_key, suffix):
    """변화량 div — 비교 불가(None)면 표시 자체를 생략한다(section-4 규칙, s5의 "(-)"와 다름).
    표시값(반올림) 0이면 화살표 없이 검정."""
    if delta is None:
        return ""
    rounded = round(delta, 1)
    if rounded == 0:
        inner = f"({rounded:.1f}{suffix})"
        color = "#1e293b"
    else:
        arrow = "▲" if delta > 0 else "▼"
        is_good = (delta > 0) == POSITIVE_ON_INCREASE[metric_key]
        color = "#dc2626" if is_good else "#2563eb"
        sign = "+" if delta > 0 else ""
        inner = f"({arrow} {sign}{rounded:.1f}{suffix})"
    return (f'\n            <div style="font-size:10.5px; text-align:center; '
            f'color:{color};">{inner}</div>')


def build_s4_rows(channels):
    """5개 항목 고정(누락 항목은 전부 "-"), M0 매출 내림차순 정렬 후 <tr> HTML 생성."""
    by_name = {c.get("name"): c for c in (channels or [])}
    entries = []
    for name in S4_CHANNELS:
        ch = by_name.get(name, {})
        m1_raw, m1_disp = s4_compute(ch.get("m1"))
        m0_raw, m0_disp = s4_compute(ch.get("m0"))
        entries.append((name, m1_raw, m1_disp, m0_raw, m0_disp))
    entries.sort(key=lambda e: e[3]["revenue"] if e[3]["revenue"] is not None else float("-inf"),
                 reverse=True)

    rows = []
    for name, m1_raw, m1_disp, m0_raw, m0_disp in entries:
        cells = [f'<td style="white-space:nowrap; text-align:left; '
                 f'border-right:1px solid #e2e8f0;">{name}</td>']
        for metric_key, suffix in METRIC_ORDER:
            delta = DELTA_FN[metric_key](m0_raw[metric_key], m1_raw[metric_key])
            last = metric_key == "roas"
            border = "" if last else " border-right:1px solid #e2e8f0;"
            cells.append(f'<td style="white-space:nowrap; text-align:center;">'
                         f'{m1_disp[metric_key]}</td>')
            cells.append(f'<td style="white-space:nowrap; text-align:center;{border}">\n'
                         f'            {m0_disp[metric_key]}'
                         f'{s4_delta_html(delta, metric_key, suffix)}\n'
                         f'          </td>')
        rows.append("<tr>\n          " + "\n          ".join(cells) + "\n        </tr>")
    return "\n        ".join(rows)


def load_rows(section):
    if not section:
        return None
    if "rows" in section:
        return section["rows"]
    path = section.get("rows_file")
    if not path:
        return None
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        return json.load(f)


def main():
    payload = json.load(sys.stdin)
    target = date.fromisoformat(payload["target_date"])
    m1_y, m1_m = month_shift(target.year, target.month, -1)
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
    if s2 and s2.get("executive_summary"):
        status["s2"] = "ok"
        html = html.replace("__S2_ITEMS_HTML__", build_summary_items(s2["executive_summary"]))
    else:
        status["s2"] = "placeholder"
        html = swap_section(html, "s2", PLACEHOLDER_CARD)

    # ── section 3 (스크립트 데이터는 섹션 유무와 무관하게 항상 유효한 JSON으로 치환 —
    #    placeholder일 땐 canvas가 없어 스크립트가 스스로 no-op 한다)
    s3 = section_data("s3")
    if s3 and s3.get("ad_cost"):
        status["s3"] = "ok"
        chart_data = {
            "labels": s3.get("labels") or build_month_labels(target),
            "ad_cost": s3["ad_cost"],
            "revenue": s3.get("revenue", []),
            "roas": s3.get("roas", []),
        }
        zero_fill = s3.get("zero_fill")
        if zero_fill is None:
            zero_fill = any(v == 0 for v in chart_data["ad_cost"]) or \
                any(v == 0 for v in chart_data["revenue"])
        html = html.replace(
            "__S3_FOOTNOTE_CURRENT_MONTH__",
            f"* 이번달({target.year % 100}년 {target.month}월)의 데이터는 1일부터 기준일인 "
            f"{target.month}월 {target.day}일까지의 수치입니다.")
        html = html.replace("__S3_FOOTNOTE_ZERO_FILL_HTML__",
                            S3_ZERO_FILL_FOOTNOTE if zero_fill else "")
    else:
        status["s3"] = "placeholder"
        html = swap_section(html, "s3", PLACEHOLDER_CARD)
        chart_data = {"labels": [], "ad_cost": [], "revenue": [], "roas": []}
    html = html.replace("__S3_CHART_DATA_JSON__", js_json(chart_data))

    # ── section 4 (5개 항목 고정 표 — 파생지표·변화량·정렬·행 HTML은 빌더가 생성)
    s4 = section_data("s4")
    if s4 and s4.get("channels"):
        status["s4"] = "ok"
        html = html.replace("__S4_ROWS_HTML__", build_s4_rows(s4["channels"]))
    else:
        status["s4"] = "placeholder"
        html = swap_section(html, "s4", PLACEHOLDER_CARD)

    # ── section 5 (행 데이터는 monthly_campaign_rows.py 출력)
    rows = load_rows(section_data("s5"))
    if rows is not None:
        status["s5"] = "ok"
    else:
        status["s5"] = "placeholder"
        html = swap_section(html, "s5", PLACEHOLDER_CARD)
        rows = []
    html = html.replace("__S5_ROWS_JSON__", js_json(rows))

    # ── 공통 치환
    html = html.replace("__REPORT_TITLE__", payload["title"])
    html = html.replace("__REPORT_DATE_LABEL__",
                        f"{target.year}년 {target.month}월 1일 ~ {target.month}월 {target.day}일")
    html = (html.replace("__M1_YY__", str(m1_y % 100)).replace("__M1_MM__", str(m1_m))
                .replace("__M0_YY__", str(target.year % 100)).replace("__M0_MM__", str(target.month)))

    # ── 치환 누락 검증 (chart.js 인라인 전에 — 알려진 토큰이 남아있으면 실패)
    leftovers = [t for t in [
        "__REPORT_TITLE__", "__REPORT_DATE_LABEL__", "__S1_", "__S2_ITEMS_HTML__",
        "__S3_", "__S4_ROWS_HTML__", "__S5_ROWS_JSON__", "__M1_", "__M0_",
    ] if t in html]
    if leftovers:
        raise SystemExit(f"치환 누락: {leftovers}")

    # ── chart.js 인라인 (마지막 — 내용이 커서 치환 검증 후에 붙인다)
    if not os.path.exists(CHART_JS) and os.path.exists(CHART_JS_FALLBACK):
        shutil.copyfile(CHART_JS_FALLBACK, CHART_JS)
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
