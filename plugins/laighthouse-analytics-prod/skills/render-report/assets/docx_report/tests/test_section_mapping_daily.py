import section_mapping as sm


# ---------------------------------------------------------------------------
# Group A (sections 1+2) -- 분기 A: Google/Meta
# ---------------------------------------------------------------------------


def test_map_daily_group_a_google_meta_two_kpi_cards_sections_and_digest():
    data = {
        "sales": {
            "budget_goal": 15000,
            "revenue_goal": 75000,
            "roas_goal": 500,
            "period_progress_pct": 93.3,
            "period_label": "28/30 days",
            "budget_utilization_pct": 86.2,
            "budget_utilization_diff": -7.1,
            "budget_spent": 12930,
            "revenue_achievement_pct": 96.6,
            "revenue_achievement_diff": 3.3,
            "revenue_actual": 72450,
            "roas_achievement_pct": 561.0,
            "roas_achievement_diff": 61.0,
            "roas_actual": 561.0,
        }
    }

    result = sm.map_daily_group_a_google_meta(data)

    assert result["sections"][0] == {
        "type": "kpi_cards",
        "cards": [
            {"label": "Monthly Budget Plan", "value": "$15,000"},
            {"label": "Monthly Revenue Target", "value": "$75,000"},
            {"label": "Monthly ROAS Target", "value": "500%"},
        ],
    }
    assert result["sections"][1] == {
        "type": "kpi_cards",
        "cards": [
            {"label": "Period Progress", "value": "93.3% (28/30 days)"},
            {
                "label": "Monthly Budget Utilization",
                "value": "86.2% (-7.1%p)",
                "diff": "Target $15,000 · Current $12,930",
                "diff_value": -7.1,
            },
            {
                "label": "Monthly Revenue Achievement",
                "value": "96.6% (+3.3%p)",
                "diff": "Target $75,000 · Current $72,450",
                "diff_value": 3.3,
            },
            {
                "label": "Monthly ROAS Achievement",
                "value": "561.0% (+61.0%p)",
                "diff": "Target 500% · Current 561.0%",
                "diff_value": 61.0,
            },
        ],
    }
    assert result["digest"]["period_progress_pct"] == 93.3
    assert result["digest"]["roas_actual"] == 561.0


# ---------------------------------------------------------------------------
# Group A (sections 1+2) -- 분기 B: naver
# ---------------------------------------------------------------------------


def test_map_daily_group_a_naver_computes_period_progress_and_diffs():
    # Engineered so budget_spent_rate - period_progress_pct == -7.1 and
    # revenue_achievement_rate - period_progress_pct == +3.3, matching
    # daily-section-2.md's worked "4월 28일" narrative numbers exactly
    # (93.3% = 28/30*100, budget diff -7.1%p, revenue diff +3.3%p).
    data = {
        "as_of_date": "2026-04-28",
        "target_cost": 15000000,
        "target_revenue": 75000000,
        "target_roas": 5.0,
        "actual_cost": 12930000,
        "actual_revenue": 72450000,
        "actual_roas": 5.61,
        "cost_progress_ratio": 0.862,
        "revenue_progress_ratio": 0.966,
    }

    result = sm.map_daily_group_a_naver(data)

    assert result["digest"] is None
    assert result["sections"][0] == {
        "type": "kpi_cards",
        "cards": [
            {"label": "월 예산 목표", "value": "15,000,000"},
            {"label": "월 매출 목표", "value": "75,000,000"},
            {"label": "월 ROAS 목표", "value": "500%"},
        ],
    }
    cards = result["sections"][1]["cards"]
    assert cards[0] == {"label": "기간 진척률", "value": "93.3% (28/30일)"}
    assert cards[1] == {
        "label": "월 예산대비 소진율",
        "value": "86.2% (-7.1%p)",
        "diff": "목표 ₩15,000,000 · 소진비용 ₩12,930,000",
        "diff_value": -7.1,
    }
    assert cards[2] == {
        "label": "월 목표 매출 대비 달성률",
        "value": "96.6% (+3.3%p)",
        "diff": "목표 ₩75,000,000 · 매출 ₩72,450,000",
        "diff_value": 3.3,
    }
    assert cards[3] == {
        "label": "월 누적 ROAS",
        # _ratio_to_pct returns an int when the result is a whole number
        # (561, 500 here), so their diff stays an int too (61, not 61.0).
        "value": "561% (+61%p)",
        "diff": "목표 500%",
        "diff_value": 61,
    }


def test_map_daily_group_a_naver_days_in_month_uses_calendar_not_hardcoded_30():
    data = {
        "as_of_date": "2026-02-14",  # Feb 2026 has 28 days
        "target_cost": 1000000,
        "target_revenue": 5000000,
        "target_roas": 5.0,
        "actual_cost": 500000,
        "actual_revenue": 2500000,
        "actual_roas": 5.0,
        "cost_progress_ratio": 0.5,
        "revenue_progress_ratio": 0.5,
    }

    result = sm.map_daily_group_a_naver(data)

    assert result["sections"][1]["cards"][0]["value"] == "50.0% (14/28일)"


# ---------------------------------------------------------------------------
# Group B (section 4) -- 분기 A / B
# ---------------------------------------------------------------------------


def test_map_daily_group_b_google_meta_chart_no_digest():
    data = {
        "sales_daily": {
            "labels": ["3/26(Thu)", "3/27(Fri)"],
            "revenue": [1000, 1200],
            "ad_spend": [200, 220],
            "roas": [500, 545],
        }
    }

    result = sm.map_daily_group_b_google_meta(data)

    assert result["sections"] == [
        {
            "type": "chart",
            "heading": "Sales campaign: Daily performance in the last 7 days",
            "categories": ["3/26(Thu)", "3/27(Fri)"],
            "bar_series": [
                {"name": "Revenue", "values": [1000, 1200]},
                {"name": "Ad Spend", "values": [200, 220]},
            ],
            "line_series": {"name": "ROAS", "values": [500, 545]},
        }
    ]
    assert result["digest"] is None


def test_map_daily_group_b_naver_computes_roas_and_weekday_labels():
    data = {
        "items": [
            {"logdate": "2026-04-22", "ad_cost": 3000000, "revenue": 18000000},
            {"logdate": "2026-04-28", "ad_cost": 3100000, "revenue": 15400000},
        ]
    }

    result = sm.map_daily_group_b_naver(data)

    section = result["sections"][0]
    assert section["type"] == "chart"
    assert section["heading"] == "최근 7일 성과"
    # 2026-04-22 is a Wednesday, 2026-04-28 is a Tuesday.
    assert section["categories"] == ["4/22(수)", "4/28(화)"]
    assert section["bar_series"] == [
        {"name": "매출", "values": [18000000, 15400000]},
        {"name": "광고비", "values": [3000000, 3100000]},
    ]
    assert section["line_series"]["values"] == [600.0, 496.77]
    assert result["digest"]["daily_items"][1]["roas"] == 496.77


def test_map_daily_group_b_naver_zero_ad_cost_falls_back_to_zero_roas():
    data = {"items": [{"logdate": "2026-04-22", "ad_cost": 0, "revenue": 0}]}

    result = sm.map_daily_group_b_naver(data)

    assert result["sections"][0]["line_series"]["values"] == [0.0]


# ---------------------------------------------------------------------------
# Group C (section 5) -- 분기 A / B
# ---------------------------------------------------------------------------


def test_map_daily_group_c_google_meta_table_matches_md_literal_example():
    data = {
        "sales_by_campaign": [
            {
                "media": "Google Ads",
                "campaign": "Auto_Gen_D2C_BottomFunnel_Rev_PerfMax - High Performing + Other",
                "impression": 3548,
                "click": 62,
                "ctr": 1.75,
                "cost": 53,
                "revenue": 46,
                "roas": 86.8,
            }
        ]
    }

    result = sm.map_daily_group_c_google_meta(data)

    assert result["sections"] == [
        {
            "type": "table",
            "heading": "Performance by Campaign",
            "headers": ["Media", "Campaign", "Impression", "Click", "CTR (%)", "Cost ($)", "Revenue ($)", "ROAS (%)"],
            "rows": [
                [
                    "Google Ads",
                    "Auto_Gen_D2C_BottomFunnel_Rev_PerfMax - High Performing + Other",
                    "3,548",
                    "62",
                    1.75,
                    "53",
                    "46",
                    86.8,
                ]
            ],
        }
    ]
    assert result["digest"] is None


def test_map_daily_group_c_naver_table_matches_md_literal_example_and_computes_cpm():
    data = {
        "items": [
            {
                "campaign": "00_통합(BS)_MO",
                "channel": "BRS",
                "revenue": 4441630,
                "ad_cost": 494112,
                "roas": 898.91,
                "impressions": 5901,
                "clicks": 686,
                "ctr": 11.63,
                "cpc": 720.28,
                "purchases": 66,
            }
        ]
    }

    result = sm.map_daily_group_c_naver(data)

    section = result["sections"][0]
    assert section["type"] == "table"
    assert section["heading"] == "캠페인 성과"
    assert section["rows"] == [
        [
            "네이버 브랜드검색",
            "00_통합(BS)_MO",
            "5,901",
            "686",
            "494,112",
            "720.28",
            "11.63%",
            "83.73",  # 494112 / 5901, rounded to 2 decimals (see FLAGGED cpm note)
            66,
            "4,441,630",
            "898.91%",
        ]
    ]
    assert result["digest"] is None


def test_map_daily_group_c_naver_filters_rows_below_10000_and_falls_back():
    data = {
        "items": [
            {
                "campaign": "테스트 캠페인",
                "channel": "PLINK",
                "revenue": 0,
                "ad_cost": 9999,
                "roas": 0,
                "impressions": 10,
                "clicks": 1,
                "ctr": 10.0,
                "cpc": 9999.0,
                "purchases": 0,
            }
        ]
    }

    result = sm.map_daily_group_c_naver(data)

    assert result["sections"] == [
        {
            "type": "kpi_cards",
            "cards": [{"label": "안내", "value": "이번 기간 10,000원 이상 집행된 캠페인이 없음"}],
        }
    ]


# ---------------------------------------------------------------------------
# Group D (section 6) -- 분기 A / B
# ---------------------------------------------------------------------------


def test_map_daily_group_d_google_meta_table_no_roas_column():
    data = {
        "sales_by_asset_group": [
            {
                "media": "Google Ads",
                "campaign": "Auto_Gen_D2C_BottomFunnel_Rev_PerfMax - High Performing + Other",
                "asset_group": "CITRUS Kiwi overlay pack assets",
                "impression": 509,
                "click": 15,
                "ctr": 2.95,
                "cost": 10,
                "revenue": 0,
            }
        ]
    }

    result = sm.map_daily_group_d_google_meta(data)

    assert result["sections"] == [
        {
            "type": "table",
            "heading": "Performance by Asset group",
            "headers": ["Media", "Campaign", "Asset Group", "Impression", "Click", "CTR (%)", "Cost ($)", "Revenue ($)"],
            "rows": [
                [
                    "Google Ads",
                    "Auto_Gen_D2C_BottomFunnel_Rev_PerfMax - High Performing + Other",
                    "CITRUS Kiwi overlay pack assets",
                    "509",
                    "15",
                    2.95,
                    "10",
                    "0",
                ]
            ],
        }
    ]
    assert result["digest"] is None


def test_map_daily_group_d_naver_builds_flat_tree_with_group_and_keyword_rows():
    data = {
        "ad_group": {
            "items": [
                {
                    "nvr_media_type": "BRS",
                    "campaign_name": "00_통합(BS)_MO",
                    "group_name": "02_분유(스토어)",
                    "imp": 1000,
                    "click": 200,
                    "cost_exc_vat": 100000,
                    "gross_conv_cnt": 50,
                    "gross_conv_amnt": 5000000,
                }
            ]
        },
        "keyword": {
            "items": [
                {
                    "nvr_media_type": "BRS",
                    "campaign_name": "00_통합(BS)_MO",
                    "group_name": "02_분유(스토어)",
                    "term": "아기사랑수",
                    "imp": 300,
                    "click": 40,
                    "cost_exc_vat": 20000,
                    "gross_conv_cnt": 10,
                    "gross_conv_amnt": 1000000,
                },
                {
                    # term "-" rows are dropped entirely (unmatched traffic).
                    "nvr_media_type": "BRS",
                    "campaign_name": "00_통합(BS)_MO",
                    "group_name": "02_분유(스토어)",
                    "term": "-",
                    "imp": 999,
                    "click": 999,
                    "cost_exc_vat": 999999,
                    "gross_conv_cnt": 999,
                    "gross_conv_amnt": 999999,
                },
                {
                    # Below the 10,000 ad_cost floor -- dropped, group unaffected.
                    "nvr_media_type": "BRS",
                    "campaign_name": "00_통합(BS)_MO",
                    "group_name": "02_분유(스토어)",
                    "term": "소액키워드",
                    "imp": 10,
                    "click": 1,
                    "cost_exc_vat": 500,
                    "gross_conv_cnt": 0,
                    "gross_conv_amnt": 0,
                },
            ]
        },
    }

    result = sm.map_daily_group_d_naver(data)

    section = result["sections"][0]
    assert section["type"] == "table"
    assert section["heading"] == "광고 그룹 및 키워드 성과"
    assert section["rows"] == [
        [
            "네이버 브랜드검색 / 00_통합(BS)_MO",
            "02_분유(스토어)",
            "전체",
            "1,000",
            "200",
            "100,000",
            "500.0",  # cpc = 100000/200
            "20.0%",  # ctr = 200/1000*100
            "100.0",  # cpm = 100000/1000 (see FLAGGED cpm note in section_mapping.py)
            50,
            "5,000,000",
            "5000.0%",  # roas = 5000000/100000*100
        ],
        [
            "",
            "",
            "└ 아기사랑수",
            "300",
            "40",
            "20,000",
            "500.0",
            "13.33%",
            "66.67",
            10,
            "1,000,000",
            "5000.0%",
        ],
    ]
    assert result["digest"] is None


def test_map_daily_group_d_naver_group_below_floor_drops_group_and_children():
    data = {
        "ad_group": {
            "items": [
                {
                    "nvr_media_type": "PLINK",
                    "campaign_name": "캠페인A",
                    "group_name": "그룹A",
                    "imp": 10,
                    "click": 1,
                    "cost_exc_vat": 500,
                    "gross_conv_cnt": 0,
                    "gross_conv_amnt": 0,
                }
            ]
        },
        "keyword": {"items": []},
    }

    result = sm.map_daily_group_d_naver(data)

    assert result["sections"] == [
        {
            "type": "kpi_cards",
            "cards": [{"label": "안내", "value": "이번 기간 10,000원 이상 집행된 광고그룹이 없음"}],
        }
    ]
    assert result["digest"] is None


def test_map_daily_group_d_naver_truncates_children_to_20_with_notice_row():
    keyword_items = [
        {
            "nvr_media_type": "BRS",
            "campaign_name": "캠페인A",
            "group_name": "그룹A",
            "term": f"키워드{i}",
            "imp": 100,
            "click": 10,
            "cost_exc_vat": 10000,
            "gross_conv_cnt": 1,
            "gross_conv_amnt": 100000 - i,  # descending revenue for stable ordering
        }
        for i in range(25)
    ]
    data = {
        "ad_group": {
            "items": [
                {
                    "nvr_media_type": "BRS",
                    "campaign_name": "캠페인A",
                    "group_name": "그룹A",
                    "imp": 3000,
                    "click": 300,
                    "cost_exc_vat": 300000,
                    "gross_conv_cnt": 30,
                    "gross_conv_amnt": 3000000,
                }
            ]
        },
        "keyword": {"items": keyword_items},
    }

    result = sm.map_daily_group_d_naver(data)

    rows = result["sections"][0]["rows"]
    # 1 group row + 20 keyword rows + 1 "외 N개 키워드" notice row.
    assert len(rows) == 1 + 20 + 1
    assert rows[-1] == ["", "", "└ 외 5개 키워드", "", "", "", "", "", "", "", "", ""]
    # Top-revenue keyword (i=0) must be first among the kept children.
    assert rows[1][2] == "└ 키워드0"


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def test_map_section_dispatches_all_daily_branch_groups():
    assert sm.map_section("daily", "B_google_meta", {"sales_daily": {"labels": [], "revenue": [], "ad_spend": [], "roas": []}})["sections"][0]["heading"].startswith("Sales campaign")
    assert sm.map_section("daily", "B_naver", {"items": []})["sections"][0]["heading"] == "최근 7일 성과"


def test_map_section_rejects_unknown_daily_group():
    try:
        sm.map_section("daily", "Z_naver", {})
        assert False, "expected ValueError"
    except ValueError as e:
        assert "daily/Z_naver" in str(e)
