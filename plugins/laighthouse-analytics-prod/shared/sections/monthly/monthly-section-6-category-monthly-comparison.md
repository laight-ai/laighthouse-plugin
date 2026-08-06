# Monthly Section 6: 카테고리별 월간 매출액 비교

**report_type:** `monthly` (항상 포함) — mtd(MK)에는 없는 신규 섹션.

이 섹션은 "이번 달 vs 전월"의 카테고리별 매출액을 나란히 비교하는 바 차트다. 상위 5개
카테고리(이번 달 매출 기준)를 개별 막대로 보여주고, 나머지 카테고리는 모두 합쳐 "기타" 막대
하나로 묶는다. 각 카테고리 쌍 위에는 전월 대비 증감률(%)을 배지로 표시한다.

---

## 도구 선정 근거 (중요 — 반드시 읽고 넘어갈 것)

> ⚠️ **`get_sku_sales_monthly_table`(범용 GA 아이템 성과 테이블)을 여기 쓰지 않는다.** 처음
> 설계 시 이 도구가 참고 후보로 거론되었으나, naver 기반 default generator 브랜드(남양유업 등)는
> GA 아이템 카탈로그 테이블(`ga_itemperf_catalog`) 자체에 대한 읽기 권한이 없어 **SQL 권한 오류로
> 항상 실패한다** (`SELECT command denied ... 5_7_ga_itemperf_catalog`, 2026-07-22 확인). 이
> 도구는 Aqua Glow/Saturday Skin류 GA 기반 브랜드에서만 동작하는 범용 SKU 도구이며, naver 브랜드
> 에는 애초에 대응하는 데이터소스가 없다.
> 대신 naver 전용 `get_naver_category_sales`(mtd-section-6.1이 상품별 누적 판매액에 쓰는 것과
> 동일한 도구)를 **월별로 두 번** 호출해 "이번 달"과 "전월"의 카테고리 합계를 각각 받아온다 —
> `get_sku_sales_monthly_table`의 "상위 N + 나머지" 개념만 참고해, 상위 5개 카테고리 + 기타
> 1개로 재구성한다.

## MCP 도구 호출: `get_naver_category_sales` (두 번 호출, `prev_start_date`/`prev_end_date` 없이)

```json
// 1) 이번 달
{ "brand_name": "...", "start_date": "이번달 1일", "end_date": "이번달 말일" }
// 2) 전월 (동일 브랜드, 전월 전체 구간)
{ "brand_name": "...", "start_date": "전월 1일", "end_date": "전월 말일" }
```

> ⚠️ 이 섹션에서는 도구의 `prev_start_date`/`prev_end_date` 파라미터(mtd-section-6.1이 쓰는
> 자동 `mom` 계산)를 넘기지 않는다 — 그 `mom`은 **카테고리 단위**로만 계산되며, 이 섹션처럼 "상위
> 5개 밖 카테고리를 합친 기타" 묶음에 대한 증감률은 별도로 직접 계산해야 하기 때문이다. 대신 두
> 기간을 독립적으로 호출해 각 기간의 `items[]`(카테고리별 `category`/`sales`)를 그대로 받고,
> 이 스킬이 상위 5개/기타 그룹핑과 증감률 계산을 함께 수행한다.

## 필요 데이터 (MCP)
- `curr_items[]`: 이번 달 카테고리별 `{ category, sales }` 배열 (호출 1의 `items`)
- `prev_items[]`: 전월 카테고리별 `{ category, sales }` 배열 (호출 2의 `items`)

## 데이터 가공 (이 단계만 예외적으로 허용 — 상위 규칙 참고)

1. `curr_items`를 `sales` 내림차순 정렬 → 상위 5개 카테고리명을 추출한다.
2. 상위 5개 각각에 대해: `curr` = 해당 카테고리의 이번 달 `sales`, `prev` = `prev_items`에서
   같은 `category`를 찾은 `sales` (없으면 0).
3. "기타" = 상위 5개에 포함되지 않은 나머지 카테고리 전체를 각각 이번 달/전월 기준으로
   합산(`sum(sales)`)한 값.
4. 6개 막대(상위 5 + 기타) 각각에 대해 `change_pct = (curr - prev) / prev * 100`을 계산한다.
   `prev`가 0이면 `change_pct`는 `null`로 두고 배지에 "신규"로 표시한다 (0으로 나누지 않는다).
5. 위 5단계는 전부 기계적 재집계(합산·정렬·나눗셈)이며, 값 자체를 임의로 보정·추정하지 않으므로
   상위 "데이터 처리 원칙"과 충돌하지 않는다.

## 응답 데이터 구조 (가공 후, 렌더링에 쓰는 최종 형태)

```json
{
  "category_monthly_comparison": {
    "prev_month_label": "26년 2월",
    "curr_month_label": "26년 3월",
    "labels": ["국내분유", "커피", "단백질보충제", "우유/요거트", "두유", "기타"],
    "prev": [563042000, 375669000, 195245000, 92661000, 28052426, 46471380],
    "curr": [592787349, 369661967, 228341896, 110042863, 29897949, 59117096],
    "change_pct": [5.1, -1.6, 17.0, 18.8, 6.6, 27.2]
  }
}
```
