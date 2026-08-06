# Monthly Section 7: 일일 카테고리별 매출 현황 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/monthly/monthly-section-7-daily-category-chart.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

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

> ⚠️ **원본은 5개 카테고리 매출 추이를 겹쳐 그리는 멀티라인 차트였지만, docx 생성기의 (구버전) `chart`
> 타입은 막대 시리즈 + 단일 꺾은선 시리즈로 구성된 콤보 차트만 지원하고(막대 없는 다중 라인
> 차트는 지원하지 않는다), 5개의 독립된 라인 시리즈를 표현할 수 없다. 따라서 이 섹션은
> `table`로 낸다** (mtd-section-6과 동일한 판단) — `daily_sales.labels`(날짜)를 행으로,
> `daily_sales.series`의 각 카테고리(매출 상위 5개, `label` 필드 순서 그대로 — monthly-section-6과
> 동일 카테고리로 맞춘다)를 열로 펼친다.
- `rows`에는 `daily_sales.labels` 배열의 각 날짜(`i`)마다 한 행씩, 그 날짜의 `daily_sales.series`
  5개 항목의 `data[i]` 값을 순서대로 채운 행을 전부 넣는다(월 전체 다 낸다 — 상/하한 컷 없음).
- 매출 금액은 `toLocaleString()` 스타일 천 단위 콤마 포맷 문자열로 만들어 넣는다.
- 데이터가 비어있으면 이 섹션 자체를 생략한다(임의로 채우지 않는다).


> ✅ **멀티라인 차트 복원**: 이제 docx 생성기가 `line_chart` 타입(카테고리별 색상 라인 N개)을
> 지원하므로, 이 섹션은 HTML 원본과 동일하게 상위 5개 카테고리의 일별 매출 추이를 멀티라인
> 차트로 렌더링한다 (`section_mapping.py`가 `line_chart` 섹션을 직접 생성 — 표 대체는 폐기).
