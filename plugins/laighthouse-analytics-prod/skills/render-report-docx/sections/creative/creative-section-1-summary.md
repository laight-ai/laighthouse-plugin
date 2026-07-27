# creative-section-1: 소재 성과 개요 + 소재별 성과 표

## MCP 도구 호출

`mcp__laighthouse__get_ad_performance_daily_table` 1회:

```json
{
  "brand_name": "{brand_name}",
  "start_date": "{기간 시작일}",
  "end_date": "{기간 종료일}",        // 시작~종료 31일 이내
  "group_by": "ad",
  "media": "{media}"                  // 기본 "meta" (Google/Meta 소재 브랜드)
}
```

- ⚠️ **`group_by="ad"` 서버 이슈 (2026-07-27 실측)**: 일부 브랜드 테이블에 `ad_status`
  컬럼이 없어 `group_by="ad"`가 500(OperationalError)을 반환한다. 이 경우
  **`group_by="ad-set"`으로 폴백**한다 — ad-set(광고세트) 그레인을 소재 근사치로 쓰며,
  응답의 `ad_name`이 빈 문자열이면 매핑 스크립트가 `asset_group`을 소재 식별자로
  대신 쓴다 (`section_mapping._creative_identity`).
- 응답은 JSON이 아니라 **`{"result": "<markdown 표>"}`** 다. 데이터가 없으면
  `{"result": "_No data_"}`. 컬럼(2026-07-27 실측): logdate, media, campaign_name,
  asset_group, ad_name, cost, impression, click, reach, purchase_count,
  purchase_amount, add_to_cart, view_content, ctr, cpc, cpm, cvr, roas, is_active,
  creative_id, video_view 등.
- ⚠️ `roas`(1.4138)·`ctr`(0.0075)·`cvr`는 **비율값**이다 — 매핑 스크립트가 합산 후
  %로 재계산하므로 LLM이 변환하지 않는다.

## 저장 형식

응답을 가공 없이 그대로 그룹 A 값으로 저장한다 (`{"result": "..."}` 통째로).

## DOCX 섹션 (매핑 스크립트가 생성 — `map_creative_group_a`)

1. `kpi_cards` "소재 성과 개요" — 집행 소재 수 / 총 광고비 / 총 전환 매출 / 전체 ROAS.
2. `table` "소재별 성과" — 소재(ad_name, 비면 asset_group)별로 일자 행을 **합산**
   (cost/impression/click/purchase_count/purchase_amount/video_view), CTR·CPC·ROAS는
   합산값에서 재계산(일별 비율 평균 금지). 광고비 내림차순 정렬.
3. `line_chart` "상위 소재 일별 매출 추이" — 광고비 상위 5개 소재의 일별
   purchase_amount 라인.

이 합산/재계산은 이 섹션에 **명시적으로 문서화된 기계적 집계 규칙**이다
(데이터 처리 원칙의 예외 아님 — 규칙 자체가 여기 적혀 있다).
