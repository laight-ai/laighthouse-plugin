# MTD Section 6: 일일 카테고리별 매출 현황

**report_type:** `mtd` (항상 포함).

## MCP 도구 호출: `get_naver_item_sales_daily`

```json
{ "brand_name": "...", "start_date": "당월초", "end_date": "target_date" }
```
> ⚠️ **`group_by` 파라미터를 보내지 않는다.** enum 문자열 인자가 토크나이저 버그로 계속 숫자로
> 잘못 잘려 들어가는 문제 때문에 도구에서 `group_by`를 통째로 제거했다 — 서버가 항상
> `category_3rd` 기준으로 그룹핑해서 반환한다. `group_by` 키 자체를 요청 JSON에 넣지 않는다.
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`, `/v2/naver/item-sales/daily` 래퍼)
- mtd-section-6와 동일 호출 결과를 재사용 — `items[]`를 `(logdate, product_category_3rd)`로
  그룹핑해 `sum(sales_amount)`, 매출 상위 5개 카테고리만 시리즈로 렌더링

## 필요 데이터 (MCP)
- `daily_sales.labels`: 날짜 배열 (예: ['2026-04-01', ..., '2026-04-30'])
- `daily_sales.series`: 카테고리별 시계열 배열
  ```json
  [
    { "label": "국내분유", "color": "#3b82f6", "data": [숫자, ...] },
    { "label": "커피",     "color": "#ef4444", "data": [숫자, ...] },
    { "label": "단백질보충제", "color": "#22c55e", "data": [숫자, ...] },
    { "label": "우유/요거트", "color": "#eab308", "data": [숫자, ...] },
    { "label": "두유",     "color": "#a855f7", "data": [숫자, ...] }
  ]
  ```

## DOCX 섹션

```json
{
  "type": "table",
  "heading": "일일 카테고리별 매출 현황",
  "headers": ["날짜", "국내분유", "커피", "단백질보충제", "우유/요거트", "두유"],
  "rows": [
    ["{daily_sales.labels[i]}", "{series[0].data[i]}", "{series[1].data[i]}", "{series[2].data[i]}", "{series[3].data[i]}", "{series[4].data[i]}"]
  ]
}
```

> ⚠️ **원본은 5개 카테고리 매출 추이를 겹쳐 그리는 멀티라인 차트였지만, docx 생성기의 `chart`
> 타입은 막대 시리즈 + 단일 꺾은선 시리즈로 구성된 콤보 차트만 지원하고(막대 없는 다중 라인
> 차트는 지원하지 않는다), 5개의 독립된 라인 시리즈를 표현할 수 없다. 따라서 이 섹션은
> `table`로 낸다** — `daily_sales.labels`(날짜)를 행으로, `daily_sales.series`의 각 카테고리
> (매출 상위 5개, `label` 필드 순서 그대로)를 열로 펼친다.
- `rows`에는 `daily_sales.labels` 배열의 각 날짜(`i`)마다 한 행씩, 그 날짜의 `daily_sales.series`
  5개 항목의 `data[i]` 값을 순서대로 채운 행을 전부 넣는다(전체 기간 다 낸다 — 상/하한 컷 없음).
- 매출 금액은 `toLocaleString()` 스타일 천 단위 콤마 포맷 문자열로 만들어 넣는다.