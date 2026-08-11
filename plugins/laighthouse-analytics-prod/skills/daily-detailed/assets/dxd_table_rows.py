#!/usr/bin/env python3
"""daily-detailed section-4/5 공용: D-1 vs D-0 조인·파생지표·정렬·필터·<tr> HTML 생성.

이미 검증된 asset 스크립트다 — 실행 중 모델이 이 파일을 만들거나 수정하지 않는다. stdin으로
MCP 응답 JSON을 받아 stdout으로 완성된 행 배열만 낸다. 중간 파일을 만들지 않는다(파이프로만
입출력).

입력 (stdin, JSON):
{
  "level": "campaign" | "ad",       # section-4=campaign, section-5=ad
  "d1_date": "YYYY-MM-DD",
  "d0_date": "YYYY-MM-DD",
  "threshold": 10000,                 # D0 광고비 <= threshold 인 행 제외 (기본 10000)
  "media_rows": [ ... ],              # google/meta/naver get_ad_performance_daily_table 응답 행을
                                       # 그대로 이어붙인 리스트 (media 필드로 매체 구분)
  "airbridge_rows": [ ... ]           # media="airbridge" 응답 행 (항상 group_by="campaign")
}

출력 (stdout, JSON): [{"search": "매체 캠페인 [광고그룹 광고] (소문자)", "html": "<tr>...</tr>"}, ...]
D0 광고비 내림차순, threshold 이하 제외, HTML까지 완성된 상태 — 그대로
{DAILY_CAMPAIGN_ROWS}/{DAILY_AD_ROWS} 자리에 넣으면 된다.

사용 예:
  echo '{"level":"campaign", ...}' | python3 assets/dxd_table_rows.py
"""
import sys
import json
import io

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MEDIA_LABEL = {"google": "Google Ads", "meta": "Meta Ads", "naver": "Naver Ads"}

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
