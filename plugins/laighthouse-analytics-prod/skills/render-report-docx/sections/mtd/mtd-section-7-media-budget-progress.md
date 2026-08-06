# MTD Section 7: 매체별 예산 소진 현황 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/mtd/mtd-section-7-media-budget-progress.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "table",
  "heading": "매체별 예산 소진 현황 ({media_budget_progress.channel_group})",
  "headers": ["매체", "예산 소진율", "목표 소진", "예산 소진", "일 소진예산", "일 평균 소진액"],
  "rows": [
    ["{channel}", "{spent_rate}%", "{budget_goal_fmt}", "{spent_fmt}", "{daily_budget_fmt}", "{daily_spent_avg_fmt}"],
    ["합계", "{total.spent_rate}%", "{total.budget_goal_fmt}", "{total.spent_fmt}", "{total.daily_budget_fmt}", "{total.daily_spent_avg_fmt}"]
  ]
}
```

- `rows`에는 `media_budget_progress.rows` 배열의 모든 항목을 위 필드 매핑대로 한 행씩 그대로
  넣고, 마지막에 `media_budget_progress.total`을 "합계" 행으로 한 번 더 추가한다(원본 HTML의
  진행바+합계 강조 행과 동일 구성, 진행바 자체는 정적 문서 표에서 표현하지 않고 `{spent_rate}%`
  수치만 낸다).
- 금액 필드(`budget_goal`/`spent`/`daily_budget`/`daily_spent_avg`)는 `toLocaleString()` 스타일
  천 단위 콤마 포맷 문자열로 만들어 넣는다.
- 매체 개수는 MCP 데이터에 따라 가변 — `spent_rate` 임계값별 진행바 색상 강조(원본의
  90%/70% 기준)는 정적 표에서는 표현하지 않는다(검색창/페이지네이션과 마찬가지로 정적
  문서에서는 의미가 없음).
