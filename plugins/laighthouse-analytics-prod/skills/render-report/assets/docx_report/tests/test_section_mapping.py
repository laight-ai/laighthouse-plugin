import section_mapping as sm


def test_map_mtd_group_a_kpi_cards_and_digest():
    data = {
        "target_cost": 15000000,
        "target_revenue": 75900000,
        "target_roas": 5.06,
        "actual_cost": 8400000,
        "actual_revenue": 73374000,
        "actual_roas": 8.7357,
        "cost_progress_ratio": 0.56,
        "revenue_progress_ratio": 0.966,
    }

    result = sm.map_mtd_group_a(data)

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
                "label": "기간 예산대비 소진율",
                "value": "56%",
                "diff": "목표 15,000,000 · 소진 8,400,000",
            },
            {
                "label": "기간 목표 매출 대비 달성률",
                "value": "96.6%",
                "diff": "목표 75,900,000 · 매출 73,374,000",
            },
            {
                "label": "기간 누적 ROAS",
                "value": "873.57%",
                "diff": "목표 506%",
            },
        ],
    }
    assert result["digest"] == {
        "roas_goal_pct": 506,
        "roas_actual_pct": 873.57,
        "budget_spent_rate": 56,
        "revenue_achievement_rate": 96.6,
        "target_cost": 15000000,
        "actual_cost": 8400000,
        "target_revenue": 75900000,
        "actual_revenue": 73374000,
    }


def test_map_mtd_group_a_missing_targets_raises():
    try:
        sm.map_mtd_group_a({"target_cost": 1})
        assert False, "expected KeyError for incomplete target_progress response"
    except KeyError:
        pass


def test_map_mtd_group_b_monthly_chart():
    data = {
        "items": [
            {"month": "25년 11월", "cost": 1000000, "purchase_amount": 5000000, "roas": 500},
            {"month": "25년 12월", "cost": 1100000, "purchase_amount": 5500000, "roas": 500},
        ]
    }

    result = sm.map_mtd_group_b(data)

    assert result["digest"] is None
    assert result["sections"] == [
        {
            "type": "chart",
            "heading": "월별 광고 성과",
            "categories": ["25년 11월", "25년 12월"],
            "bar_series": [
                {"name": "광고비", "values": [1000000, 1100000]},
                {"name": "매출", "values": [5000000, 5500000]},
            ],
            "line_series": {"name": "ROAS", "values": [500, 500]},
        }
    ]


def test_map_mtd_group_c_daily_category_table_and_digest():
    data = {
        "daily": {
            "items": [
                {"logdate": "2026-05-01", "product_category_3rd": "국내분유", "sales_amount": 1000000},
                {"logdate": "2026-05-01", "product_category_3rd": "커피", "sales_amount": 500000},
                {"logdate": "2026-05-02", "product_category_3rd": "국내분유", "sales_amount": 1200000},
                {"logdate": "2026-05-02", "product_category_3rd": "커피", "sales_amount": 600000},
            ]
        },
        "cumulative": {
            "items": [
                {"category": "국내분유", "sales": 64295126, "discount_rate": 91.75, "refund_rate": 41.86, "mom": 49.19},
                {"category": "커피", "sales": 44081771, "discount_rate": 92.80, "refund_rate": 19.78, "mom": 47.20},
            ]
        },
    }

    result = sm.map_mtd_group_c(data)

    assert result["sections"] == [
        {
            "type": "table",
            "heading": "일일 카테고리별 매출 현황",
            "headers": ["날짜", "국내분유", "커피"],
            "rows": [
                ["2026-05-01", "1,000,000", "500,000"],
                ["2026-05-02", "1,200,000", "600,000"],
            ],
        }
    ]
    assert result["digest"] == {
        "top_categories": ["국내분유", "커피"],
        "top_category_totals": {"국내분유": 2200000, "커피": 1100000},
        "product_cumulative_sales": data["cumulative"]["items"],
    }


def test_map_mtd_group_d_media_budget_progress():
    data = {
        "items": [
            {
                "channel": "네이버 브랜드검색", "spent_rate": 55.9, "budget_goal": 19099909,
                "spent": 9237537, "daily_budget": 10669754, "daily_spent_avg": 8421155,
            },
        ],
        "total": {
            "spent_rate": 50, "budget_goal": 24000000, "spent": 11600000,
            "daily_budget": 13000000, "daily_spent_avg": 10800000,
        },
        "channel_group": "SA / DA",
    }

    result = sm.map_mtd_group_d(data)

    assert result["sections"] == [
        {
            "type": "table",
            "heading": "매체별 예산 소진 현황 (SA / DA)",
            "headers": ["매체", "예산 소진율", "목표 소진", "예산 소진", "일 소진예산", "일 평균 소진액"],
            "rows": [
                ["네이버 브랜드검색", "55.9%", "19,099,909", "9,237,537", "10,669,754", "8,421,155"],
                ["합계", "50%", "24,000,000", "11,600,000", "13,000,000", "10,800,000"],
            ],
        }
    ]
    assert result["digest"] == {
        "channels": [{"channel": "네이버 브랜드검색", "spent_rate": 55.9}],
        "total_spent_rate": 50,
    }


def test_map_mtd_group_e_campaign_performance():
    data = {
        "items": [
            {
                "campaign": "05_GT케이(SPBR)_MO", "channel": "NVSHOP", "revenue": 1320543,
                "ad_cost": 129801, "roas": 1017, "impressions": 12778, "clicks": 53,
                "ctr": 0.41, "cpc": 2449.08, "purchases": 17, "avg_price": 77679,
            },
        ]
    }

    result = sm.map_mtd_group_e(data)

    assert result["sections"] == [
        {
            "type": "table",
            "heading": "캠페인별 성과",
            "headers": [
                "캠페인", "네이버 광고 채널명", "매출", "광고비", "ROAS",
                "노출", "클릭", "CTR", "CPC", "구매", "평균단가",
            ],
            "rows": [
                [
                    "05_GT케이(SPBR)_MO", "NVSHOP", "1,320,543", "129,801", "1017%",
                    "12,778", "53", "0.41%", "2,449.08", 17, "77,679",
                ]
            ],
        }
    ]
    assert result["digest"] == {"top_campaigns_by_ad_cost": data["items"]}


def test_map_mtd_group_f_group_performance():
    data = {
        "items": [
            {
                "group": "002_브랜드_공용_통합", "impressions": 3528, "clicks": 108,
                "cpc": 346.41, "ad_cost": 37412, "revenue": 666438,
            },
        ]
    }

    result = sm.map_mtd_group_f(data)

    assert result["digest"] is None
    assert result["sections"] == [
        {
            "type": "table",
            "heading": "광고그룹별 성과",
            "headers": ["광고그룹", "노출", "클릭", "CPC", "광고비", "매출"],
            "rows": [["002_브랜드_공용_통합", "3,528", "108", "346.41", "37,412", "666,438"]],
        }
    ]


def test_map_mtd_group_g_keyword_performance():
    data = {
        "items": [
            {
                "keyword": "알파카리그린티라떼", "impressions": 9076, "clicks": 659, "ad_cost": 353722,
                "cpc": 536.76, "ctr": 7.26, "cpm": 38973.34, "purchases": 183, "revenue": 8057615,
                "roas": 2278,
            },
        ]
    }

    result = sm.map_mtd_group_g(data)

    assert result["digest"] is None
    assert result["sections"] == [
        {
            "type": "table",
            "heading": "키워드별 성과",
            "headers": ["키워드", "노출", "클릭", "광고비", "CPC", "클릭율", "CPM", "구매건수", "매출", "ROAS"],
            "rows": [
                [
                    "알파카리그린티라떼", "9,076", "659", "353,722", "536.76",
                    "7.26%", "38,973.34", 183, "8,057,615", "2278%",
                ]
            ],
        }
    ]


def test_map_section_dispatches_by_report_type_and_group():
    result = sm.map_section("mtd", "F", {"items": []})
    assert result["sections"][0]["heading"] == "광고그룹별 성과"


def test_map_section_rejects_unknown_group():
    try:
        sm.map_section("mtd", "Z", {})
        assert False, "expected ValueError"
    except ValueError as e:
        assert "mtd/Z" in str(e)
