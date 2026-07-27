import section_mapping as sm


def test_map_monthly_group_a_kpi_cards_and_digest():
    data = {
        "target_cost": 15000000,
        "target_revenue": 75900000,
        "target_roas": 5.06,
        "actual_cost": 14800000,
        "actual_revenue": 76200000,
        "actual_roas": 5.15,
        "cost_progress_ratio": 0.9867,
        "revenue_progress_ratio": 1.004,
    }

    result = sm.map_monthly_group_a(data)

    section1, section2 = result["sections"]
    assert section1 == {
        "type": "kpi_cards",
        "cards": [
            {"label": "월 예산 목표", "value": "15,000,000"},
            {"label": "월 매출 목표", "value": "75,900,000"},
            {"label": "월 ROAS 목표", "value": "506%"},
        ],
    }
    assert section2 == {
        "type": "kpi_cards",
        "cards": [
            {
                "label": "월 예산대비 소진율",
                "value": "98.67%",
                "diff": "목표 15,000,000 · 소진 14,800,000",
            },
            {
                "label": "월 목표 매출 대비 달성률",
                "value": "100.4%",
                "diff": "목표 75,900,000 · 매출 76,200,000",
            },
            {
                "label": "월 누적 ROAS",
                "value": "515%",
                "diff": "목표 506%",
            },
        ],
    }
    assert result["digest"] == {
        "roas_goal_pct": 506,
        "roas_actual_pct": 515,
        "budget_spent_rate": 98.67,
        "revenue_achievement_rate": 100.4,
        "target_cost": 15000000,
        "actual_cost": 14800000,
        "target_revenue": 75900000,
        "actual_revenue": 76200000,
    }


def test_map_monthly_group_b_ad_performance_chart_and_digest():
    data = {
        "items": [
            {"month": "25년 10월", "cost": 900000, "purchase_amount": 4800000, "roas": 533},
            {"month": "25년 11월", "cost": 1000000, "purchase_amount": 5000000, "roas": 500},
        ]
    }

    result = sm.map_monthly_group_b(data)

    assert result["sections"] == [
        {
            "type": "chart",
            "heading": "월별 광고 성과",
            "categories": ["25년 10월", "25년 11월"],
            "bar_series": [
                {"name": "광고비", "values": [900000, 1000000]},
                {"name": "매출", "values": [4800000, 5000000]},
            ],
            "line_series": {"name": "ROAS", "values": [533, 500]},
        }
    ]
    assert result["digest"] == {"items": data["items"]}


def test_map_monthly_group_c_category_comparison_and_daily_table():
    # curr/prev pairs and category names lifted from monthly-section-6.md's
    # literal example. change_pct is *not* copied from that example, though:
    # recomputing (curr-prev)/prev*100 against the doc's own curr/prev values
    # reproduces 5 of its 6 documented change_pct numbers exactly once rounded
    # to 1 decimal (커피/단백질보충제/우유·요거트/두유/기타), but the first row
    # (국내분유, documented as 5.1) only comes out to 5.3 from the documented
    # prev/curr pair -- almost certainly a single-digit typo in the doc's prev
    # value (563,042,000 vs an intended ~564,042,000), not a different formula.
    # We assert the value the documented formula actually produces from the
    # documented inputs, per this skill's "never invent/recalculate beyond
    # what's documented" rule -- faithfully executing the rule, not the
    # doc's arithmetic slip.
    data = {
        "curr": {
            "items": [
                {"category": "국내분유", "sales": 592787349},
                {"category": "커피", "sales": 369661967},
                {"category": "단백질보충제", "sales": 228341896},
                {"category": "우유/요거트", "sales": 110042863},
                {"category": "두유", "sales": 29897949},
                {"category": "기타1", "sales": 3000000},
                {"category": "기타2", "sales": 2000000},
            ]
        },
        "prev": {
            "items": [
                {"category": "국내분유", "sales": 563042000},
                {"category": "커피", "sales": 375669000},
                {"category": "단백질보충제", "sales": 195245000},
                {"category": "우유/요거트", "sales": 92661000},
                {"category": "두유", "sales": 28052426},
                {"category": "기타1", "sales": 2000000},
                {"category": "기타2", "sales": 1000000},
            ]
        },
        "daily": {
            "items": [
                {"logdate": "2026-03-01", "product_category_3rd": "국내분유", "sales_amount": 1000000},
                {"logdate": "2026-03-01", "product_category_3rd": "커피", "sales_amount": 500000},
                {"logdate": "2026-03-02", "product_category_3rd": "국내분유", "sales_amount": 1200000},
                {"logdate": "2026-03-02", "product_category_3rd": "커피", "sales_amount": 600000},
                # A non-top-5 category present in the daily feed must be
                # dropped from the table -- top-5 selection comes from
                # section 6 (curr totals), not from the daily series itself.
                {"logdate": "2026-03-02", "product_category_3rd": "기타1", "sales_amount": 999999},
            ]
        },
        "curr_month_label": "26년 3월",
        "prev_month_label": "26년 2월",
    }

    result = sm.map_monthly_group_c(data)

    top5 = ["국내분유", "커피", "단백질보충제", "우유/요거트", "두유"]
    section6, section7 = result["sections"]

    assert section6 == {
        "type": "chart",
        "heading": "카테고리별 월간 매출액 비교",
        "categories": top5 + ["기타"],
        "bar_series": [
            {
                "name": "26년 2월",
                "values": [563042000, 375669000, 195245000, 92661000, 28052426, 3000000],
            },
            {
                "name": "26년 3월",
                "values": [592787349, 369661967, 228341896, 110042863, 29897949, 5000000],
            },
        ],
        "line_series": {
            "name": "전월 대비 증감률(%)",
            "values": [5.3, -1.6, 17.0, 18.8, 6.6, 66.7],
        },
    }

    assert section7 == {
        "type": "line_chart",
        "heading": "일일 카테고리별 매출 현황",
        "categories": ["3/1", "3/2"],
        "series": [
            {"name": cat, "values": values}
            for cat, values in zip(top5, [[1000000, 1200000], [500000, 600000],
                                          [0, 0], [0, 0], [0, 0]])
        ],
    }

    assert result["digest"] == {
        "category_monthly_comparison": {
            "prev_month_label": "26년 2월",
            "curr_month_label": "26년 3월",
            "labels": top5 + ["기타"],
            "prev": [563042000, 375669000, 195245000, 92661000, 28052426, 3000000],
            "curr": [592787349, 369661967, 228341896, 110042863, 29897949, 5000000],
            "change_pct": [5.3, -1.6, 17.0, 18.8, 6.6, 66.7],
        },
        "daily_sales": {"labels": ["2026-03-01", "2026-03-02"], "top_categories": top5},
    }


def test_map_monthly_group_c_new_category_change_pct_is_null_but_chart_shows_zero():
    data = {
        "curr": {"items": [{"category": "신규카테고리", "sales": 1000000}]},
        "prev": {"items": []},
        "daily": {"items": []},
        "curr_month_label": "26년 3월",
        "prev_month_label": "26년 2월",
    }

    result = sm.map_monthly_group_c(data)

    # top5 has just the one category here, but the "기타" bucket is always
    # appended (even if empty/zero) -- so both entries are null-prev/new.
    section6 = result["sections"][0]
    assert section6["line_series"]["values"] == [0, 0]
    assert result["digest"]["category_monthly_comparison"]["change_pct"] == [None, None]


def test_map_monthly_group_d_media_comparison_table_and_digest():
    data = {
        "prev": {
            "channels": [
                {
                    "channel": "nvad:BRS",
                    "actual": [
                        {"date": "2026-02-01", "cost": 6000000, "revenue": 43000000},
                        {"date": "2026-02-02", "cost": 7625164, "revenue": 55613900},
                    ],
                },
                {
                    "channel": "nvgfa_ad:",
                    "actual": [
                        {"date": "2026-02-01", "cost": 5500000, "revenue": 15000000},
                    ],
                },
            ]
        },
        "curr": {
            "channels": [
                {
                    "channel": "nvad:BRS",
                    "actual": [
                        {"date": "2026-03-01", "cost": 7000000, "revenue": 46000000},
                        {"date": "2026-03-02", "cost": 8128305, "revenue": 46365460},
                    ],
                },
                {
                    "channel": "nvgfa_ad:",
                    "actual": [
                        {"date": "2026-03-01", "cost": 6050000, "revenue": 14000000},
                    ],
                },
                # nvad:PLINK/nvad:NVSHOP/nvgfa_dp: absent entirely -> must still
                # appear as a zero-spend row, per monthly-section-8.md.
            ]
        },
        "prev_month_label": "2026년 2월",
        "curr_month_label": "2026년 3월",
    }

    result = sm.map_monthly_group_d(data)

    heading_section = result["sections"][0]
    assert heading_section == {"type": "heading", "text": "매체 별 성과 비교"}

    brs_table = result["sections"][1]
    assert brs_table["heading"] == "네이버 브랜드검색"
    assert brs_table["headers"] == ["월", "광고비 (원)", "매출 (원)", "ROAS"]
    assert brs_table["rows"] == [
        ["2026년 2월", "13,625,164", "98,613,900", "723.76%"],
        ["2026년 3월", "15,128,305", "92,365,460", "610.55%"],
    ]

    plink_table = result["sections"][2]
    assert plink_table["heading"] == "네이버 파워링크"
    assert plink_table["rows"] == [
        ["2026년 2월", "0", "0", "0.00%"],
        ["2026년 3월", "0", "0", "0.00%"],
    ]

    gfa_ad_table = result["sections"][4]
    assert gfa_ad_table["heading"] == "네이버 GFA 애드부스트"
    # VAT-inclusive raw cost / 1.1
    assert gfa_ad_table["rows"][0][1] == _amount_close(5500000 / 1.1)
    assert gfa_ad_table["rows"][1][1] == _amount_close(6050000 / 1.1)

    assert len(result["sections"]) == 1 + 5  # heading + 5 channel groups

    digest = result["digest"]["media_monthly_comparison"]
    assert [c["channel_label"] for c in digest] == [
        "네이버 브랜드검색", "네이버 파워링크", "네이버 쇼핑검색",
        "네이버 GFA 애드부스트", "네이버 GFA 디스플레이",
    ]
    assert digest[0]["rows"][1]["roas"] == 610.55


def _amount_close(value):
    return sm._fmt_amount(value)


def test_map_section_dispatches_monthly_groups():
    result = sm.map_section("monthly", "B", {"items": []})
    assert result["sections"][0]["heading"] == "월별 광고 성과"


def test_map_section_rejects_unknown_monthly_group():
    try:
        sm.map_section("monthly", "Z", {})
        assert False, "expected ValueError"
    except ValueError as e:
        assert "monthly/Z" in str(e)
