#!/usr/bin/env python3
"""monthly-detailed section-5 전용: 캠페인 성과 비교(M-1 vs M0) 조인·파생지표·변화율·정렬·필터·
<tr> HTML 생성.

이미 검증된 asset 스크립트다 — 실행 중 모델이 이 파일을 만들거나 수정하지 않는다. stdin으로
MCP 응답 JSON을 받아 stdout으로 완성된 행 배열만 낸다. 중간 파일을 만들지 않는다(파이프로만
입출력).

`daily-detailed/assets/dxd_table_rows.py`(D-1 vs D-0, 날짜 단위 조인)와 계산 로직은 거의
동일하지만, 이 스킬은 월 단위(M-1 vs M0) 비교이고 비교 불가 시 규칙이 다르다 —
`monthly-detailed-section-5-campaign-performance.md`의 스펙을 그대로 따른다:
  - M-1 값이 없거나(캠페인 자체가 그 달에 없음) 0이어서 비교가 불가능하면, 변화량 자리에
    "(-)"를 화살표/색 없이 회색으로 표시한다 (daily처럼 변화량 칸 자체를 비워두지 않는다).
  - 필터 기준은 M0 광고비 ₩300,000 이하 제외 (daily는 ₩10,000).
  - 매체 쪽에만 있는(airbridge 미매칭) 캠페인은 그 달의 매출/예약 완료/CPA/ROAS를 "-"로
    표시한다(N/A 아님) — CTR만 노출 0일 때 N/A를 쓴다.

입력 (stdin, JSON):
{
  "m1_month": "YYYY-MM",
  "m0_month": "YYYY-MM",
  "threshold": 300000,                # M0 광고비 <= threshold 인 행 제외 (기본 300000)
  "media_rows": [ ... ],              # google/meta/naver get_ad_performance_monthly_table
                                       # (group_by:"campaign") 응답 행을 그대로 이어붙인 리스트
                                       # (media 필드로 매체 구분, month/campaign_name/cost/
                                       # impression/click 포함)
  "airbridge_rows": [ ... ]           # media="airbridge" 응답 행(group_by:"campaign",
                                       # month/campaign_name/airbridge_revenue/reservation 포함)
}

출력 (stdout, JSON): [{"search": "매체 캠페인 (소문자)", "html": "<tr>...</tr>"}, ...]
M0 광고비 내림차순, threshold 이하 제외, HTML까지 완성된 상태 — 그대로
{MONTHLY_CAMPAIGN_ROWS} 자리에 넣으면 된다.

사용 예:
  echo '{"m1_month":"2026-06","m0_month":"2026-07", ...}' | python3 assets/monthly_campaign_rows.py
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

METRIC_ORDER = [("cost", "%"), ("ctr", "%p"), ("reservation", "%"), ("cpa", "%"), ("revenue", "%"), ("roas", "%p")]


def fmt_won(v):
    return f"₩{round(v):,}"


def fmt_pct1(v):
    return f"{v:.1f}%"


def sum_media(rows):
    """같은 (month, media, campaign) 키에 여러 행이 있으면 합산. 행이 없으면 None(그 달에
    캠페인 자체가 없음)."""
    if not rows:
        return None
    cost = sum(r.get("cost") or 0 for r in rows)
    impression = sum(r.get("impression") or 0 for r in rows)
    click = sum(r.get("click") or 0 for r in rows)
    return {"cost": cost, "impression": impression, "click": click}


def sum_airbridge(rows):
    if not rows:
        return None
    revenue = sum(r.get("airbridge_revenue") or 0 for r in rows)
    reservation = sum(r.get("reservation") or 0 for r in rows)
    return {"revenue": revenue, "reservation": reservation}


def cost_metric(media):
    """(raw, display) — media가 None이면 그 달에 캠페인 자체가 없어 '-'."""
    if media is None:
        return None, "-"
    cost = media["cost"]
    return cost, fmt_won(cost)


def ctr_metric(media):
    """(raw, display) — media가 None이면 '-', 노출이 0이면 N/A."""
    if media is None:
        return None, "-"
    impression = media["impression"]
    click = media["click"]
    if not impression:
        return None, "N/A"
    val = click / impression * 100
    return val, fmt_pct1(val)


def revenue_reservation_metric(ab):
    """(revenue_raw, reservation_raw, revenue_disp, reservation_disp) — ab가 None이면(매체
    쪽에만 있어 airbridge 미매칭) 전부 '-'."""
    if ab is None:
        return None, None, "-", "-"
    revenue = ab["revenue"]
    reservation = ab["reservation"]
    return revenue, reservation, fmt_won(revenue), str(int(reservation))


def cpa_metric(cost_raw, reservation_raw):
    if cost_raw is None or not reservation_raw:
        return None, "-"
    val = cost_raw / reservation_raw
    return val, fmt_won(val)


def roas_metric(revenue_raw, cost_raw):
    if revenue_raw is None or not cost_raw:
        return None, "-"
    val = revenue_raw / cost_raw * 100
    return val, fmt_pct1(val)


def compute_month(media, ab):
    cost_raw, cost_disp = cost_metric(media)
    ctr_raw, ctr_disp = ctr_metric(media)
    revenue_raw, reservation_raw, revenue_disp, reservation_disp = revenue_reservation_metric(ab)
    cpa_raw, cpa_disp = cpa_metric(cost_raw, reservation_raw)
    roas_raw, roas_disp = roas_metric(revenue_raw, cost_raw)
    raw = {"cost": cost_raw, "ctr": ctr_raw, "reservation": reservation_raw, "cpa": cpa_raw, "revenue": revenue_raw, "roas": roas_raw}
    disp = {"cost": cost_disp, "ctr": ctr_disp, "reservation": reservation_disp, "cpa": cpa_disp, "revenue": revenue_disp, "roas": roas_disp}
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


DELTA_FN = {
    "cost": delta_relative,
    "ctr": delta_point,
    "reservation": delta_relative,
    "cpa": delta_relative,
    "revenue": delta_relative,
    "roas": delta_point,
}


def arrow_color(delta, metric_key, digits=1):
    """(화살표, 표시텍스트(부호 포함, 단위 제외), 색상) — delta가 None이면 비교 불가(호출부에서
    "(-)" 처리)."""
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


def delta_html(delta_tuple, suffix):
    """delta_tuple이 None이면 비교 자체가 불가능한 경우 — 섹션 스펙대로 '(-)'를 회색으로
    표시한다(daily처럼 칸을 비우지 않는다)."""
    if delta_tuple is None:
        return (
            '\n            <div style="font-size:10.5px; text-align:center; color:#94a3b8; '
            'line-height:1.3; margin-top:3px;">(-)</div>'
        )
    arrow, text, color = delta_tuple
    return (
        f'\n            <div style="font-size:10.5px; text-align:center; color:{color}; '
        f'line-height:1.3; margin-top:3px;">({arrow} {text}{suffix})</div>'
    )


def build_row_html(media_label, campaign, cells):
    id_html = (
        f'<td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{media_label}</td>\n'
        f'          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{campaign}</td>'
    )

    metric_html_parts = []
    for metric_key, suffix in METRIC_ORDER:
        m1_val, m0_val, delta = cells[metric_key]
        last = metric_key == "roas"
        border = "" if last else " border-right:1px solid #e2e8f0;"
        metric_html_parts.append(
            f'<td style="white-space:nowrap; text-align:center; padding-top:10px; padding-bottom:10px; line-height:1.3;">{m1_val}</td>\n'
            f'          <td style="white-space:nowrap; text-align:center;{border} padding-top:10px; padding-bottom:10px; line-height:1.3;">\n'
            f'            <div style="line-height:1.3;">{m0_val}</div>{delta_html(delta, suffix)}\n'
            f"          </td>"
        )

    return "<tr>\n          " + id_html + "\n          " + "\n          ".join(metric_html_parts) + "\n        </tr>"


def main():
    payload = json.load(sys.stdin)
    m1_month = payload["m1_month"]
    m0_month = payload["m0_month"]
    threshold = payload.get("threshold", 300000)
    media_rows = payload["media_rows"]
    airbridge_rows = payload["airbridge_rows"]

    media_idx = {}
    for r in media_rows:
        media = r.get("media")
        if media not in MEDIA_LABEL:
            continue  # 이 섹션에 불필요한 매체(ga4 등)는 방어적으로 제외
        key = (r.get("month"), media, r.get("campaign_name") or "")
        media_idx.setdefault(key, []).append(r)

    ab_idx = {}
    for r in airbridge_rows:
        key = (r.get("month"), r.get("campaign_name") or "")
        ab_idx.setdefault(key, []).append(r)

    # M0에 캠페인 행이 존재하는 (media, campaign) 키만 후보로 삼는다 — M0에 없으면(M-1에만
    # 있던 캠페인) 필터 대상에서 자연히 제외된다.
    m0_keys = {(media, campaign) for (month, media, campaign) in media_idx.keys() if month == m0_month}

    out = []
    for media, campaign in m0_keys:
        media_label = MEDIA_LABEL[media]

        m0_media = sum_media(media_idx.get((m0_month, media, campaign)))
        if m0_media is None or m0_media["cost"] <= threshold:
            continue

        m1_media = sum_media(media_idx.get((m1_month, media, campaign)))
        m0_ab = sum_airbridge(ab_idx.get((m0_month, campaign)))
        m1_ab = sum_airbridge(ab_idx.get((m1_month, campaign)))

        m1_raw, m1_disp = compute_month(m1_media, m1_ab)
        m0_raw, m0_disp = compute_month(m0_media, m0_ab)

        cells = {}
        for metric_key, _suffix in METRIC_ORDER:
            delta = DELTA_FN[metric_key](m0_raw[metric_key], m1_raw[metric_key])
            cells[metric_key] = (m1_disp[metric_key], m0_disp[metric_key], arrow_color(delta, metric_key))

        html = build_row_html(media_label, campaign, cells)
        out.append({
            "search": f"{media_label.lower()} {campaign.lower()}",
            "html": html,
            "_m0_cost": m0_media["cost"],
        })

    out.sort(key=lambda r: r["_m0_cost"], reverse=True)
    for r in out:
        del r["_m0_cost"]

    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
