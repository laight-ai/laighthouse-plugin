# MTD Section 1: 월 목표 카드 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/mtd/mtd-section-1-kpi-goals.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "kpi_cards",
  "cards": [
    { "label": "월 예산 목표", "value": "{monthly_budget_goal}" },
    { "label": "월 매출 목표", "value": "{monthly_revenue_goal}" },
    { "label": "월 ROAS 목표", "value": "{monthly_roas_goal}%" }
  ]
}
```

- 이 세 카드는 목표값만 표시하는 정적 카드이므로 `diff`/`diff_value`는 넣지 않는다.
- 금액 필드(`monthly_budget_goal`/`monthly_revenue_goal`)는 `toLocaleString()` 스타일 천 단위
  콤마 포맷 문자열로 만들어 넣는다.
