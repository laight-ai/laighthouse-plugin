#!/usr/bin/env python3
"""daily-detailed section-4/5 공용: D-1 vs D-0 조인·파생지표·정렬·필터·<tr> HTML 생성.

이미 검증된 asset 스크립트다 — 실행 중 모델이 이 파일을 만들거나 수정하지 않는다. stdin으로
MCP 응답 JSON을 받아 stdout으로 완성된 행 배열만 낸다. 중간 파일을 만들지 않는다(파이프로만
입출력).

⚠️ **`get_ad_performance_daily_table`은 JSON 행 배열이 아니라 마크다운 표(파이프 `|`로 구분된
텍스트 한 덩어리)를 반환한다.** 그 원본 문자열을 손으로 JSON으로 옮겨 적거나(전사 실수·행 누락
위험), 그걸 파싱하는 별도 스크립트 파일을 새로 만들지 않는다 — 아래 (C) 입력 형태로 그 원본
문자열을 **그대로** 넘기면 이 스크립트가 직접 파싱한다.

입력 (stdin, JSON) — 셋 중 한 형태:

(A) media별로 개별 호출한 경우, 이미 파싱된 행 객체로 넘길 때(예: section-5, `group_by:"ad"`는
    카디널리티 위험이 있어 매체별 개별 호출을 유지):
{
  "level": "campaign" | "ad",       # section-4=campaign, section-5=ad
  "d1_date": "YYYY-MM-DD",
  "d0_date": "YYYY-MM-DD",
  "threshold": 10000,                 # D0 광고비 <= threshold 인 행 제외 (기본 10000)
  "media_rows": [ ... ],              # google/meta/naver get_ad_performance_daily_table 응답 행을
                                       # 그대로 이어붙인 리스트 (media 필드로 매체 구분)
  "airbridge_rows": [ ... ]           # media="airbridge" 응답 행 (항상 group_by="campaign")
}

(B) `media`를 생략해 한 번에 받은 경우, 이미 파싱된 행 객체로 넘길 때(예: section-4,
    `group_by:"campaign"`은 캠페인 단위라 카디널리티가 낮아 안전):
{
  "level": "campaign", "d1_date": "...", "d0_date": "...",
  "rows": [ ... ]    # google/meta/naver/airbridge/ga4가 섞인 단일 응답 그대로 — media 필드로
                     # 자동 분리한다(ga4 등 불필요한 매체는 자동 제외)
}

(C) **권장 — MCP 도구가 실제로 반환하는 원본 마크다운 문자열을 그대로 넘길 때** (A/B의
    `media_rows`/`airbridge_rows`/`rows` 대신 아래 `markdown` 키 하나만 쓴다. 각 도구 호출의
    `result` 문자열을 파싱·가공 없이 그대로 배열에 담는다 — 호출이 몇 번이든(section-4는 1개,
    section-5는 4개) 전부 이 배열 하나에 넣으면 스크립트가 각 문자열을 파싱하고 `media` 필드로
    media_rows/airbridge_rows를 자동 분리한다):
{
  "level": "campaign" | "ad", "d1_date": "...", "d0_date": "...",
  "markdown": [ "<google 호출의 result 원본 문자열>", "<meta 호출의 result 원본 문자열>", ... ]
}

출력 (stdout, JSON): [{"search": "매체 캠페인 [광고그룹 광고] (소문자)", "html": "<tr>...</tr>"}, ...]
D0 광고비 내림차순, threshold 이하 제외, HTML까지 완성된 상태 — 그대로
{DAILY_CAMPAIGN_ROWS}/{DAILY_AD_ROWS} 자리에 넣으면 된다.

사용 예:
  echo '{"level":"campaign", "d1_date":"...", "d0_date":"...", "markdown":["| logdate | media | ...\\n| --- | ...\\n| 2026-07-03 | google | ..."]}' \
    | python3 assets/dxd_table_rows.py
"""
import sys
import json
import io

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MEDIA_LABEL = {"google": "Google Ads", "meta": "Meta Ads", "naver": "Naver Ads"}

STRING_FIELDS = {"logdate", "media", "campaign_name", "asset_group", "ad_name", "channel"}


def _coerce_cell(key, value):
    value = value.strip()
    if key in STRING_FIELDS:
        return value
    if value == "":
        return None
    try:
        f = float(value)
    except ValueError:
        return value  # 예상 못 한 비숫자 값은 문자열 그대로 보존(방어적)
    return int(f) if f.is_integer() else f


def parse_markdown_table(text):
    """`get_ad_performance_daily_table` 등이 반환하는 파이프(|) 마크다운 표 문자열을
    행 dict 리스트로 파싱한다. 두 번째 줄(전부 `---`인 구분선)은 건너뛴다."""
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        return []
    header = [c.strip() for c in lines[0].strip().strip("|").split("|")]
    rows = []
    for line in lines[1:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(c == "" or set(c) <= {"-"} for c in cells):
            continue  # 구분선(| --- | --- | ...) 스킵
        if len(cells) != len(header):
            continue  # 길이가 안 맞는 손상된 행은 방어적으로 스킵
        rows.append({h: _coerce_cell(h, v) for h, v in zip(header, cells)})
    return rows


# 각 지표의 색상 규칙: True면 "증가=빨강(긍정)", False면 "감소=빨강(긍정)" (CPA만 False)
POSITIVE_ON_INCREASE = {
    "cost": True,
    "ctr": True,
    "reservation": True,
    "cpa": False,
    "revenue": True,
    "roas": True,
}


def fmt_won(v):
    return f"₩{round(v):,}"


def fmt_pct1(v):
    return f"{v:.1f}%"


def calc_ctr(click, impression):
    if not impression:
        return None
    return click / impression * 100


def calc_cpa(cost, reservation):
    if not reservation:
        return None
    return cost / reservation


def calc_roas(revenue, cost):
    if not cost:
        return None
    return revenue / cost * 100


def delta_relative(d0, d1):
    """% 변화 (광고비/예약 완료/CPA/매출): D0 또는 D1이 없으면(airbridge 미매칭 "-" 포함)
    표시 안 함, D1이 0이어도 표시 안 함."""
    if d0 is None or d1 in (None, 0):
        return None
    return (d0 - d1) / d1 * 100


def delta_point(d0, d1):
    """%p 변화 (CTR/ROAS): D1이 None이면 표시 안 함, 0은 유효한 값."""
    if d0 is None or d1 is None:
        return None
    return d0 - d1


def arrow_color(delta, metric_key, digits=1):
    """(화살표, 표시텍스트(부호 포함, 단위 제외), 색상) — delta가 None이면 표시하지 않음(빈 문자열)."""
    if delta is None:
        return None
    rounded = round(delta, digits)
    if rounded == 0:
        return ("", f"{rounded:.{digits}f}", "#1e293b")
    arrow = "▲" if delta > 0 else "▼"
    positive_on_increase = POSITIVE_ON_INCREASE[metric_key]
    is_good = (delta > 0) == positive_on_increase
    color = "#dc2626" if is_good else "#2563eb"
    sign = "+" if delta > 0 else ""
    return (arrow, f"{sign}{rounded:.{digits}f}", color)


def value_cell(value_str):
    return value_str


def delta_html(delta_tuple, suffix):
    if delta_tuple is None:
        return ""
    arrow, text, color = delta_tuple
    return (
        f'\n            <div style="font-size:10.5px; text-align:center; color:{color};">'
        f"({arrow} {text}{suffix})</div>"
    )


def media_group_key(row, level):
    media = row.get("media") or ""
    campaign = row.get("campaign_name") or ""
    if level == "ad":
        return (media, campaign, row.get("asset_group") or "", row.get("ad_name") or "")
    return (media, campaign)


def index_media_by_date_key(rows, level):
    idx = {}
    for r in rows:
        k = (r.get("logdate"), media_group_key(r, level))
        idx.setdefault(k, []).append(r)
    return idx


def sum_media(rows):
    if not rows:
        return None
    cost = sum(r.get("cost") or 0 for r in rows)
    impression = sum(r.get("impression") or 0 for r in rows)
    click = sum(r.get("click") or 0 for r in rows)
    return {"cost": cost, "impression": impression, "click": click}


def index_airbridge_by_date_campaign(rows):
    idx = {}
    for r in rows:
        k = (r.get("logdate"), r.get("campaign_name") or "")
        idx.setdefault(k, []).append(r)
    return idx


def sum_airbridge(rows):
    if not rows:
        return None
    revenue = sum(r.get("airbridge_revenue") or 0 for r in rows)
    reservation = sum(r.get("reservation") or 0 for r in rows)
    return {"revenue": revenue, "reservation": reservation}


def compute_metrics(media_sum, ab_sum):
    """media_sum/ab_sum 중 하나가 None이면 해당 값은 미매칭("-")."""
    cost = media_sum["cost"] if media_sum else 0.0
    ctr = calc_ctr(media_sum["click"], media_sum["impression"]) if media_sum else None
    revenue = ab_sum["revenue"] if ab_sum else None
    reservation = ab_sum["reservation"] if ab_sum else None
    cpa = calc_cpa(cost, reservation) if ab_sum else None
    roas = calc_roas(revenue, cost) if ab_sum else None
    return {
        "cost": cost,
        "ctr": ctr,
        "reservation": reservation,
        "cpa": cpa,
        "revenue": revenue,
        "roas": roas,
    }


def display(metrics, unmatched):
    d = {}
    d["cost"] = fmt_won(metrics["cost"])
    d["ctr"] = fmt_pct1(metrics["ctr"]) if metrics["ctr"] is not None else "N/A"
    if unmatched:
        d["reservation"] = "-"
        d["cpa"] = "-"
        d["revenue"] = "-"
        d["roas"] = "-"
    else:
        d["reservation"] = str(int(metrics["reservation"])) if metrics["reservation"] is not None else "N/A"
        d["cpa"] = fmt_won(metrics["cpa"]) if metrics["cpa"] is not None else "N/A"
        d["revenue"] = fmt_won(metrics["revenue"]) if metrics["revenue"] is not None else "N/A"
        d["roas"] = fmt_pct1(metrics["roas"]) if metrics["roas"] is not None else "N/A"
    return d


def build_row_html(level, media_label, campaign, asset_group, ad_name, cells):
    if level == "ad":
        id_html = (
            f'<td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{media_label}</td>\n'
            f'          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{campaign}</td>\n'
            f'          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{asset_group}</td>\n'
            f'          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{ad_name}</td>'
        )
    else:
        id_html = (
            f'<td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{media_label}</td>\n'
            f'          <td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{campaign}</td>'
        )

    metric_html_parts = []
    for i, (metric_key, suffix) in enumerate(
        [("cost", "%"), ("ctr", "%p"), ("reservation", "%"), ("cpa", "%"), ("revenue", "%"), ("roas", "%p")]
    ):
        d1_val, d0_val, delta = cells[metric_key]
        last = metric_key == "roas"
        border = "" if last else " border-right:1px solid #e2e8f0;"
        metric_html_parts.append(
            f'<td style="white-space:nowrap; text-align:center;">{d1_val}</td>\n'
            f'          <td style="white-space:nowrap; text-align:center;{border}">\n'
            f"            {d0_val}{delta_html(delta, suffix)}\n"
            f"          </td>"
        )

    return "<tr>\n          " + id_html + "\n          " + "\n          ".join(metric_html_parts) + "\n        </tr>"


def main():
    payload = json.load(sys.stdin)
    level = payload["level"]
    d1_date = payload["d1_date"]
    d0_date = payload["d0_date"]
    threshold = payload.get("threshold", 10000)
    if "markdown" in payload:
        md = payload["markdown"]
        if isinstance(md, str):
            md = [md]
        rows = [r for text in md for r in parse_markdown_table(text)]
        media_rows = [r for r in rows if r.get("media") in MEDIA_LABEL]
        airbridge_rows = [r for r in rows if r.get("media") == "airbridge"]
    elif "rows" in payload:
        rows = payload["rows"]
        media_rows = [r for r in rows if r.get("media") in MEDIA_LABEL]
        airbridge_rows = [r for r in rows if r.get("media") == "airbridge"]
    else:
        media_rows = payload["media_rows"]
        airbridge_rows = payload["airbridge_rows"]

    media_idx = index_media_by_date_key(media_rows, level)
    ab_idx = index_airbridge_by_date_campaign(airbridge_rows)

    keys = {k for (_date, k) in media_idx.keys()}

    out = []
    for key in keys:
        media_code = key[0]
        campaign = key[1]
        media_label = MEDIA_LABEL.get(media_code)
        if media_label is None:
            continue  # ga4 등 이 섹션에 불필요한 매체는 방어적으로 제외

        d1_media = sum_media(media_idx.get((d1_date, key)))
        d0_media = sum_media(media_idx.get((d0_date, key)))
        if d0_media is None:
            continue  # D0 매체 데이터 자체가 없으면 cost=0 -> threshold 이하와 동일하게 제외

        if d0_media["cost"] <= threshold:
            continue

        d1_ab = sum_airbridge(ab_idx.get((d1_date, campaign)))
        d0_ab = sum_airbridge(ab_idx.get((d0_date, campaign)))

        d1_metrics = compute_metrics(d1_media, d1_ab)
        d0_metrics = compute_metrics(d0_media, d0_ab)
        d1_disp = display(d1_metrics, unmatched=(d1_ab is None)) if d1_media else None
        d0_disp = display(d0_metrics, unmatched=(d0_ab is None))

        cells = {}
        for metric_key, delta_fn in [
            ("cost", delta_relative),
            ("ctr", delta_point),
            ("reservation", delta_relative),
            ("cpa", delta_relative),
            ("revenue", delta_relative),
            ("roas", delta_point),
        ]:
            d1_val = d1_disp[metric_key] if d1_disp else "N/A"
            d0_val = d0_disp[metric_key]
            d1_raw = d1_metrics[metric_key] if d1_media else None
            d0_raw = d0_metrics[metric_key]
            delta = delta_fn(d0_raw, d1_raw)
            cells[metric_key] = (d1_val, d0_val, arrow_color(delta, metric_key))

        asset_group = key[2] if level == "ad" else None
        ad_name = key[3] if level == "ad" else None
        asset_group_disp = asset_group if asset_group else "-"
        ad_name_disp = ad_name if ad_name else "-"

        html = build_row_html(level, media_label, campaign, asset_group_disp, ad_name_disp, cells)
        search_parts = [media_label.lower(), campaign.lower()]
        if level == "ad":
            search_parts += [asset_group_disp.lower(), ad_name_disp.lower()]
        out.append({
            "search": " ".join(search_parts),
            "html": html,
            "_d0_cost": d0_media["cost"],
        })

    out.sort(key=lambda r: r["_d0_cost"], reverse=True)
    for r in out:
        del r["_d0_cost"]

    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
