# Executive-MTD Section 1: 목표 달성 현황 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/executive-mtd/executive-mtd-section-1-achievement.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "kpi_cards",
  "cards": [
    {
      "label": "기간 예산대비 소진율",
      "value": "{overview.budget_spent_rate}%",
      "diff": "목표 {overview.budget_goal} · 소진 {overview.budget_spent}"
    },
    {
      "label": "기간 목표 매출 대비 달성률",
      "value": "{overview.revenue_achievement_rate}%",
      "diff": "목표 {overview.revenue_goal} · 기간 매출 {overview.revenue_actual}"
    },
    {
      "label": "기간 누적 ROAS",
      "value": "{overview.roas_actual}%",
      "diff": "목표 {overview.roas_goal}%"
    }
  ]
}
```

- 각 카드는 원본 HTML의 "기간 목표 / 실제" 두 값을 `diff` 필드 하나의 문자열로 합쳐서 담는다
  (예: `"목표 15,000,000 · 소진 8,400,000"`). 이 값들은 증감(+/-)이 아니라 목표 대비 절대값
  병기이므로 `diff_value`는 넣지 않는다(부호 기반 색상 강조 대상이 아님).
- 금액 필드(`budget_goal`/`budget_spent`/`revenue_goal`/`revenue_actual`)는 `toLocaleString()`
  스타일 천 단위 콤마 포맷 문자열로 만들어 넣는다.

## 렌더링 규칙
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- `get_target_progress_v2`가 예산 미설정 메시지("No naver budget/target available for {month}.")를 반환하면 목표 관련 필드 전체를
  "목표 미설정"으로 표시한다.
- 월 목표 카드(kpi-goals) 섹션은 제거되었다 — 이 섹션(목표 달성 현황)이 executive-mtd 보고서의 첫 번째 섹션이다.
