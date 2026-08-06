# MTD Section 6: 일일 카테고리별 매출 현황

**report_type:** `mtd` (항상 포함).

## MCP 도구 호출: `get_naver_item_sales_daily`

```json
{ "brand_name": "...", "start_date": "당월초", "end_date": "target_date" }
```
> ⚠️ **`group_by` 파라미터를 보내지 않는다.** 서버가 항상 `category_3rd` 기준으로 그룹핑해서
> 반환한다. `group_by` 키 자체를 요청 JSON에 넣지 않는다.
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`, `/v2/naver/item-sales/daily` 래퍼)
- mtd-section-6와 동일 호출 결과를 재사용 — `items[]`를 `(logdate, product_category_3rd)`로
  그룹핑해 `sum(sales_amount)`, 매출 상위 5개 카테고리만 시리즈로 렌더링

## MCP 도구 호출: `list_promotions` (2026-07-24 추가 — 아래 "프로모션 오버레이" 참고)

> ⚠️ **HTML 보고서(render-report) 전용** — PPT/DOCX 렌더링 시에는 `list_promotions` 호출과 프로모션 오버레이 단계를 전부 건너뛴다 (해당 출력 스펙에 오버레이 마크업이 없음).

```json
{ "brand_name": "...", "start_date": "당월초", "end_date": "target_date" }
```
- 위 `get_naver_item_sales_daily`와 정확히 같은 날짜 범위로 1회만 추가 호출한다.

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

## 프로모션 오버레이 (2026-07-24 추가, 2026-07-24 "특이사항" 라벨 삭제)

> ⚠️ **HTML 보고서(render-report) 전용** — PPT/DOCX 렌더링 시에는 `list_promotions` 호출과 프로모션 오버레이 단계를 전부 건너뛴다 (해당 출력 스펙에 오버레이 마크업이 없음).

스크린샷 참고 — 차트 아래에 프로모션 시작~종료 구간을 가로 브래킷(┃───┃)으로 표시하고 중앙에
"{프로모션명} ({시작}~{종료})" 라벨을 붙인다. `daily-section-4`(최근 7일 성과)의 "요일별 셀"
방식과 다른 이유: 이 차트는 최대 31일까지 다루므로 매일 칸을 만들면 너무 촘촘해진다 — 대신
구간 하나를 통째로 브래킷 하나로 표시한다. (초기 시안에는 브래킷 왼쪽에 "특이사항"이라는
고정 레이블을 뒀으나, 불필요하다고 판단해 삭제함 — 브래킷과 라벨만으로 충분히 의미가
전달된다.)

### 데이터 가공 (이 단계만 예외적으로 허용 — 상위 "데이터 처리 원칙" 참고)

1. `list_promotions` 응답의 `items[]`(각 `date_begin`/`date_end`/`title`)를 받는다.
2. 각 프로모션에 대해, `daily_sales.labels` 배열에서 `date_begin`/`date_end`에 해당하는 인덱스를
   찾는다. `date_begin`이 `labels[0]`보다 이르면 `start_idx=0`으로 clamp, `date_end`가
   `labels[last]`보다 늦으면 `end_idx=labels.length-1`로 clamp한다 (차트 범위 밖으로 삐져나온
   구간은 보이는 부분만 표시).
3. `date_begin`/`date_end`가 `daily_sales.labels`의 범위와 전혀 겹치지 않는(완전히 범위 밖)
   프로모션은 제외한다.
4. `range_label`은 `"{date_begin의 월}월 {date_begin의 일}일~{date_end의 일}일"` 형식으로 만든다
   (같은 달이면 월을 한 번만 표시 — 스크린샷의 "5월 1일~11일" 참고. 월이 걸치면
   "{시작월}월 {시작일}일~{종료월}월 {종료일}일"로 둘 다 표시).
5. 겹치는 프로모션이 여러 개면 각각을 별도의 행(브래킷 줄)으로 쌓는다 — 하나로 합치지 않는다.
6. 위 1~5단계는 전부 기계적 날짜 매칭·클램핑이며 프로모션 존재 여부를 임의로 추정하지 않으므로
   상위 "데이터 처리 원칙"과 충돌하지 않는다.

### 응답 데이터 구조 (가공 후)

```json
{
  "daily_promotions_ranges": [
    { "title": "5월 가정의달 세일", "start_idx": 0, "end_idx": 10, "range_label": "5월 1일~11일" }
  ]
}
```
(`start_idx`/`end_idx`는 `daily_sales.labels` 배열의 인덱스. 프로모션이 없으면 빈 배열 `[]`.)
