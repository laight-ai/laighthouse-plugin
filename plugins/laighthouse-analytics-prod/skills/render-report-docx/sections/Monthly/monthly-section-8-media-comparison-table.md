# Monthly Section 8: 매체별 성과 비교 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/monthly/monthly-section-8-media-comparison-table.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "heading",
  "text": "매체 별 성과 비교"
}
```

이어서 `media_monthly_comparison` 배열의 채널 그룹마다 아래 `table` 섹션을 하나씩(총 5개)
반복해서 낸다 — HTML의 "채널 그룹마다 하위 표 반복"을 각 그룹별 독립된 `table` 섹션 객체로
펼친 것이다 (하나의 `table` 섹션은 헤더+행 하나만 표현하므로, 그룹마다 별도 섹션으로 분리):

```json
{
  "type": "table",
  "heading": "{channel_label}",
  "headers": ["월", "광고비 (원)", "매출 (원)", "ROAS"],
  "rows": [
    ["{rows[0].month_label}", "{rows[0].cost_fmt}", "{rows[0].revenue_fmt}", "{rows[0].roas_fmt}%"],
    ["{rows[1].month_label}", "{rows[1].cost_fmt}", "{rows[1].revenue_fmt}", "{rows[1].roas_fmt}%"]
  ]
}
```

- 상위 `heading`(`매체 별 성과 비교`) 섹션 하나 뒤에, `media_monthly_comparison`의 각 채널 그룹당
  위 `table` 섹션을 하나씩 순서대로 추가한다 — `rows[0]`은 전월, `rows[1]`은 이번달이다.
- `cost`/`revenue`는 `toLocaleString()`으로 천 단위 콤마 포맷 (원 단위, 접미사 없음).
- `roas`는 소수점 둘째자리까지 표시 (예: `723.76%`).
- 채널 그룹 순서는 항상 위 매핑 표 순서(브랜드검색 → 파워링크 → 쇼핑검색 → GFA 애드부스트 →
  GFA 디스플레이)로 고정한다.
- 특정 채널에 예산/집행 자체가 없는 브랜드는 해당 채널 그룹을 생략하지 않고 `cost`/`revenue`가
  0인 행으로 표시한다 (임의 생략 금지).
- 데이터가 비어있으면 이 섹션 전체를 생략한다(임의로 채우지 않는다).
