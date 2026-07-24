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


# ---------------------------------------------------------------------------
# monthly
# ---------------------------------------------------------------------------


def map_monthly_group_a(data):
    """monthly-section-1 (월 목표 카드) + monthly-section-2 (목표 달성 현황).

    `data`: raw get_naver_target_progress response (as_of_date = 해당 월 말일).
    Identical field mapping to map_mtd_group_a -- the only documented
    difference between mtd and monthly for this pair is the card label prefix
    ("기간" -> "월") and that the caller passes as_of_date=month-end instead of
    a partial-month date (that distinction lives entirely in the MCP call
    params, not in this function).
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
                "label": "월 예산대비 소진율",
                "value": f"{budget_spent_rate}%",
                "diff": f"목표 {_fmt_amount(data['target_cost'])} · 소진 {_fmt_amount(data['actual_cost'])}",
            },
            {
                "label": "월 목표 매출 대비 달성률",
                "value": f"{revenue_achievement_rate}%",
                "diff": f"목표 {_fmt_amount(data['target_revenue'])} · 매출 {_fmt_amount(data['actual_revenue'])}",
            },
            {
                "label": "월 누적 ROAS",
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


def map_monthly_group_b(data):
    """monthly-section-4 (월별 광고 성과 차트).

    `data`: raw get_naver_monthly_ad_performance response
    ({"items": [{"month", "cost", "purchase_amount", "roas"}, ...]}).
    Identical mapping to map_mtd_group_b; unlike mtd, monthly's digest is not
    None -- section3 item 2 needs the last-6-months trend, so the raw items
    are passed through unmodified (digest carries numbers, not a verdict on
    which "phase" the trend is in -- that judgment call is left to the LLM).
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
    digest = {"items": items}
    return {"sections": [section], "digest": digest}


def map_monthly_group_c(data):
    """monthly-section-6 (카테고리별 월간 매출액 비교) + monthly-section-7 (일일 카테고리별
    매출 현황).

    These two sections are grouped together (unlike their mtd analogues, which
    are independent) because monthly-section-7 explicitly requires reusing
    section 6's top-5-category selection instead of computing its own top-5
    from the daily series -- so both outputs must be produced from a single
    top-5 ranking to stay consistent.

    `data`: {
      "curr": <get_naver_category_sales response, 이번 달 전체>,
      "prev": <get_naver_category_sales response, 전월 전체>,
      "daily": <get_naver_item_sales_daily response, 이번 달 전체>,
      "curr_month_label": "26년 3월",   # e.g. -- caller-supplied, not returned by any MCP tool
      "prev_month_label": "26년 2월",
    }
    The month labels aren't part of any MCP response; the caller (who already
    computed the curr/prev date ranges to make the two get_naver_category_sales
    calls) supplies them directly, same spirit as map_mtd_group_d's
    caller-supplied `channel_group` passthrough.
    """
    curr_items = data["curr"]["items"]
    prev_items = data["prev"]["items"]
    curr_map = {row["category"]: row["sales"] for row in curr_items}
    prev_map = {row["category"]: row["sales"] for row in prev_items}

    top5 = [
        category
        for category, _ in sorted(curr_map.items(), key=lambda kv: kv[1], reverse=True)[:5]
    ]

    other_curr = sum(sales for cat, sales in curr_map.items() if cat not in top5)
    other_prev = sum(sales for cat, sales in prev_map.items() if cat not in top5)

    labels = top5 + ["기타"]
    curr_values = [curr_map[cat] for cat in top5] + [other_curr]
    prev_values = [prev_map.get(cat, 0) for cat in top5] + [other_prev]

    # change_pct rounded to 1 decimal place -- confirmed against
    # monthly-section-6.md's own literal example: recomputing (curr-prev)/prev*100
    # for its 6 example rows reproduces 5 of the 6 documented change_pct values
    # exactly once rounded to 1 decimal (-1.6/17.0/18.8/6.6/27.2); the 6th
    # (국내분유, documented as 5.1) only comes out to ~5.3 from the documented
    # prev/curr pair, which looks like a single-digit typo in the doc's prev
    # value rather than a different rounding rule -- the 1-decimal rounding
    # rule itself is unambiguous from the other 5 matches.
    change_pct = []
    for curr_val, prev_val in zip(curr_values, prev_values):
        if prev_val == 0:
            change_pct.append(None)
        else:
            change_pct.append(round((curr_val - prev_val) / prev_val * 100, 1))
    # Chart line_series can't carry `null`; per monthly-section-6.md, a null
    # (new-category) change_pct displays as 0 on the chart line.
    change_pct_chart = [0 if v is None else v for v in change_pct]

    section6 = {
        "type": "chart",
        "heading": "카테고리별 월간 매출액 비교",
        "categories": labels,
        "bar_series": [
            {"name": data["prev_month_label"], "values": prev_values},
            {"name": data["curr_month_label"], "values": curr_values},
        ],
        "line_series": {"name": "전월 대비 증감률(%)", "values": change_pct_chart},
    }

    daily_items = data["daily"]["items"]
    by_date = {}
    for row in daily_items:
        by_date.setdefault(row["logdate"], {})[row["product_category_3rd"]] = row["sales_amount"]
    date_labels = sorted(by_date.keys())
    rows = [
        [label] + [_fmt_amount(by_date[label].get(cat, 0)) for cat in top5]
        for label in date_labels
    ]
    section7 = {
        "type": "table",
        "heading": "일일 카테고리별 매출 현황",
        "headers": ["날짜"] + top5,
        "rows": rows,
    }

    digest = {
        "category_monthly_comparison": {
            "prev_month_label": data["prev_month_label"],
            "curr_month_label": data["curr_month_label"],
            "labels": labels,
            "prev": prev_values,
            "curr": curr_values,
            "change_pct": change_pct,
        },
        "daily_sales": {"labels": date_labels, "top_categories": top5},
    }
    return {"sections": [section6, section7], "digest": digest}


_MONTHLY_CHANNEL_LABELS = [
    ("nvad:BRS", "네이버 브랜드검색"),
    ("nvad:PLINK", "네이버 파워링크"),
    ("nvad:NVSHOP", "네이버 쇼핑검색"),
    ("nvgfa_ad:", "네이버 GFA 애드부스트"),
    ("nvgfa_dp:", "네이버 GFA 디스플레이"),
]


def map_monthly_group_d(data):
    """monthly-section-8 (매체별 성과 비교).

    `data`: {
      "curr": <get_naver_channel_progression response, 이번 달>,
      "prev": <get_naver_channel_progression response, 전월>,
      "curr_month_label": "2026년 3월",   # caller-supplied, see map_monthly_group_c
      "prev_month_label": "2026년 2월",
    }
    Each of curr/prev is assumed shaped as
    {"channels": [{"channel": "nvad:BRS", "actual": [{"date","cost","revenue"}, ...]}, ...]}.

    ⚠️ NOTE ON THE `"channel"` KEY NAME: no section .md file in this skill
    contains a literal raw JSON example of get_naver_channel_progression's
    response (every doc that uses this tool only describes the aggregated
    output, not the raw per-channel shape). The `"channel"` key name used here
    is inferred from the naming convention used consistently by every *other*
    naver MCP tool response documented in this skill (mtd-section-7, -9,
    daily-section-5 all key the channel/campaign's channel field as
    `"channel"`) -- this is a schema-naming inference, not a guessed
    computation rule; the actual aggregation logic below (VAT/1.1, ROAS
    formula, rounding) is taken verbatim from monthly-section-8-media-
    comparison-table.md. Verify this key name against the live tool schema
    before relying on this mapper in production.
    """
    def _channel_totals(period, channel_key):
        channels = period.get("channels", [])
        match = next((c for c in channels if c.get("channel") == channel_key), None)
        actual = match["actual"] if match else []
        cost_sum = sum(row["cost"] for row in actual)
        revenue_sum = sum(row["revenue"] for row in actual)
        if channel_key.startswith("nvgfa_"):
            cost_sum = cost_sum / 1.1
        return cost_sum, revenue_sum

    rows_by_channel = []
    for channel_key, channel_label in _MONTHLY_CHANNEL_LABELS:
        prev_cost, prev_revenue = _channel_totals(data["prev"], channel_key)
        curr_cost, curr_revenue = _channel_totals(data["curr"], channel_key)

        def _roas(cost_sum, revenue_sum):
            if cost_sum == 0:
                # monthly-section-8.md requires every channel group to appear
                # even with zero spend, but doesn't document what ROAS should
                # show for a 0-spend channel (unlike executive-mtd-section-5,
                # which excludes null-ROAS rows entirely). Falling back to
                # 0.00 here mirrors monthly-section-6's documented "null ->
                # 0" fallback for change_pct rather than inventing a new rule.
                return 0.0
            return round(revenue_sum / cost_sum * 100, 2)

        rows_by_channel.append(
            {
                "channel_label": channel_label,
                "rows": [
                    {
                        "month_label": data["prev_month_label"],
                        "cost": prev_cost,
                        "revenue": prev_revenue,
                        "roas": _roas(prev_cost, prev_revenue),
                    },
                    {
                        "month_label": data["curr_month_label"],
                        "cost": curr_cost,
                        "revenue": curr_revenue,
                        "roas": _roas(curr_cost, curr_revenue),
                    },
                ],
            }
        )

    sections = [{"type": "heading", "text": "매체 별 성과 비교"}]
    for channel in rows_by_channel:
        sections.append(
            {
                "type": "table",
                "heading": channel["channel_label"],
                "headers": ["월", "광고비 (원)", "매출 (원)", "ROAS"],
                "rows": [
                    [
                        row["month_label"],
                        _fmt_amount(row["cost"]),
                        _fmt_amount(row["revenue"]),
                        f"{row['roas']:.2f}%",
                    ]
                    for row in channel["rows"]
                ],
            }
        )

    digest = {"media_monthly_comparison": rows_by_channel}
    return {"sections": sections, "digest": digest}


MAPPERS = {
    ("mtd", "A"): map_mtd_group_a,
    ("mtd", "B"): map_mtd_group_b,
    ("mtd", "C"): map_mtd_group_c,
    ("mtd", "D"): map_mtd_group_d,
    ("mtd", "E"): map_mtd_group_e,
    ("mtd", "F"): map_mtd_group_f,
    ("mtd", "G"): map_mtd_group_g,
    ("monthly", "A"): map_monthly_group_a,
    ("monthly", "B"): map_monthly_group_b,
    ("monthly", "C"): map_monthly_group_c,
    ("monthly", "D"): map_monthly_group_d,
}


def map_section(report_type, group, data):
    mapper = MAPPERS.get((report_type, group))
    if mapper is None:
        raise ValueError(f"unknown report_type/group: {report_type}/{group}")
    return mapper(data)
