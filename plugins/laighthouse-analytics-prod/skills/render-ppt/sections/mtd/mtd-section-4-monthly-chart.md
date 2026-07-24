# MTD Section 4: 월별 광고 성과 차트

**report_type:** `mtd` (항상 포함) — naver 기반 default generator 브랜드 전용(다형식품 등).

## MCP 도구 호출: `get_naver_monthly_ad_performance`

```json
{ "brand_name": "...", "start_month": "5개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "as_of_date": "target_date" }
```

> ⚠️ **`get_ad_performance_monthly_table`을 여기 쓰지 않는다 (2026-07-10 확인된 문제 — 값은 나오지만
> 실제 PDF/report-backend 수치와 맞지 않았다).** 그 도구는 `_query_nv_monthly`(범용 ad-performance
> 파이프라인, `mcp_server/tools_tables.py::_to_markdown_table`로 마크다운 반환)를 타는데, 이건
> report-backend가 이 차트를 만들 때 실제로 호출하는 API가 아니다. report-backend
> `default/_mtd_components.py::build_mtd_ad_performance`/`_build_ad_performance_chart`는
> `default/_prism_data.py::_build_13m_channel_frames`를 통해 **`get_naver_channel_progression`을
> 월마다 반복 호출**해서 만든다 — `get_naver_monthly_ad_performance`는 바로 그 호출 패턴(월별
> `get_naver_channel_progression` 루프 + `_calculate_cost`/`_calculate_sales` 리듀스)을 서버 사이드로
> 그대로 재현한 신규 naver 전용 MCP 도구다. `laighthouse-prism/src/mcp_server/tools_naver.py`에
> 정의돼 있다.
> `as_of_date`는 범위의 마지막 달(당월)만 그 날짜까지로 자르고, 그 이전 달들은 항상 달력상 전체
> 기간을 커버한다 — mtd-section-2(`get_naver_target_progress`)에 준 것과 같은 `target_date`를 준다.

## 필요 데이터 (MCP)
최근 6개월 배열 (응답 `items[]`의 `month`/`cost`/`purchase_amount`/`roas` 필드에서 매핑):
- `monthly_chart.labels`: 연월 레이블 배열 (예: ['25년 11월', ..., '26년 4월']) ← `month`
- `monthly_chart.ad_cost`: 광고비 배열 (숫자, 원) ← `cost`
- `monthly_chart.revenue`: 매출 배열 (숫자, 원) ← `purchase_amount`
- `monthly_chart.roas`: ROAS 배열 (숫자, %) ← `roas` **그대로** (이 도구는 report-backend의
  `_get_ad_performance_values_by_month`와 동일하게 이미 `sales/cost×100`으로 퍼센트 스케일로 반환한다
  — `get_naver_target_progress`의 `target_roas`/`actual_roas`와 달리 ×100 변환이 필요 없다)

## PPT 섹션

```json
{
  "type": "chart",
  "heading": "월별 광고 성과",
  "categories": "{monthly_chart.labels}",
  "bar_series": [
    { "name": "광고비", "values": "{monthly_chart.ad_cost}" },
    { "name": "매출", "values": "{monthly_chart.revenue}" }
  ],
  "line_series": { "name": "ROAS", "values": "{monthly_chart.roas}" }
}
```

- `categories`는 `monthly_chart.labels`(연월 레이블 배열, 예: `["25년 11월", ..., "26년 4월"]`)를
  그대로 넣는다.
- `bar_series`는 광고비(`monthly_chart.ad_cost`)와 매출(`monthly_chart.revenue`) 두 시리즈,
  `line_series`는 ROAS(`monthly_chart.roas`) 한 시리즈다 — 원본 Chart.js 혼합 차트(막대 2개 +
  꺾은선 1개)와 동일 구성.
- 위 JSON의 문자열 자리(`"{monthly_chart.labels}"` 등)는 실제 렌더링 시 그 배열/리스트 값으로
  그대로 치환한다(문자열이 아니라 JSON 배열이 들어간다).