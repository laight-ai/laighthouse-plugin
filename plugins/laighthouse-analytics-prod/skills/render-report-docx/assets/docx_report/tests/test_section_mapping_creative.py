import section_mapping as sm

# a trimmed real get_ad_performance_daily_table response (더마토리, 2026-05-10~11,
# group_by="ad-set" — ad_name empty, asset_group carries the creative identity)
_MD = (
    "| logdate | media | campaign_name | asset_group | ad_name | cost | impression "
    "| click | reach | purchase_count | purchase_amount | add_to_cart | view_content "
    "| ctr | cpc | cpm | cvr | roas | is_active | creative_id | video_view |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- "
    "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
    "| 2026-05-10 | meta | g_meta_con_모공패드_상시 | 모공_con_ADV+ |  | 292885 | 44519 "
    "| 334 | 22107 | 20 | 414080 | 28 | 359 | 0.0075 | 876.9 | 6578.9 | 0.0599 | 1.4138 "
    "|  |  | 64 |\n"
    "| 2026-05-11 | meta | g_meta_con_모공패드_상시 | 모공_con_ADV+ |  | 300000 | 50000 "
    "| 400 | 25000 | 25 | 500000 | 30 | 400 | 0.008 | 750.0 | 6000.0 | 0.0625 | 1.6667 "
    "|  |  | 70 |\n"
    "| 2026-05-10 | meta | g_meta_traffic_모공패드_상시 | 모공_traffic_NONE |  | 123599 "
    "| 19854 | 437 | 18967 | 0 | 0 | 8 | 486 | 0.022 | 282.8 | 6225.4 | 0.0 | 0.0 "
    "|  |  | 2113 |\n"
)


def test_parse_md_table_and_no_data():
    rows = sm._parse_md_table({"result": _MD})
    assert len(rows) == 3
    assert rows[0]["campaign_name"] == "g_meta_con_모공패드_상시"
    assert rows[0]["ad_name"] == ""
    assert sm._parse_md_table({"result": "_No data_"}) == []


def test_creative_group_a_aggregates_by_creative():
    result = sm.map_creative_group_a({"result": _MD})
    cards, table, chart = result["sections"]

    assert cards["type"] == "kpi_cards"
    labels = {c["label"]: c["value"] for c in cards["cards"]}
    assert labels["집행 소재 수"] == "2"
    assert labels["총 광고비"] == "716,484"      # 292885+300000+123599
    assert labels["총 전환 매출"] == "914,080"   # 414080+500000

    assert table["heading"] == "소재별 성과"
    top = table["rows"][0]
    assert top[0] == "모공_con_ADV+"             # ad_name empty → asset_group
    assert top[2] == "592,885"                   # two days summed
    # roas recomputed from sums: 914080/592885 → 154.2%
    assert top[9] == "154.2%"

    assert chart["type"] == "line_chart"
    assert chart["categories"] == ["5/10", "5/11"]
    adv = next(s for s in chart["series"] if s["name"] == "모공_con_ADV+")
    assert adv["values"] == [414080, 500000]

    digest = result["digest"]
    assert digest["overall_roas"] == 127.6       # 914080/716484
    assert digest["top_creatives"][0]["name"] == "모공_con_ADV+"


# ad-grain markdown carrying creative_id / platform_account_id (the join keys)
_MD_AD = (
    "| logdate | media | campaign_name | asset_group | ad_name | cost | impression "
    "| click | purchase_count | purchase_amount | creative_id | platform_account_id |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    "| 2026-05-14 | meta | camp | set | 모공패드_영상A | 250000 | 40000 | 300 | 20 "
    "| 500000 | 456.0 | 123 |\n"
    "| 2026-05-15 | meta | camp | set | 모공패드_영상A | 250000 | 40000 | 300 | 20 "
    "| 500000 | 456.0 | 123 |\n"
)

_PNG_DATA_URL = ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAA"
                 "fFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def test_creative_group_b_joins_thumbnails_with_performance():
    # real get_ad_creative_info shape (prism 1.27.0): platform lists echoing
    # {account_id, creative_id, thumbnail_image_url, thumbnail_image_data_url}
    creative = {"google": [], "tiktok": [], "meta": [
        {"account_id": 123, "creative_id": 456,
         "thumbnail_image_url": "https://cdn/x.png",
         "thumbnail_image_data_url": _PNG_DATA_URL},
        {"account_id": 123, "creative_id": 789,
         "thumbnail_image_url": "https://cdn/y.png",
         "thumbnail_image_data_url": None},
    ]}
    result = sm.map_creative_group_b({"creative": creative, "performance": {"result": _MD_AD}})
    table = result["sections"][0]
    assert table["headers"] == ["썸네일", "소재", "플랫폼", "광고비", "매출", "ROAS"]
    matched = table["rows"][0]
    assert matched[0] == {"type": "image", "data_url": _PNG_DATA_URL}
    assert matched[1] == "모공패드_영상A"          # joined on creative_id 456
    assert matched[3] == "500,000"                # two days summed
    assert matched[5] == "200.0%"                 # 1,000,000 / 500,000
    unmatched = table["rows"][1]
    assert unmatched[0] == "-" and unmatched[1] == "789" and unmatched[3] == "-"
    assert result["digest"] == {"creative_info_rows": 2, "thumbnails": 1}


def test_creative_group_b_empty_info_degrades():
    result = sm.map_creative_group_b(
        {"creative": {"google": [], "meta": [], "tiktok": []},
         "performance": {"result": _MD}})
    assert result["sections"][0]["body"] == "데이터 준비 중"


def test_creative_registered_in_mappers_and_orders():
    import map_report
    assert ("creative", "A") in sm.MAPPERS and ("creative", "B") in sm.MAPPERS
    entries = map_report.ORDERS["creative"]
    assert entries[-1][0] == "analysis" and entries[-1][1] == "section4"


def test_creative_chart_falls_back_to_cost_when_no_revenue():
    md = (
        "| logdate | media | campaign_name | asset_group | ad_name | cost | impression "
        "| click | purchase_count | purchase_amount |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| 2026-07-01 | meta | c | s | 소재A | 1000 | 10 | 1 | 0 | 0 |\n"
        "| 2026-07-02 | meta | c | s | 소재A | 2000 | 10 | 1 | 0 | 0 |\n"
    )
    result = sm.map_creative_group_a({"result": md})
    chart = result["sections"][2]
    assert chart["heading"] == "상위 소재 일별 광고비 추이"
    assert chart["series"][0]["values"] == [1000, 2000]
