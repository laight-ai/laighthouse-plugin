# Monthly Section 4: 월별 광고 성과 차트

**report_type:** `monthly` (항상 포함) — naver 기반 default generator 브랜드 전용(남양유업 등).

mtd(MK)의 `mtd-section-4-monthly-chart.md`와 **완전히 동일한 포맷/차트**다 (혼합 바+라인
차트, 최근 6개월). 유일한 차이는 `as_of_date`를 항상 대상 월의 **마지막 날**로 준다는 점뿐이다
— mtd는 부분월 커트오프가 있지만 monthly는 매월 전체를 다루므로, 차트에 표시되는 마지막
달(당월)도 다른 달과 동일하게 달력상 전체 기간을 커버한다.

## MCP 도구 호출: `get_naver_monthly_ad_performance`

```json
{ "brand_name": "...", "start_month": "5개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "as_of_date": "당월 마지막 날" }
```

> ⚠️ **`get_ad_performance_monthly_table`을 여기 쓰지 않는다** (mtd-section-4와 동일한 이유 —
> 그 도구는 report-backend가 실제로 호출하는 API가 아닌 별개의 범용 파이프라인을 탄다). 이 차트는
> `get_naver_channel_progression`을 월마다 반복 호출해 5개 채널(BRS/PLINK/NVSHOP/GFA
> 애드부스트/GFA 디스플레이)을 합산하는 `get_naver_monthly_ad_performance` 전용 도구를 쓴다.
> `as_of_date`는 범위의 마지막 달(당월)만 그 날짜까지로 자르는데, monthly 보고서에서는 항상
> 당월 말일을 주므로 실질적으로 "자르기"가 발생하지 않고 전체 달력월이 그대로 반영된다.

## 필요 데이터 (MCP)
최근 6개월 배열 (응답 `items[]`의 `month`/`cost`/`purchase_amount`/`roas` 필드에서 매핑):
- `monthly_chart.labels`: 연월 레이블 배열 (예: ['25년 10월', ..., '26년 3월']) ← `month`
- `monthly_chart.ad_cost`: 광고비 배열 (숫자, 원) ← `cost`
- `monthly_chart.revenue`: 매출 배열 (숫자, 원) ← `purchase_amount`
- `monthly_chart.roas`: ROAS 배열 (숫자, %) ← `roas` **그대로** (이미 percentage 스케일로
  반환되므로 × 100 변환 불필요)

## DOCX 섹션

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

- `categories`는 `monthly_chart.labels`(연월 레이블 배열, 예: `["25년 10월", ..., "26년 3월"]`)를
  그대로 넣는다.
- `bar_series`는 광고비(`monthly_chart.ad_cost`)와 매출(`monthly_chart.revenue`) 두 시리즈,
  `line_series`는 ROAS(`monthly_chart.roas`) 한 시리즈다 — 원본 Chart.js 혼합 차트(막대 2개 +
  꺾은선 1개)와 동일 구성.
- 위 JSON의 문자열 자리(`"{monthly_chart.labels}"` 등)는 실제 렌더링 시 그 배열/리스트 값으로
  그대로 치환한다(문자열이 아니라 JSON 배열이 들어간다).
