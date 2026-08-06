# Executive-MTD Section 2: 월별 광고 성과 차트 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/executive-mtd/executive-mtd-section-2-monthly-chart.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

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

- `categories`는 `monthly_chart.labels`(연월 레이블 배열)를 그대로 넣는다.
- `bar_series`는 광고비(`monthly_chart.ad_cost`)와 매출(`monthly_chart.revenue`) 두 시리즈,
  `line_series`는 ROAS(`monthly_chart.roas`) 한 시리즈다 — 원본 Chart.js 혼합 차트(막대 2개 +
  꺾은선 1개)와 동일 구성.
- 위 JSON의 문자열 자리(`"{monthly_chart.labels}"` 등)는 실제 렌더링 시 그 배열/리스트 값으로
  그대로 치환한다(문자열이 아니라 JSON 배열이 들어간다).
