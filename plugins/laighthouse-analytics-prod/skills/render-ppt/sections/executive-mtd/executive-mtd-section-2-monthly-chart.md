# Executive-MTD Section 2: 월별 광고 성과 차트

**report_type:** `executive-mtd` (항상 포함) — naver 기반 default generator 브랜드 전용
(남양유업 등). mtd(MK)의 `mtd-section-4-monthly-chart.md`와 **완전히 동일한 포맷/차트**다
(혼합 바+라인 차트, 최근 6개월).

⚠️ **executive-mtd에서는 이 섹션의 순서가 mtd(MK)와 다르다** — mtd(MK)는 Executive Summary
(3번) 다음에 월별 광고 성과 차트(4번)가 오지만, executive-mtd는 **이 차트가 Executive Summary
보다 먼저** 온다. 임원이 먼저 추세 그래프로 큰 그림을 보고, 그다음 Executive Summary에서 그
추세에 대한 해석/의사결정 포인트를 읽게 하려는 의도다.

## MCP 도구 호출: `get_naver_monthly_ad_performance`

```json
{ "brand_name": "...", "start_month": "5개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "as_of_date": "target_date" }
```

> ⚠️ **`get_ad_performance_monthly_table`을 여기 쓰지 않는다** (mtd-section-4와 동일한 이유 —
> report-backend가 실제로 호출하는 API가 아닌 별개의 범용 파이프라인을 탄다). 이 차트는
> `get_naver_channel_progression`을 월마다 반복 호출해 5개 채널을 합산하는 전용 도구
> `get_naver_monthly_ad_performance`를 쓴다.

## 필요 데이터 (MCP)
최근 6개월 배열 (응답 `items[]`의 `month`/`cost`/`purchase_amount`/`roas` 필드에서 매핑):
- `monthly_chart.labels`: 연월 레이블 배열 ← `month`
- `monthly_chart.ad_cost`: 광고비 배열 (숫자, 원) ← `cost`
- `monthly_chart.revenue`: 매출 배열 (숫자, 원) ← `purchase_amount`
- `monthly_chart.roas`: ROAS 배열 (숫자, %) ← `roas` **그대로** (× 100 변환 불필요)

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

- `categories`는 `monthly_chart.labels`(연월 레이블 배열)를 그대로 넣는다.
- `bar_series`는 광고비(`monthly_chart.ad_cost`)와 매출(`monthly_chart.revenue`) 두 시리즈,
  `line_series`는 ROAS(`monthly_chart.roas`) 한 시리즈다 — 원본 Chart.js 혼합 차트(막대 2개 +
  꺾은선 1개)와 동일 구성.
- 위 JSON의 문자열 자리(`"{monthly_chart.labels}"` 등)는 실제 렌더링 시 그 배열/리스트 값으로
  그대로 치환한다(문자열이 아니라 JSON 배열이 들어간다).
