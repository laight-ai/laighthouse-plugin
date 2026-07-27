"""Pure MCP-response -> {sections, digest} mappers, per report_type/group.

Field mappings mirror the rules documented in each
sections/<report_type>/*.md file exactly. This module is the *executor* of
those rules, not their source of truth -- if a .md file's mapping rule
changes, update the corresponding function here to match it, never the
other way around.

No network/MCP calls happen here: callers save a raw MCP response to a JSON
file and pass its parsed contents in.

BRANCH REGISTRATION SCHEME (daily only): `daily` is the only report_type whose
sections branch on brand ad-media (분기 A = Google/Meta brands, 분기 B = naver
brands) -- each section file documents both branches. Rather than overload one
mapper per group with an internal if/else (the two branches call different MCP
tools and consume structurally unrelated response shapes), each daily group
gets two separate functions and two separate MAPPERS registrations, keyed as
("daily", "<GROUP>_google_meta") / ("daily", "<GROUP>_naver"). The orchestrator
determines the branch once (per daily-section-1's rule, before dispatching any
subagent) and tells every subagent which of the two `--group` values to pass to
map_section.py -- see SKILL.md's "daily 전용" section.
"""

from datetime import date as _date
import calendar as _calendar


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

    `data`: dict parsed from the get_target_progress_v2 markdown response.
    """
    roas_goal_pct = _ratio_to_pct(data["target_roas"])
    roas_actual_pct = _ratio_to_pct(data["actual_roas"])
    budget_spent_rate = _ratio_to_pct(data["cost_progress_ratio"])
    revenue_achievement_rate = _ratio_to_pct(data["revenue_progress_ratio"])

    section1 = {
        "type": "kpi_cards",
        "heading": "월 목표 및 달성 현황",
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
                "accent": "#3b82f6",
                "diff": f"목표 {_fmt_amount(data['target_cost'])} · 소진 {_fmt_amount(data['actual_cost'])}",
            },
            {
                "label": "기간 목표 매출 대비 달성률",
                "value": f"{revenue_achievement_rate}%",
                "accent": "#16a34a",
                "diff": f"목표 {_fmt_amount(data['target_revenue'])} · 매출 {_fmt_amount(data['actual_revenue'])}",
            },
            {
                "label": "기간 누적 ROAS",
                "value": f"{roas_actual_pct}%",
                "accent": "#7c3aed",
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

    def _short_date(iso):
        _, month, day = iso.split("-")
        return f"{int(month)}/{int(day)}"

    # the HTML original draws this as a 5-line daily trend chart; the docx
    # renderer's line_chart type restores that instead of the table fallback
    section = {
        "type": "line_chart",
        "heading": "일일 카테고리별 매출 현황",
        "categories": [_short_date(label) for label in labels],
        "series": [
            {"name": cat, "values": [by_date[label].get(cat, 0) for label in labels]}
            for cat in top_categories
        ],
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

    def _row(r, label, bar_color):
        return [
            label,
            {"type": "bar", "pct": r["spent_rate"], "color": bar_color, "label": f"{r['spent_rate']}%"},
            _fmt_amount(r["budget_goal"]),
            _fmt_amount(r["spent"]),
            _fmt_amount(r["daily_budget"]),
            _fmt_amount(r["daily_spent_avg"]),
        ]

    table_rows = [_row(r, r["channel"], "3B82F6") for r in rows]
    table_rows.append(_row(total, "합계", "1E293B"))

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
        # original row count when the caller truncated items at the source
        # (SKILL.md's top-15 저장 규칙) so the renderer's "외 n행 생략"
        # caption reflects the full dataset, not the truncated file.
        "rows_total": data.get("items_total", len(items)),
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
        "rows_total": data.get("items_total", len(items)),
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
        "rows_total": data.get("items_total", len(items)),
    }
    return {"sections": [section], "digest": None}


# ---------------------------------------------------------------------------
# monthly
# ---------------------------------------------------------------------------


def map_monthly_group_a(data):
    """monthly-section-1 (월 목표 카드) + monthly-section-2 (목표 달성 현황).

    `data`: dict parsed from the get_target_progress_v2 markdown response (as_of_date = 해당 월 말일).
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
        "heading": "월 목표 및 달성 현황",
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

    def _short_date(iso):
        _, month, day = iso.split("-")
        return f"{int(month)}/{int(day)}"

    # multi-line daily trend, like the HTML original (see mtd group C)
    section7 = {
        "type": "line_chart",
        "heading": "일일 카테고리별 매출 현황",
        "categories": [_short_date(label) for label in date_labels],
        "series": [
            {"name": cat,
             "values": [by_date[label].get(cat, 0) for label in date_labels]}
            for cat in top5
        ],
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

    # one consolidated table (docx layout): a per-channel mini-table each with
    # its own numbered banner wasted a near-empty page per channel
    table_rows = []
    for channel in rows_by_channel:
        for row in channel["rows"]:
            table_rows.append([
                channel["channel_label"],
                row["month_label"],
                _fmt_amount(row["cost"]),
                _fmt_amount(row["revenue"]),
                f"{row['roas']:.2f}%",
            ])
    sections = [{
        "type": "table",
        "heading": "매체별 성과 비교",
        "headers": ["매체", "월", "광고비 (원)", "매출 (원)", "ROAS"],
        "rows": table_rows,
    }]

    digest = {"media_monthly_comparison": rows_by_channel}
    return {"sections": sections, "digest": digest}


# ---------------------------------------------------------------------------
# executive-mtd
# ---------------------------------------------------------------------------


def map_execmtd_group_a(data):
    """executive-mtd-section-1 (목표 달성 현황).

    `data`: dict parsed from the get_target_progress_v2 markdown response (as_of_date = target_date,
    partial month -- same call shape as mtd's, but executive-mtd has no
    separate kpi-goals card section, so this produces a single kpi_cards
    section instead of mtd_group_a's pair.
    """
    roas_goal_pct = _ratio_to_pct(data["target_roas"])
    roas_actual_pct = _ratio_to_pct(data["actual_roas"])
    budget_spent_rate = _ratio_to_pct(data["cost_progress_ratio"])
    revenue_achievement_rate = _ratio_to_pct(data["revenue_progress_ratio"])

    section = {
        "type": "kpi_cards",
        "heading": "목표 달성 현황",
        "cards": [
            {
                "label": "기간 예산대비 소진율",
                "value": f"{budget_spent_rate}%",
                "diff": f"목표 {_fmt_amount(data['target_cost'])} · 소진 {_fmt_amount(data['actual_cost'])}",
            },
            {
                "label": "기간 목표 매출 대비 달성률",
                "value": f"{revenue_achievement_rate}%",
                "diff": f"목표 {_fmt_amount(data['target_revenue'])} · 기간 매출 {_fmt_amount(data['actual_revenue'])}",
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
    return {"sections": [section], "digest": digest}


def map_execmtd_group_b(data):
    """executive-mtd-section-2 (월별 광고 성과 차트).

    `data`: raw get_naver_monthly_ad_performance response, identical shape
    and mapping to map_mtd_group_b. Unlike mtd's group B (digest=None),
    executive-mtd-section-3's Executive Summary explicitly lists this
    section's raw response as one of its inputs, so the digest carries the
    raw `items` through unmodified (same spirit as map_monthly_group_b).
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


def map_execmtd_group_c(data):
    """executive-mtd-section-4 (주요 카테고리별 월간 매출액 증감).

    `data`: {
      "curr": <get_naver_category_sales response, 이번 달 MTD(1일~target_date)>,
      "prev": <get_naver_category_sales response, 전월 동일 기간(1일~day-of-month
               매칭, clamp)>,
    }
    Each is shaped {"items": [{"category", "sales"}, ...]}. The curr/prev
    date-range computation itself (day-of-month matching + clamp to the
    previous month's last day) happens in the caller, before this function
    ever sees the data -- this function only does the MoM arithmetic
    documented in executive-mtd-section-4-category-mom-highlights.md.

    ASSUMPTION (flagged, no concrete example covers this): the .md file
    computes mom_pct only for categories present in `prev` with a non-zero
    value, and separately flags prev==0 categories as "신규" excluded "from
    the calculation" -- but it never states whether/how 신규 categories
    interact with the |mom_pct|>=10 / min-3 / max-6 selection window (the
    file's own worked example has no 신규 entries). This function treats
    신규 categories as always-shown highlights, appended after the
    threshold-based selection (uncapped by the 3/6 window, which the .md
    only ties to the mom_pct-ranked list) -- this specific interaction is an
    assumption, not a documented rule; flag before relying on it for a real
    six-plus-new-category brand.
    """
    curr_map = {row["category"]: row["sales"] for row in data["curr"]["items"]}
    prev_map = {row["category"]: row["sales"] for row in data["prev"]["items"]}
    all_categories = sorted(set(curr_map) | set(prev_map))

    new_categories = []
    ranked = []
    for cat in all_categories:
        curr_val = curr_map.get(cat, 0)
        prev_val = prev_map.get(cat, 0)
        if prev_val == 0:
            new_categories.append(cat)
        else:
            mom_pct = round((curr_val - prev_val) / prev_val * 100, 1)
            ranked.append((cat, mom_pct))

    ranked.sort(key=lambda kv: abs(kv[1]), reverse=True)

    if not ranked and not new_categories:
        cards = [{"label": "안내", "value": "이번 기간 카테고리별 매출 변동이 두드러지지 않았습니다"}]
        return {"sections": [{"type": "kpi_cards", "cards": cards}], "digest": {"category_mom_highlights": []}}

    above_threshold = [item for item in ranked if abs(item[1]) >= 10]
    if len(above_threshold) < 3:
        selected = ranked[:3]
    else:
        selected = above_threshold[:6]

    highlights = [{"category": cat, "mom_pct": pct} for cat, pct in selected]
    highlights += [{"category": cat, "mom_pct": None} for cat in new_categories]

    if not highlights:
        cards = [{"label": "안내", "value": "이번 기간 카테고리별 매출 변동이 두드러지지 않았습니다"}]
        return {"sections": [{"type": "kpi_cards", "cards": cards}], "digest": {"category_mom_highlights": []}}

    cards = []
    for item in highlights:
        if item["mom_pct"] is None:
            cards.append({"label": item["category"], "value": "신규"})
        else:
            pct = item["mom_pct"]
            change_label = f"+{pct}%" if pct > 0 else f"{pct}%"
            cards.append({"label": item["category"], "value": change_label, "diff_value": pct})

    section = {"type": "kpi_cards", "heading": "주요 카테고리별 월간 매출액 증감", "cards": cards}
    digest = {"category_mom_highlights": highlights}
    return {"sections": [section], "digest": digest}


_EXECMTD_CHANNEL_LABELS = [
    ("nvad:BRS", "네이버 브랜드검색"),
    ("nvad:PLINK", "네이버 파워링크"),
    ("nvad:NVSHOP", "네이버 쇼핑검색"),
    ("nvgfa_ad:", "네이버 GFA 애드부스트"),
]


def map_execmtd_group_d(data):
    """executive-mtd-section-5 (매체별 성과 비교).

    `data`: {
      "curr": <get_naver_channel_progression response, 이번 달>,
      "curr_as_of_date": "2026-03-15",
      "prev": <get_naver_channel_progression response, 전월>,
      "prev_as_of_date": "2026-02-15",   # day-of-month matched, clamp to
                                          # prev month's last day -- computed
                                          # by the caller, same rule as group C
      "curr_period_label": "3월",
      "prev_period_label": "2월",
    }
    Each of curr/prev shaped {"channels": [{"channel": "...", "actual": [{"date","cost","revenue"}, ...]}]}
    (same inferred raw shape as map_monthly_group_d -- see that function's
    docstring for the schema-naming caveat).

    Unlike get_naver_channel_progression's monthly-report usage, this
    function must itself apply the `date <= as_of_date` cutoff (the tool
    always returns the full calendar month) before summing -- per
    executive-mtd-section-5.md's explicit instruction that the skill (not
    the tool) performs this truncation. nvgfa_dp: is excluded entirely (not
    just from the label table) per the .md's explicit exclusion rule.
    """
    def _channel_totals(period, as_of_date, channel_key):
        channels = period.get("channels", [])
        match = next((c for c in channels if c.get("channel") == channel_key), None)
        actual = match["actual"] if match else []
        actual = [row for row in actual if row["date"] <= as_of_date]
        cost_sum = sum(row["cost"] for row in actual)
        revenue_sum = sum(row["revenue"] for row in actual)
        if channel_key.startswith("nvgfa_"):
            cost_sum = cost_sum / 1.1
        return cost_sum, revenue_sum

    rows = []
    for channel_key, channel_label in _EXECMTD_CHANNEL_LABELS:
        prev_cost, prev_revenue = _channel_totals(data["prev"], data["prev_as_of_date"], channel_key)
        curr_cost, curr_revenue = _channel_totals(data["curr"], data["curr_as_of_date"], channel_key)

        prev_roas = None if prev_cost == 0 else (prev_revenue / prev_cost * 100)
        curr_roas = None if curr_cost == 0 else (curr_revenue / curr_cost * 100)
        if prev_roas is None or curr_roas is None:
            continue

        change_pp = round(curr_roas - prev_roas, 1)
        rows.append(
            {
                "channel_label": channel_label,
                "prev_roas": round(prev_roas, 1),
                "curr_roas": round(curr_roas, 1),
                "change_pp": change_pp,
            }
        )

    rows.sort(key=lambda r: r["change_pp"])

    if not rows:
        return {"sections": [], "digest": {"media_roas_comparison": None}}

    table_rows = [
        [
            row["channel_label"],
            f"{row['prev_roas']}%",
            f"{row['curr_roas']}%",
            (f"+{row['change_pp']}%p" if row["change_pp"] > 0 else f"{row['change_pp']}%p"),
        ]
        for row in rows
    ]
    section = {
        "type": "table",
        "heading": "매체별 성과 비교",
        "headers": ["채널", f"{data['prev_period_label']} ROAS", f"{data['curr_period_label']} ROAS", "변동"],
        "rows": table_rows,
    }
    digest = {
        "media_roas_comparison": {
            "prev_period_label": data["prev_period_label"],
            "curr_period_label": data["curr_period_label"],
            "rows": rows,
        }
    }
    return {"sections": [section], "digest": digest}


# ---------------------------------------------------------------------------
# daily
# ---------------------------------------------------------------------------
#
# See the module docstring for the branch registration scheme. Group letters
# mirror the section numbers they cover: A=1+2 (kpi 카드 쌍), B=4 (최근 7일
# 차트), C=5 (캠페인 성과 표), D=6 (광고그룹/키워드 표). Section 3(Executive
# Summary)는 ANALYSIS 섹션이라 여기 없다 -- 아래 각 함수의 digest 문서 참고.


def _signed(value):
    """Sign-prefixed number string: >0 gets a literal '+', <=0 prints as-is
    (its own '-' already carries the sign) -- same convention already used by
    map_execmtd_group_c's change_label for diff_value-bearing cards.
    """
    return f"+{value}" if value > 0 else f"{value}"


def map_daily_group_a_google_meta(data):
    """daily-section-1 (월 목표 카드) + daily-section-2 (Overview), 분기 A (Google/Meta).

    `data`: raw `target_progress` (v1, generic) response, shaped
    {"sales": {...}} -- every field daily-section-1/2.md documents
    (`sales.budget_goal`, `sales.period_progress_pct`, `sales.roas_achievement_diff`,
    etc.) is already computed by the tool; this function only formats/composes
    strings, it does not (re)compute any ratio or diff.
    """
    sales = data["sales"]

    section1 = {
        "type": "kpi_cards",
        "heading": "Monthly Goals & Achievement",
        "cards": [
            {"label": "Monthly Budget Plan", "value": f"${_fmt_amount(sales['budget_goal'])}"},
            {"label": "Monthly Revenue Target", "value": f"${_fmt_amount(sales['revenue_goal'])}"},
            {"label": "Monthly ROAS Target", "value": f"{sales['roas_goal']}%"},
        ],
    }
    section2 = {
        "type": "kpi_cards",
        "cards": [
            {
                "label": "Period Progress",
                "value": f"{sales['period_progress_pct']}% ({sales['period_label']})",
            },
            {
                "label": "Monthly Budget Utilization",
                "value": f"{sales['budget_utilization_pct']}% ({_signed(sales['budget_utilization_diff'])}%p)",
                "diff": f"Target ${_fmt_amount(sales['budget_goal'])} · Current ${_fmt_amount(sales['budget_spent'])}",
                "diff_value": sales["budget_utilization_diff"],
            },
            {
                "label": "Monthly Revenue Achievement",
                "value": f"{sales['revenue_achievement_pct']}% ({_signed(sales['revenue_achievement_diff'])}%p)",
                "diff": f"Target ${_fmt_amount(sales['revenue_goal'])} · Current ${_fmt_amount(sales['revenue_actual'])}",
                "diff_value": sales["revenue_achievement_diff"],
            },
            {
                "label": "Monthly ROAS Achievement",
                "value": f"{sales['roas_achievement_pct']}% ({_signed(sales['roas_achievement_diff'])}%p)",
                "diff": f"Target {sales['roas_goal']}% · Current {sales['roas_actual']}%",
                "diff_value": sales["roas_achievement_diff"],
            },
        ],
    }
    # Consumed by daily-section-3 분기 A (its step 1 explicitly reuses this
    # same target_progress call before authoring the summary).
    digest = {
        "period_progress_pct": sales["period_progress_pct"],
        "budget_utilization_pct": sales["budget_utilization_pct"],
        "budget_utilization_diff": sales["budget_utilization_diff"],
        "revenue_achievement_pct": sales["revenue_achievement_pct"],
        "revenue_achievement_diff": sales["revenue_achievement_diff"],
        "roas_achievement_pct": sales["roas_achievement_pct"],
        "roas_achievement_diff": sales["roas_achievement_diff"],
        "budget_goal": sales["budget_goal"],
        "budget_spent": sales["budget_spent"],
        "revenue_goal": sales["revenue_goal"],
        "revenue_actual": sales["revenue_actual"],
        "roas_goal": sales["roas_goal"],
        "roas_actual": sales["roas_actual"],
    }
    return {"sections": [section1, section2], "digest": digest}


def map_daily_group_a_naver(data):
    """daily-section-1 (월 목표 카드) + daily-section-2 (목표 달성 현황), 분기 B (naver).

    `data`: dict parsed from the get_target_progress_v2 markdown response
    ({"target_cost","target_revenue","target_roas","actual_cost","actual_revenue",
    "actual_roas","cost_progress_ratio","revenue_progress_ratio"}) plus one
    caller-supplied field, "as_of_date" (the same target_date string already
    passed as the MCP call's `as_of_date` param) -- the tool's response has no
    date/month field, so `period_progress_pct`/`period_label` (day-of-month /
    days-in-month, per daily-section-2.md's explicit formula) can only be
    computed here given that one extra string. This mirrors the existing
    caller-supplied-label convention (map_monthly_group_c's month labels,
    map_execmtd_group_d's period labels) rather than inventing a new pattern.

    digest=None: unlike 분기 A, daily-section-3 분기 B's data-collection list
    does NOT reuse this call at all -- its top_bullet is built from
    get_naver_daily_attributed_sales (daily-section-4's call, see
    map_daily_group_b_naver's digest) plus separate campaign/ad-group/promotion
    calls, never from get_target_progress_v2. Documented explicitly so a
    future editor doesn't assume symmetry with 분기 A.
    """
    as_of = _date.fromisoformat(data["as_of_date"])
    days_in_month = _calendar.monthrange(as_of.year, as_of.month)[1]
    period_progress_pct = round(as_of.day / days_in_month * 100, 1)
    period_label = f"{as_of.day}/{days_in_month}일"

    roas_goal_pct = _ratio_to_pct(data["target_roas"])
    roas_actual_pct = _ratio_to_pct(data["actual_roas"])
    budget_spent_rate = _ratio_to_pct(data["cost_progress_ratio"])
    revenue_achievement_rate = _ratio_to_pct(data["revenue_progress_ratio"])

    # budget/revenue diffs are relative to period_progress_pct (pace vs. an
    # evenly-spread expectation), NOT vs. the target -- per daily-section-2.md's
    # explicit warning that this differs from ROAS diff (target-relative).
    budget_spent_diff = round(budget_spent_rate - period_progress_pct, 1)
    revenue_achievement_diff = round(revenue_achievement_rate - period_progress_pct, 1)
    roas_diff = round(roas_actual_pct - roas_goal_pct, 1)

    section1 = {
        "type": "kpi_cards",
        "heading": "월 목표 및 달성 현황",
        "cards": [
            {"label": "월 예산 목표", "value": _fmt_amount(data["target_cost"])},
            {"label": "월 매출 목표", "value": _fmt_amount(data["target_revenue"])},
            {"label": "월 ROAS 목표", "value": f"{roas_goal_pct}%"},
        ],
    }
    section2 = {
        "type": "kpi_cards",
        "cards": [
            {"label": "기간 진척률", "value": f"{period_progress_pct}% ({period_label})"},
            {
                "label": "월 예산대비 소진율",
                "value": f"{budget_spent_rate}% ({_signed(budget_spent_diff)}%p)",
                "diff": f"목표 ₩{_fmt_amount(data['target_cost'])} · 소진비용 ₩{_fmt_amount(data['actual_cost'])}",
                "diff_value": budget_spent_diff,
            },
            {
                "label": "월 목표 매출 대비 달성률",
                "value": f"{revenue_achievement_rate}% ({_signed(revenue_achievement_diff)}%p)",
                "diff": f"목표 ₩{_fmt_amount(data['target_revenue'])} · 매출 ₩{_fmt_amount(data['actual_revenue'])}",
                "diff_value": revenue_achievement_diff,
            },
            {
                "label": "월 누적 ROAS",
                "value": f"{roas_actual_pct}% ({_signed(roas_diff)}%p)",
                "diff": f"목표 {roas_goal_pct}%",
                "diff_value": roas_diff,
            },
        ],
    }
    return {"sections": [section1, section2], "digest": None}


def map_daily_group_b_google_meta(data):
    """daily-section-4 (최근 7일 성과), 분기 A (Google/Meta).

    `data`: raw get_sales_performance_daily response, shaped
    {"sales_daily": {"labels","revenue","ad_spend","roas"}} -- all four arrays
    already computed by the tool.
    """
    sd = data["sales_daily"]
    section = {
        "type": "chart",
        "heading": "Sales campaign: Daily performance in the last 7 days",
        "categories": sd["labels"],
        "bar_series": [
            {"name": "Revenue", "values": sd["revenue"]},
            {"name": "Ad Spend", "values": sd["ad_spend"]},
        ],
        "line_series": {"name": "ROAS", "values": sd["roas"]},
    }
    return {"sections": [section], "digest": None}


_DAILY_KOREAN_WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


def map_daily_group_b_naver(data):
    """daily-section-4 (최근 7일 성과), 분기 B (naver).

    `data`: raw get_naver_daily_attributed_sales response, shaped
    {"items": [{"logdate","ad_cost","revenue", ...}, ...]} ("items" as the
    top-level key is inferred from every other naver MCP tool response
    documented in this skill -- daily-section-4.md itself has no literal raw
    JSON example, only the field list -- verify against the live tool schema).
    `roas` is not returned by the tool; per daily-section-4.md this skill
    computes it (`revenue / ad_cost * 100`). 0-cost days fall back to
    roas=0.0, mirroring map_monthly_group_d's documented 0-spend fallback
    (no rule is documented for this edge case here, but that's the closest
    precedent in this file rather than inventing a new one).
    """
    items = data["items"]
    labels, revenue, ad_spend, roas = [], [], [], []
    digest_items = []
    for item in items:
        d = _date.fromisoformat(item["logdate"])
        labels.append(f"{d.month}/{d.day}({_DAILY_KOREAN_WEEKDAYS[d.weekday()]})")
        revenue.append(item["revenue"])
        ad_spend.append(item["ad_cost"])
        item_roas = round(item["revenue"] / item["ad_cost"] * 100, 2) if item["ad_cost"] else 0.0
        roas.append(item_roas)
        digest_items.append({**item, "roas": item_roas})

    section = {
        "type": "chart",
        "heading": "최근 7일 성과",
        "categories": labels,
        "bar_series": [
            {"name": "매출", "values": revenue},
            {"name": "광고비", "values": ad_spend},
        ],
        "line_series": {"name": "ROAS", "values": roas},
    }
    # Consumed by daily-section-3 분기 B's top_bullet (오늘 vs. 비교 기준 기간
    # 평균) -- the orchestrator still needs its own additional
    # get_naver_sa_performance_daily/list_promotions calls for the
    # campaign/ad-group bullets; see SKILL.md's "daily 전용" section.
    digest = {"daily_items": digest_items}
    return {"sections": [section], "digest": digest}


def map_daily_group_c_google_meta(data):
    """daily-section-5 (캠페인 성과), 분기 A (Google/Meta).

    `data`: raw get_sales_by_campaign_monthly response, shaped
    {"sales_by_campaign": [{"media","campaign","impression","click","ctr",
    "cost","revenue","roas"}, ...]}. `ctr`/`roas` are placed as-is (the table
    headers already carry the "(%)" unit, so no suffix is appended here).
    """
    items = data["sales_by_campaign"]
    rows = [
        [
            item["media"],
            item["campaign"],
            _fmt_amount(item["impression"]),
            _fmt_amount(item["click"]),
            item["ctr"],
            _fmt_amount(item["cost"]),
            _fmt_amount(item["revenue"]),
            item["roas"],
        ]
        for item in items
    ]
    section = {
        "type": "table",
        "heading": "Performance by Campaign",
        "headers": ["Media", "Campaign", "Impression", "Click", "CTR (%)", "Cost ($)", "Revenue ($)", "ROAS (%)"],
        "rows": rows,
    }
    return {"sections": [section], "digest": None}


_DAILY_NAVER_CHANNEL_LABELS = {
    "BRS": "네이버 브랜드검색",
    "PLINK": "네이버 파워링크",
    "NVSHOP": "네이버 쇼핑검색",
}


def map_daily_group_c_naver(data):
    """daily-section-5 (캠페인 성과), 분기 B (naver).

    `data`: raw get_naver_campaign_performance response
    ({"items": [{"campaign","channel","revenue","ad_cost","roas","impressions",
    "clicks","ctr","cpc","purchases"}, ...]}). `ctr`/`roas` already arrive
    percentage-scale (no x100). `cpm` isn't in the response; computed here as
    `ad_cost / impressions * 1000` per daily-section-5.md's explicit formula.
    Rows with `ad_cost < 10,000` are dropped (2026-07-23 rule); if that leaves
    nothing, an "안내" kpi_cards fallback replaces the table (same shape as
    map_execmtd_group_c's no-highlights fallback) instead of an empty table.

    ⚠️ FLAGGED cpm formula: daily-section-5.md's prose states
    `cpm = ad_cost / impressions × 1000`, but its own literal example
    (revenue 4,441,630 / ad_cost 494,112 / impressions 5,901 -- the same row
    reused for daily-section-6's worked example) is a naver-style cpc/roas
    table with `cpc: 720.28` documented alongside it; no cpm value is given
    in section-5's own example, but the *identical row* is used again in
    daily-section-6.md's worked cpm example there, where `cost/impressions`
    (WITHOUT `x 1000`) is what reproduces the documented result. Since both
    section-5 and section-6 state the same formula prose and section-6's
    worked numbers only match without the `x 1000`, this function follows
    the worked example (`ad_cost / impressions`, no `x 1000`) here too for
    consistency, treating the "x 1000" in both .md files' prose as a
    copy-paste error from the standard CPM definition -- verify against a
    live tool response before trusting this in production.

    digest=None -- daily-section-3 분기 B's campaign-level bullets are sourced
    from get_naver_sa_performance_daily(group_by="campaign") across two date
    ranges (target_date + a comparison baseline), not from this single-day
    get_naver_campaign_performance call, so this section's output isn't a
    valid digest source for section 3 (see SKILL.md's "daily 전용" section).
    """
    filtered = [item for item in data["items"] if item["ad_cost"] >= 10000]
    if not filtered:
        cards = [{"label": "안내", "value": "이번 기간 10,000원 이상 집행된 캠페인이 없음"}]
        return {"sections": [{"type": "kpi_cards", "cards": cards}], "digest": None}

    rows = []
    for item in filtered:
        cpm = round(item["ad_cost"] / item["impressions"], 2) if item["impressions"] else None
        rows.append(
            [
                _DAILY_NAVER_CHANNEL_LABELS.get(item["channel"], item["channel"]),
                item["campaign"],
                _fmt_amount(item["impressions"]),
                _fmt_amount(item["clicks"]),
                _fmt_amount(item["ad_cost"]),
                _fmt_amount(item["cpc"]),
                f"{item['ctr']}%",
                _fmt_amount(cpm) if cpm is not None else "-",
                item["purchases"],
                _fmt_amount(item["revenue"]),
                f"{item['roas']}%",
            ]
        )
    section = {
        "type": "table",
        "heading": "캠페인 성과",
        "headers": ["광고 채널", "캠페인", "노출", "클릭", "광고비", "CPC", "CTR", "CPM", "구매건수", "매출", "ROAS"],
        "rows": rows,
    }
    return {"sections": [section], "digest": None}


def map_daily_group_d_google_meta(data):
    """daily-section-6 (광고 그룹 및 키워드 성과), 분기 A (Google/Meta).

    `data`: raw get_sales_by_asset_group_monthly response, shaped
    {"sales_by_asset_group": [{"media","campaign","asset_group","impression",
    "click","ctr","cost","revenue"}, ...]} -- no ROAS column (PMax asset
    groups have no keyword targeting, per daily-section-6.md).
    """
    items = data["sales_by_asset_group"]
    rows = [
        [
            item["media"],
            item["campaign"],
            item["asset_group"],
            _fmt_amount(item["impression"]),
            _fmt_amount(item["click"]),
            item["ctr"],
            _fmt_amount(item["cost"]),
            _fmt_amount(item["revenue"]),
        ]
        for item in items
    ]
    section = {
        "type": "table",
        "heading": "Performance by Asset group",
        "headers": ["Media", "Campaign", "Asset Group", "Impression", "Click", "CTR (%)", "Cost ($)", "Revenue ($)"],
        "rows": rows,
    }
    return {"sections": [section], "digest": None}


def _daily_naver_node_metrics(imp, click, cost, conv_cnt, conv_amnt):
    """ctr/cpc/cpm/roas from raw imp/click/cost_exc_vat/gross_conv_cnt/
    gross_conv_amnt, per daily-section-6.md step 3. cpc/roas are `None` when
    their denominator (click/cost) is 0, per the .md's explicit "-" display
    rule; ctr/cpm defensively do the same for a 0-impression node even though
    the .md doesn't call that case out (it should never occur for a row that
    already cleared the >=10,000 ad_cost filter, but this avoids a
    ZeroDivisionError instead of guessing a display value).

    Rounded to 2 decimals -- the .md states the four formulas but not a
    decimal count; 2 decimals matches the precision of every other
    naver-computed ratio metric already in this file (map_mtd_group_e's cpc,
    map_daily_group_c_naver's cpm, etc.), so this follows that established
    convention rather than inventing a new one.

    ⚠️ FLAGGED cpm formula: daily-section-6.md's prose says
    `cpm = cost_exc_vat / imp × 1000`, but its own worked example (group node
    cpm=101.4 from imp=1315/ad_cost=133321; keyword node cpm=81.6 from
    imp=320/ad_cost=26100) only reproduces as plain `cost / imp` -- WITHOUT
    the `x 1000` (with it, the same inputs give ~101,381 / ~81,562, nowhere
    near the documented 101.4/81.6). See map_daily_group_c_naver's matching
    flag for daily-section-5's identical formula text/example conflict; both
    functions consistently follow the worked examples (`cost / imp`, no
    `x 1000`) rather than the prose, on the theory that "x 1000" is a
    copy-paste artifact of the standard CPM definition in this .md. Verify
    against a live tool response before trusting this in production.
    """
    ctr = round(click / imp * 100, 2) if imp else None
    cpc = round(cost / click, 2) if click else None
    cpm = round(cost / imp, 2) if imp else None
    roas = round(conv_amnt / cost * 100, 2) if cost else None
    return {
        "impressions": imp,
        "clicks": click,
        "ad_cost": cost,
        "cpc": cpc,
        "ctr": ctr,
        "cpm": cpm,
        "purchases": conv_cnt,
        "revenue": conv_amnt,
        "roas": roas,
    }


def _daily_naver_fmt_ratio(value, suffix=""):
    return "-" if value is None else f"{value}{suffix}"


def map_daily_group_d_naver(data):
    """daily-section-6 (광고 그룹 및 키워드 성과), 분기 B (naver).

    `data`: {"ad_group": <get_naver_sa_performance_daily group_by="ad-group"
    응답>, "keyword": <동일 도구 group_by="keyword" 응답>}, each shaped
    {"items": [{"nvr_media_type","campaign_name","group_name","imp","click",
    "cost_exc_vat","gross_conv_cnt","gross_conv_amnt", ...}, ...]} (keyword
    items additionally carry "term"). Both calls target the same single
    target_date -- daily is always a one-day snapshot for this section.

    Processing (per daily-section-6.md steps 1-5, mechanical only -- no value
    is invented/re-estimated, matching the "데이터 처리 원칙" exception this
    file already documents for tree-building/filtering):
    1. Drop keyword rows with term=="-".
    2. Group keyword rows by (nvr_media_type, campaign_name, group_name) as
       children of the matching ad-group row.
    3. Compute ctr/cpc/cpm/roas per node (see _daily_naver_node_metrics).
    4. Map nvr_media_type -> channel_label.
    5. Drop any node (group OR keyword, independently) with ad_cost<10,000;
       cap each group's remaining children to the top 20 by revenue (ties by
       ad_cost), appending a "외 N개 키워드" placeholder row for the rest.

    digest=None -- same reasoning as map_daily_group_c_naver: daily-section-3
    분기 B's ad-group-level bullets need a *comparison-period* call to this
    same tool (not just target_date), which this group doesn't fetch.
    """
    keyword_items = [item for item in data["keyword"]["items"] if item.get("term") != "-"]

    def _key(item):
        return (item["nvr_media_type"], item["campaign_name"], item["group_name"])

    children_by_key = {}
    for kw in keyword_items:
        metrics = _daily_naver_node_metrics(
            kw["imp"], kw["click"], kw["cost_exc_vat"], kw["gross_conv_cnt"], kw["gross_conv_amnt"]
        )
        if metrics["ad_cost"] < 10000:
            continue
        children_by_key.setdefault(_key(kw), []).append({"keyword": kw["term"], **metrics})

    groups = []
    for g in data["ad_group"]["items"]:
        metrics = _daily_naver_node_metrics(
            g["imp"], g["click"], g["cost_exc_vat"], g["gross_conv_cnt"], g["gross_conv_amnt"]
        )
        if metrics["ad_cost"] < 10000:
            continue
        children = sorted(children_by_key.get(_key(g), []), key=lambda c: (-c["revenue"], -c["ad_cost"]))
        truncated = len(children) - 20 if len(children) > 20 else None
        groups.append(
            {
                "channel_label": _DAILY_NAVER_CHANNEL_LABELS.get(g["nvr_media_type"], g["nvr_media_type"]),
                "campaign": g["campaign_name"],
                "group": g["group_name"],
                "children": children[:20],
                "children_truncated": truncated,
                **metrics,
            }
        )
    groups.sort(key=lambda g: (-g["revenue"], -g["ad_cost"]))

    if not groups:
        cards = [{"label": "안내", "value": "이번 기간 10,000원 이상 집행된 광고그룹이 없음"}]
        return {"sections": [{"type": "kpi_cards", "cards": cards}], "digest": None}

    rows = []
    for g in groups:
        rows.append(
            [
                f"{g['channel_label']} / {g['campaign']}",
                g["group"],
                "전체",
                _fmt_amount(g["impressions"]),
                _fmt_amount(g["clicks"]),
                _fmt_amount(g["ad_cost"]),
                _daily_naver_fmt_ratio(g["cpc"]),
                _daily_naver_fmt_ratio(g["ctr"], "%"),
                _daily_naver_fmt_ratio(g["cpm"]),
                g["purchases"],
                _fmt_amount(g["revenue"]),
                _daily_naver_fmt_ratio(g["roas"], "%"),
            ]
        )
        for c in g["children"]:
            rows.append(
                [
                    "",
                    "",
                    f"└ {c['keyword']}",
                    _fmt_amount(c["impressions"]),
                    _fmt_amount(c["clicks"]),
                    _fmt_amount(c["ad_cost"]),
                    _daily_naver_fmt_ratio(c["cpc"]),
                    _daily_naver_fmt_ratio(c["ctr"], "%"),
                    _daily_naver_fmt_ratio(c["cpm"]),
                    c["purchases"],
                    _fmt_amount(c["revenue"]),
                    _daily_naver_fmt_ratio(c["roas"], "%"),
                ]
            )
        if g["children_truncated"]:
            rows.append(["", "", f"└ 외 {g['children_truncated']}개 키워드", "", "", "", "", "", "", "", "", ""])

    section = {
        "type": "table",
        "heading": "광고 그룹 및 키워드 성과",
        "headers": ["채널 / 캠페인", "광고그룹", "키워드", "노출", "클릭", "광고비", "CPC", "CTR", "CPM", "구매건수", "매출", "ROAS"],
        "rows": rows,
    }
    return {"sections": [section], "digest": None}


# ---------------------------------------------------------------------------
# creative (소재 성과 보고서)
# ---------------------------------------------------------------------------


def _parse_md_table(payload):
    """Parse a `{"result": "<markdown table>"}` tool response (the generic
    `get_ad_*_table` family returns markdown, not JSON) into row dicts.
    Returns [] for the tool's literal "_No data_" response."""
    text = payload["result"] if isinstance(payload, dict) else payload
    if not text or "_No data_" in text:
        return []
    lines = [line.strip() for line in str(text).splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return []
    def _cells(line):
        return [c.strip() for c in line.strip().strip("|").split("|")]
    headers = _cells(lines[0])
    rows = []
    for line in lines[2:]:  # lines[1] is the --- separator
        cells = _cells(line)
        rows.append({h: (cells[i] if i < len(cells) else "") for i, h in enumerate(headers)})
    return rows


def _md_num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _creative_identity(row):
    """소재 식별자: ad_name 우선, 비어 있으면 asset_group(광고세트)로 폴백 —
    실측상 group_by="ad-set" 응답은 ad_name이 빈 문자열이다."""
    return row.get("ad_name") or row.get("asset_group") or "(이름 없음)"


def _aggregate_creatives(rows):
    """Daily rows -> per-소재 totals. Sums are plain additions; ctr/roas are
    recomputed from the summed numerators/denominators (the daily ratios
    cannot be averaged) — documented in creative-section-1.md."""
    totals = {}
    for row in rows:
        key = _creative_identity(row)
        t = totals.setdefault(key, {
            "name": key, "campaign": row.get("campaign_name", ""),
            "media": row.get("media", ""), "creative_id": row.get("creative_id", ""),
            "cost": 0.0, "impression": 0.0, "click": 0.0,
            "purchase_count": 0.0, "purchase_amount": 0.0, "video_view": 0.0,
        })
        for field in ("cost", "impression", "click", "purchase_count",
                      "purchase_amount", "video_view"):
            t[field] += _md_num(row.get(field))
    for t in totals.values():
        t["ctr"] = round(t["click"] / t["impression"] * 100, 2) if t["impression"] else 0.0
        t["cpc"] = round(t["cost"] / t["click"], 2) if t["click"] else 0.0
        t["roas"] = round(t["purchase_amount"] / t["cost"] * 100, 1) if t["cost"] else 0.0
    return sorted(totals.values(), key=lambda t: t["cost"], reverse=True)


def map_creative_group_a(data):
    """creative-section-1 (소재별 성과 요약) + creative-section-2 (상위 소재
    일별 매출 추이).

    `data`: raw get_ad_performance_daily_table response
    ({"result": "<markdown>"}, group_by="ad" — 서버가 ad 그레인을 못 내는
    동안은 group_by="ad-set"을 소재 근사치로 쓴다, creative-section-1.md 참고).
    """
    rows = _parse_md_table(data)
    creatives = _aggregate_creatives(rows)

    total_cost = sum(t["cost"] for t in creatives)
    total_amount = sum(t["purchase_amount"] for t in creatives)
    overall_roas = round(total_amount / total_cost * 100, 1) if total_cost else 0.0
    cards_section = {
        "type": "kpi_cards",
        "heading": "소재 성과 개요",
        "cards": [
            {"label": "집행 소재 수", "value": _fmt_amount(len(creatives))},
            {"label": "총 광고비", "value": _fmt_amount(round(total_cost))},
            {"label": "총 전환 매출", "value": _fmt_amount(round(total_amount))},
            {"label": "전체 ROAS", "value": f"{overall_roas}%",
             "accent": "#3b82f6", "diff": f"광고비 {_fmt_amount(round(total_cost))} 기준"},
        ],
    }

    table_section = {
        "type": "table",
        "heading": "소재별 성과",
        "headers": ["소재", "캠페인", "광고비", "노출", "클릭", "CTR", "CPC",
                    "구매", "매출", "ROAS"],
        "rows": [
            [t["name"], t["campaign"], _fmt_amount(round(t["cost"])),
             _fmt_amount(round(t["impression"])), _fmt_amount(round(t["click"])),
             f"{t['ctr']}%", _fmt_amount(t["cpc"]), _fmt_amount(round(t["purchase_count"])),
             _fmt_amount(round(t["purchase_amount"])), f"{t['roas']}%"]
            for t in creatives
        ],
        "rows_total": len(creatives),
    }

    # daily trend for the top-5 creatives by spend. Revenue by default;
    # brands with no purchase conversion tracked (총 매출 0 — breezm 등)
    # fall back to daily spend so the chart still carries signal.
    trend_field = "purchase_amount" if total_amount else "cost"
    trend_label = "매출" if total_amount else "광고비"
    top5 = [t["name"] for t in creatives[:5]]
    by_date = {}
    for row in rows:
        key = _creative_identity(row)
        if key in top5:
            by_date.setdefault(row.get("logdate", ""), {}).setdefault(key, 0.0)
            by_date[row["logdate"]][key] += _md_num(row.get(trend_field))
    labels = sorted(d for d in by_date if d)

    def _short_date(iso):
        parts = iso.split("-")
        return f"{int(parts[1])}/{int(parts[2])}" if len(parts) == 3 else iso

    chart_section = {
        "type": "line_chart",
        "heading": f"상위 소재 일별 {trend_label} 추이",
        "categories": [_short_date(d) for d in labels],
        "series": [
            {"name": name, "values": [round(by_date[d].get(name, 0.0)) for d in labels]}
            for name in top5
        ],
    }

    digest = {
        "total_cost": round(total_cost), "total_amount": round(total_amount),
        "overall_roas": overall_roas,
        "top_creatives": creatives[:5],
        "bottom_creatives": [t for t in creatives if t["cost"] > 0][-3:],
    }
    return {"sections": [cards_section, table_section, chart_section], "digest": digest}


def _normalize_creative_id(value):
    """creative_id normalization across sources: the markdown table may carry
    '456' / '456.0' / '', the info response carries int 456."""
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def map_creative_group_b(data):
    """creative-section-3 (소재 썸네일 · 성과 매칭).

    `data`: {"creative": <get_ad_creative_info 응답 그대로>, "performance":
    <get_ad_performance_daily_table 응답 — 그룹 A와 동일 파일 재사용>}.

    get_ad_creative_info 실측 스키마 (laighthouse-prism 1.27.0, 2026-07-27):
    응답은 {"google": [...], "meta": [...], "tiktok": [...]}, 각 항목은
    {account_id, creative_id, thumbnail_image_url, thumbnail_image_data_url}
    — data URL은 base64 인라인 썸네일(최대 20개/호출, 실패 시 null).
    성과와의 조인 키는 creative_id (성과 markdown의 creative_id 컬럼,
    group_by="ad" 그레인에서만 채워진다).
    """
    creative_payload = data.get("creative") or {}
    info_items = []
    for platform in ("google", "meta", "tiktok"):
        for item in creative_payload.get(platform, []) or []:
            info_items.append({**item, "platform": platform})

    perf = _aggregate_creatives(_parse_md_table(data.get("performance") or {}))
    perf_by_id = {}
    for t in perf:
        cid = _normalize_creative_id(t.get("creative_id"))
        if cid is not None:
            perf_by_id[cid] = t

    rows = []
    for info in info_items:
        cid = _normalize_creative_id(info.get("creative_id"))
        match = perf_by_id.get(cid)
        thumb = info.get("thumbnail_image_data_url")
        rows.append([
            {"type": "image", "data_url": thumb} if thumb else "-",
            match["name"] if match else str(info.get("creative_id", "-")),
            info["platform"],
            _fmt_amount(round(match["cost"])) if match else "-",
            _fmt_amount(round(match["purchase_amount"])) if match else "-",
            f"{match['roas']}%" if match else "-",
        ])

    if not rows:
        return {"sections": [{"type": "text", "heading": "소재 썸네일 · 성과 매칭",
                              "body": "데이터 준비 중"}],
                "digest": None}
    section = {
        "type": "table",
        "heading": "소재 썸네일 · 성과 매칭",
        "headers": ["썸네일", "소재", "플랫폼", "광고비", "매출", "ROAS"],
        "rows": rows,
    }
    thumbs = sum(1 for r in rows if isinstance(r[0], dict))
    return {"sections": [section],
            "digest": {"creative_info_rows": len(rows), "thumbnails": thumbs}}


MAPPERS = {
    ("creative", "A"): map_creative_group_a,
    ("creative", "B"): map_creative_group_b,
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
    ("executive-mtd", "A"): map_execmtd_group_a,
    ("executive-mtd", "B"): map_execmtd_group_b,
    ("executive-mtd", "C"): map_execmtd_group_c,
    ("executive-mtd", "D"): map_execmtd_group_d,
    ("daily", "A_google_meta"): map_daily_group_a_google_meta,
    ("daily", "A_naver"): map_daily_group_a_naver,
    ("daily", "B_google_meta"): map_daily_group_b_google_meta,
    ("daily", "B_naver"): map_daily_group_b_naver,
    ("daily", "C_google_meta"): map_daily_group_c_google_meta,
    ("daily", "C_naver"): map_daily_group_c_naver,
    ("daily", "D_google_meta"): map_daily_group_d_google_meta,
    ("daily", "D_naver"): map_daily_group_d_naver,
}


def map_section(report_type, group, data):
    mapper = MAPPERS.get((report_type, group))
    if mapper is None:
        raise ValueError(f"unknown report_type/group: {report_type}/{group}")
    return mapper(data)
