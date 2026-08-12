# Breezm Executive Creative Section 1: 최우수 소재 (ROAS / CTR, 최근 7일 기준)

**report_type:** `creative-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
**메타(Meta Ads)만 대상**이다. 기준일 포함 **최근 7일을 통째로 합산**한 소재(개별 광고) 단위
**ROAS 1·2위**와 **CTR 1·2위**를 카드로 보여준다 (`creative-detailed` section-1과 동일 내용).

> ℹ️ 카드 HTML(3행 표 구조, 이미지 onerror 폴백, 각주)은 전부 `assets/report-template.html` +
> `assets/build_report.py`가 처리한다 — 모델은 아래 규칙으로 랭킹만 정해서 빌더 입력 JSON의
> `s1`에 넣는다.

## MCP 도구 호출: `get_ad_performance_range_table` × 2 (`group_by:"ad"`, 최근 7일)

```json
{ "brand_name": "breezm", "media": "meta", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
{ "brand_name": "breezm", "media": "airbridge", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
```

- 이 도구는 구간 전체를 **소재당 1행으로 이미 합산**해 돌려준다 — 응답이 그 자체로 최종
  데이터라 별도 집계가 필요 없다(정렬만 하면 랭킹이 나온다). `is_active`는 항상 비어 있으나
  이 섹션은 쓰지 않는다.
- ⚠️ **`media`를 생략하지 않는다** — `group_by:"ad"`에서 생략하면 다른 매체 행까지 섞여 온다.
- `meta` 행: 소재(`campaign_name`+`asset_group`+`ad_name`)별 7일 합산
  `cost`/`impression`/`click` + `creative_id`/`platform_account_id`.
- `airbridge` 행: 같은 소재 단위 7일 합산 `airbridge_revenue`/`reservation`
  (소재 단위까지 매출·예약 정상 귀속 확인됨, 2026-08-03).
- ⚠️ `campaign-type` 금지. `group_by`는 문자열 `"ad"` 그대로.
- 이 2회 응답은 section-3/4/5와 공유되지 않는다(그쪽은 날짜별 daily_table이 별도로 필요).
  단, **section-4의 "광고비 상위 5개" 선정은 이 meta 응답의 7일 합산 `cost`를 그대로 쓴다**
  (재집계 불필요 — section-4 파일 참고).

## MCP 도구 호출: `get_ad_creative_info` × 1 (최종 선정된 소재만)

```json
{ "brand_name": "breezm", "meta": [ { "account_id": "{platform_account_id}", "creative_id": "{creative_id}" }, ... ] }
```

- 아래 선정 로직으로 ROAS 1·2위 + CTR 1·2위를 먼저 정한 뒤, 그 소재들(최대 4개, 중복은
  유니크하게)의 쌍만 모아 **1회** 호출한다 — 전체 소재를 조회하지 않는다.
- 응답의 `thumbnail_image_url`만 쓴다 — `thumbnail_image_data_url`(base64)은 쓰지 않는다.

## 조인·선정 로직

- **조인**: `campaign_name`+`asset_group`+`ad_name` **세 필드 정확 일치**만 (정규화·부분일치
  금지). 매체 쪽에만 있는 소재 → ROAS 랭킹 제외(CTR 랭킹엔 포함 가능). airbridge 쪽에만 있는
  소재 → 이 섹션 전체에서 제외.
- `CTR` = click ÷ impression × 100 (노출 0이면 CTR 랭킹 제외).
  `ROAS` = airbridge_revenue ÷ cost × 100 (광고비 0이면 ROAS 랭킹 제외).
- ROAS/CTR 각각 내림차순 1·2위 — 두 랭킹은 독립(같은 소재가 양쪽 1위여도 그대로 둔다).
- 유효 후보가 2개 미만이면 2위 항목을 빼면 된다 — `-` 표시·이미지 미표시는 빌더가 처리한다.

## 빌더 `s1` 필드

```json
"s1": {
  "roas": [ {"name": "소재명", "value": 388.05, "thumbnail_url": "https://..."}, {...2위...} ],
  "ctr":  [ {"name": "소재명", "value": 2.41, "thumbnail_url": null} ]
}
```

- `value`는 숫자 원본 그대로(% 소수 1자리 포맷은 빌더가 한다). `name`은 소재(광고) 이름만 —
  캠페인/광고그룹명을 덧붙이지 않는다.
- `thumbnail_url`은 `get_ad_creative_info`의 `thumbnail_image_url` — 없으면 `null`(이미지 셀
  비움). 각 배열은 1·2위 순서, 2위 없으면 1개만.
- 데이터가 비어있으면 `s1` 자체를 빼면 "데이터 준비 중" 카드로 렌더링된다 — 임의로 채우지
  않는다.
