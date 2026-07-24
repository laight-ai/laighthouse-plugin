import section_mapping as sm


def test_map_execmtd_group_a_single_kpi_cards_section_and_digest():
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

    result = sm.map_execmtd_group_a(data)

    # executive-mtd has no separate kpi-goals card section -- only one section.
    assert len(result["sections"]) == 1
    assert result["sections"][0] == {
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
                "diff": "목표 75,900,000 · 기간 매출 73,374,000",
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


def test_map_execmtd_group_b_monthly_chart_has_digest_unlike_mtd():
    data = {
        "items": [
            {"month": "25년 11월", "cost": 1000000, "purchase_amount": 5000000, "roas": 500},
            {"month": "25년 12월", "cost": 1100000, "purchase_amount": 5500000, "roas": 500},
        ]
    }

    result = sm.map_execmtd_group_b(data)

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
    # Unlike mtd's group B (digest=None), executive-mtd-section-3 explicitly
    # reuses this section's response, so the digest carries the raw items.
    assert result["digest"] == {"items": data["items"]}


def test_map_execmtd_group_c_category_mom_highlights_matches_md_example_minus_below_threshold():
    # Values engineered so (curr-prev)/prev*100 reproduces the .md file's
    # literal example percentages exactly: 기타 27.2, 단백질보충제 17.0,
    # 국내분유 5.1, 커피 -1.6. 커피 is excluded from the final selection
    # (|mom_pct|<10 and 3 stronger categories already fill the min-3 window).
    data = {
        "curr": {
            "items": [
                {"category": "기타", "sales": 1272},
                {"category": "단백질보충제", "sales": 1170},
                {"category": "국내분유", "sales": 1051},
                {"category": "커피", "sales": 984},
            ]
        },
        "prev": {
            "items": [
                {"category": "기타", "sales": 1000},
                {"category": "단백질보충제", "sales": 1000},
                {"category": "국내분유", "sales": 1000},
                {"category": "커피", "sales": 1000},
            ]
        },
    }

    result = sm.map_execmtd_group_c(data)

    assert result["sections"] == [
        {
            "type": "kpi_cards",
            "cards": [
                {"label": "기타", "value": "+27.2%", "diff_value": 27.2},
                {"label": "단백질보충제", "value": "+17.0%", "diff_value": 17.0},
                {"label": "국내분유", "value": "+5.1%", "diff_value": 5.1},
            ],
        }
    ]
    assert result["digest"] == {
        "category_mom_highlights": [
            {"category": "기타", "mom_pct": 27.2},
            {"category": "단백질보충제", "mom_pct": 17.0},
            {"category": "국내분유", "mom_pct": 5.1},
        ]
    }


def test_map_execmtd_group_c_new_category_shown_as_new_and_negative_label_has_no_plus():
    data = {
        "curr": {
            "items": [
                {"category": "커피", "sales": 800},
                {"category": "신규카테고리", "sales": 500000},
            ]
        },
        "prev": {
            "items": [
                {"category": "커피", "sales": 1000},
            ]
        },
    }

    result = sm.map_execmtd_group_c(data)

    cards = result["sections"][0]["cards"]
    assert {"label": "커피", "value": "-20.0%", "diff_value": -20.0} in cards
    assert {"label": "신규카테고리", "value": "신규"} in cards
    assert result["digest"]["category_mom_highlights"] == [
        {"category": "커피", "mom_pct": -20.0},
        {"category": "신규카테고리", "mom_pct": None},
    ]


def test_map_execmtd_group_c_no_highlights_falls_back_to_notice_card():
    data = {"curr": {"items": []}, "prev": {"items": []}}

    result = sm.map_execmtd_group_c(data)

    assert result["sections"] == [
        {
            "type": "kpi_cards",
            "cards": [
                {
                    "label": "안내",
                    "value": "이번 기간 카테고리별 매출 변동이 두드러지지 않았습니다",
                }
            ],
        }
    ]
    assert result["digest"] == {"category_mom_highlights": []}


def test_map_execmtd_group_d_media_roas_comparison_table_and_digest():
    data = {
        "prev": {
            "channels": [
                {
                    "channel": "nvad:BRS",
                    "actual": [
                        {"date": "2026-02-01", "cost": 3000000, "revenue": 21714000},
                        {"date": "2026-02-15", "cost": 3000000, "revenue": 21714000},
                        # Outside the day-of-month-matched prev window -- must
                        # be excluded by the as_of_date cutoff.
                        {"date": "2026-02-20", "cost": 9999999, "revenue": 1},
                    ],
                },
                {
                    "channel": "nvgfa_ad:",
                    "actual": [
                        {"date": "2026-02-01", "cost": 5500000, "revenue": 15000000},
                    ],
                },
                {
                    # Excluded from the table entirely, per the .md's explicit rule.
                    "channel": "nvgfa_dp:",
                    "actual": [
                        {"date": "2026-02-01", "cost": 1000000, "revenue": 1000000},
                    ],
                },
            ]
        },
        "prev_as_of_date": "2026-02-15",
        "curr": {
            "channels": [
                {
                    "channel": "nvad:BRS",
                    "actual": [
                        {"date": "2026-03-01", "cost": 3500000, "revenue": 21367000},
                        {"date": "2026-03-15", "cost": 3500000, "revenue": 21367000},
                    ],
                },
                {
                    "channel": "nvgfa_ad:",
                    "actual": [
                        {"date": "2026-03-01", "cost": 6050000, "revenue": 14000000},
                    ],
                },
                # nvad:PLINK/nvad:NVSHOP absent -> cost_sum 0 -> excluded from rows.
            ]
        },
        "curr_as_of_date": "2026-03-15",
        "prev_period_label": "2월",
        "curr_period_label": "3월",
    }

    result = sm.map_execmtd_group_d(data)

    section = result["sections"][0]
    assert section["type"] == "table"
    assert section["heading"] == "매체별 성과 비교"
    assert section["headers"] == ["채널", "2월 ROAS", "3월 ROAS", "변동"]

    # nvad:PLINK/NVSHOP have cost_sum 0 in both periods -> excluded entirely.
    labels = [row[0] for row in section["rows"]]
    assert "네이버 파워링크" not in labels
    assert "네이버 쇼핑검색" not in labels
    assert "네이버 GFA 디스플레이" not in labels

    # BRS: prev cost 6,000,000 / revenue 43,428,000 -> roas 723.8%
    #      curr cost 7,000,000 / revenue 42,734,000 -> roas 610.5%
    brs_row = next(row for row in section["rows"] if row[0] == "네이버 브랜드검색")
    assert brs_row == ["네이버 브랜드검색", "723.8%", "610.5%", "-113.3%p"]

    # GFA 애드부스트: VAT-inclusive raw cost / 1.1.
    gfa_row = next(row for row in section["rows"] if row[0] == "네이버 GFA 애드부스트")
    assert gfa_row[1].endswith("%") and gfa_row[2].endswith("%")

    # Sorted ascending by change_pp (worst change first).
    change_pps = [float(row[3].replace("%p", "")) for row in section["rows"]]
    assert change_pps == sorted(change_pps)

    digest = result["digest"]["media_roas_comparison"]
    assert digest["prev_period_label"] == "2월"
    assert digest["curr_period_label"] == "3월"
    assert {r["channel_label"] for r in digest["rows"]} == {"네이버 브랜드검색", "네이버 GFA 애드부스트"}


def test_map_execmtd_group_d_no_valid_rows_returns_no_section():
    data = {
        "prev": {"channels": []},
        "prev_as_of_date": "2026-02-15",
        "curr": {"channels": []},
        "curr_as_of_date": "2026-03-15",
        "prev_period_label": "2월",
        "curr_period_label": "3월",
    }

    result = sm.map_execmtd_group_d(data)

    assert result["sections"] == []
    assert result["digest"] == {"media_roas_comparison": None}


def test_map_section_dispatches_executive_mtd_groups():
    result = sm.map_section("executive-mtd", "B", {"items": []})
    assert result["sections"][0]["heading"] == "월별 광고 성과"


def test_map_section_rejects_unknown_executive_mtd_group():
    try:
        sm.map_section("executive-mtd", "Z", {})
        assert False, "expected ValueError"
    except ValueError as e:
        assert "executive-mtd/Z" in str(e)
