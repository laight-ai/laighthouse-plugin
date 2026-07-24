"""Pure MCP-response -> {sections, digest} mappers, per report_type/group.

Field mappings mirror the rules documented in each
sections/<report_type>/*.md file exactly. This module is the *executor* of
those rules, not their source of truth -- if a .md file's mapping rule
changes, update the corresponding function here to match it, never the
other way around.

No network/MCP calls happen here: callers save a raw MCP response to a JSON
file and pass its parsed contents in.
"""


def _fmt_amount(value):
    """toLocaleString()-style thousands separator, preserving exact digits."""
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        sign = "-" if value < 0 else ""
        magnitude = abs(value)
        int_part = int(magnitude)
        frac = repr(magnitude).split(".", 1)[1]
        return f"{sign}{int_part:,}.{frac}"
    return str(value)


def _ratio_to_pct(ratio):
    """Ratio (e.g. 5.06) -> percent number (506), per the x100 display rule.

    Rounded to 6 decimals first to absorb float multiplication noise
    (0.29 * 100 == 28.999999999999996) without altering the underlying value.
    """
    if ratio is None:
        return None
    pct = round(ratio * 100, 6)
    return int(pct) if pct.is_integer() else pct


# ---------------------------------------------------------------------------
# mtd
# ---------------------------------------------------------------------------


def map_mtd_group_a(data):
    """mtd-section-1 (월 목표 카드) + mtd-section-2 (목표 달성 현황).

    `data`: raw get_naver_target_progress response.
    """
    roas_goal_pct = _ratio_to_pct(data["target_roas"])
    roas_actual_pct = _ratio_to_pct(data["actual_roas"])
    budget_spent_rate = _ratio_to_pct(data["cost_progress_ratio"])
    revenue_achievement_rate = _ratio_to_pct(data["revenue_progress_ratio"])

    section1 = {
        "type": "kpi_cards",
        "cards": [
            {"label": "월 예산 목표", "value": _fmt_amount(data["target_cost"])},
            {"label": "월 매출 목표", "value": _fmt_amount(data["target_revenue"])},
            {"label": "월 ROAS 목표", "value": f"{roas_goal_pct}%"},
        ],
    }
    section2 = {
        "type": "kpi_cards",
        "cards": [
            {
                "label": "기간 예산대비 소진율",
                "value": f"{budget_spent_rate}%",
                "diff": f"목표 {_fmt_amount(data['target_cost'])} · 소진 {_fmt_amount(data['actual_cost'])}",
            },
            {
                "label": "기간 목표 매출 대비 달성률",
                "value": f"{revenue_achievement_rate}%",
                "diff": f"목표 {_fmt_amount(data['target_revenue'])} · 매출 {_fmt_amount(data['actual_revenue'])}",
            },
            {
                "label": "기간 누적 ROAS",
                "value": f"{roas_actual_pct}%",
                "diff": f"목표 {roas_goal_pct}%",
            },
        ],
    }
    digest = {
        "roas_goal_pct": roas_goal_pct,
        "roas_actual_pct": roas_actual_pct,
        "budget_spent_rate": budget_spent_rate,
        "revenue_achievement_rate": revenue_achievement_rate,
        "target_cost": data["target_cost"],
        "actual_cost": data["actual_cost"],
        "target_revenue": data["target_revenue"],
        "actual_revenue": data["actual_revenue"],
    }
    return {"sections": [section1, section2], "digest": digest}


def map_mtd_group_b(data):
    """mtd-section-4 (월별 광고 성과 차트).

    `data`: raw get_naver_monthly_ad_performance response
    ({"items": [{"month", "cost", "purchase_amount", "roas"}, ...]}).
    """
    items = data["items"]
    section = {
        "type": "chart",
        "heading": "월별 광고 성과",
        "categories": [item["month"] for item in items],
        "bar_series": [
            {"name": "광고비", "values": [item["cost"] for item in items]},
            {"name": "매출", "values": [item["purchase_amount"] for item in items]},
        ],
        "line_series": {"name": "ROAS", "values": [item["roas"] for item in items]},
    }
    return {"sections": [section], "digest": None}


def _top_n_categories_by_total(items, category_key, value_key, n):
    totals = {}
    for row in items:
        totals[row[category_key]] = totals.get(row[category_key], 0) + row[value_key]
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:n]
    return [category for category, _ in ranked]


def map_mtd_group_c(data):
    """mtd-section-6 (일일 카테고리별 매출) + mtd-section-6.1 (참조용, digest만).

    `data`: {"daily": <get_naver_item_sales_daily response>,
             "cumulative": <get_naver_category_sales response>}.
    """
    daily_items = data["daily"]["items"]
    cumulative_items = data["cumulative"]["items"]

    top_categories = _top_n_categories_by_total(
        daily_items, "product_category_3rd", "sales_amount", n=5
    )

    by_date = {}
    for row in daily_items:
        by_date.setdefault(row["logdate"], {})[row["product_category_3rd"]] = row["sales_amount"]
    labels = sorted(by_date.keys())

    rows = [
        [label] + [_fmt_amount(by_date[label].get(cat, 0)) for cat in top_categories]
        for label in labels
    ]

    section = {
        "type": "table",
        "heading": "일일 카테고리별 매출 현황",
        "headers": ["날짜"] + top_categories,
        "rows": rows,
    }
    digest = {
        "top_categories": top_categories,
        "top_category_totals": {
            cat: sum(by_date[label].get(cat, 0) for label in labels) for cat in top_categories
        },
        "product_cumulative_sales": cumulative_items,
    }
    return {"sections": [section], "digest": digest}


def map_mtd_group_d(data):
    """mtd-section-7 (매체별 예산 소진 현황).

    `data`: raw get_naver_channel_budget_progress response
    ({"items": [...], "total": {...}, "channel_group": "..."}).
    """
    rows = data["items"]
    total = data["total"]
    channel_group = data.get("channel_group")

    def _row(r, label):
        return [
            label,
            f"{r['spent_rate']}%",
            _fmt_amount(r["budget_goal"]),
            _fmt_amount(r["spent"]),
            _fmt_amount(r["daily_budget"]),
            _fmt_amount(r["daily_spent_avg"]),
        ]

    table_rows = [_row(r, r["channel"]) for r in rows]
    table_rows.append(_row(total, "합계"))

    heading = "매체별 예산 소진 현황"
    if channel_group:
        heading = f"{heading} ({channel_group})"

    section = {
        "type": "table",
        "heading": heading,
        "headers": ["매체", "예산 소진율", "목표 소진", "예산 소진", "일 소진예산", "일 평균 소진액"],
        "rows": table_rows,
    }
    digest = {
        "channels": [{"channel": r["channel"], "spent_rate": r["spent_rate"]} for r in rows],
        "total_spent_rate": total["spent_rate"],
    }
    return {"sections": [section], "digest": digest}


def map_mtd_group_e(data):
    """mtd-section-9 (캠페인별 성과).

    `data`: raw get_naver_campaign_performance response ({"items": [...]}).
    """
    items = data["items"]
    rows = [
        [
            item["campaign"],
            item["channel"],
            _fmt_amount(item["revenue"]),
            _fmt_amount(item["ad_cost"]),
            f"{item['roas']}%",
            _fmt_amount(item["impressions"]),
            _fmt_amount(item["clicks"]),
            f"{item['ctr']}%",
            _fmt_amount(item["cpc"]),
            item["purchases"],
            _fmt_amount(item["avg_price"]),
        ]
        for item in items
    ]
    section = {
        "type": "table",
        "heading": "캠페인별 성과",
        "headers": [
            "캠페인", "네이버 광고 채널명", "매출", "광고비", "ROAS",
            "노출", "클릭", "CTR", "CPC", "구매", "평균단가",
        ],
        "rows": rows,
    }
    digest = {
        "top_campaigns_by_ad_cost": sorted(items, key=lambda i: i["ad_cost"], reverse=True)[:3],
    }
    return {"sections": [section], "digest": digest}


def map_mtd_group_f(data):
    """mtd-section-10 (광고그룹별 성과).

    `data`: raw get_naver_group_performance response ({"items": [...]}).
    """
    items = data["items"]
    rows = [
        [
            item["group"],
            _fmt_amount(item["impressions"]),
            _fmt_amount(item["clicks"]),
            _fmt_amount(item["cpc"]),
            _fmt_amount(item["ad_cost"]),
            _fmt_amount(item["revenue"]),
        ]
        for item in items
    ]
    section = {
        "type": "table",
        "heading": "광고그룹별 성과",
        "headers": ["광고그룹", "노출", "클릭", "CPC", "광고비", "매출"],
        "rows": rows,
    }
    return {"sections": [section], "digest": None}


def map_mtd_group_g(data):
    """mtd-section-11 (키워드별 성과).

    `data`: raw get_naver_keyword_performance response ({"items": [...]}).
    """
    items = data["items"]
    rows = [
        [
            item["keyword"],
            _fmt_amount(item["impressions"]),
            _fmt_amount(item["clicks"]),
            _fmt_amount(item["ad_cost"]),
            _fmt_amount(item["cpc"]),
            f"{item['ctr']}%",
            _fmt_amount(item["cpm"]),
            item["purchases"],
            _fmt_amount(item["revenue"]),
            f"{item['roas']}%",
        ]
        for item in items
    ]
    section = {
        "type": "table",
        "heading": "키워드별 성과",
        "headers": ["키워드", "노출", "클릭", "광고비", "CPC", "클릭율", "CPM", "구매건수", "매출", "ROAS"],
        "rows": rows,
    }
    return {"sections": [section], "digest": None}


MAPPERS = {
    ("mtd", "A"): map_mtd_group_a,
    ("mtd", "B"): map_mtd_group_b,
    ("mtd", "C"): map_mtd_group_c,
    ("mtd", "D"): map_mtd_group_d,
    ("mtd", "E"): map_mtd_group_e,
    ("mtd", "F"): map_mtd_group_f,
    ("mtd", "G"): map_mtd_group_g,
}


def map_section(report_type, group, data):
    mapper = MAPPERS.get((report_type, group))
    if mapper is None:
        raise ValueError(f"unknown report_type/group: {report_type}/{group}")
    return mapper(data)
