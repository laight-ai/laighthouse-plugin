# Executive-MTD Section 1: 목표 달성 현황

**report_type:** `executive-mtd` (항상 포함) — naver 기반 default generator 브랜드 전용
(남양유업 등). mtd(MK)의 `mtd-section-2-achievement.md`와 **완전히 동일한 포맷/HTML/레이블**
이다 (Monthly report의 achievement 섹션과 달리 "기간"이라는 표현을 그대로 유지한다 — 이 보고서도
MTD를 다루므로 mtd(MK)와 동일하게 부분월 표현이 맞다).

---

## MCP 도구 호출: `get_target_progress_v2`

```json
{ "brand_name": "...", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }
```

> ℹ️ `get_target_progress_v2` 응답은 markdown이다 — `month`/`as_of_date`/`media` 헤더 라인 뒤에
> 행(cost/revenue/roas) × 열(target|actual|progress_ratio) 표가 온다. `target_cost`는 cost 행의 target 열,
> `actual_roas`는 roas 행의 actual 열에 대응하는 식으로 읽는다. 해당 월 예산(media_mix)이 없으면 예외 대신
> "No naver budget/target available for {month}." 메시지 한 줄이 반환된다.

> ⚠️ 범용 `target_progress` 툴을 여기 쓰지 않는다 — naver 전용 브랜드는 매출/ROAS가 전부 0으로
> 나온다. `get_target_progress_v2`는 target과 actual을 한 번의 호출로 모두 반환한다.

---

## 필요 데이터

응답 필드를 그대로 매핑한다 (`target_roas`/`actual_roas`/`*_progress_ratio`는 비율값이므로
표시 시 × 100):

- `overview.budget_goal` ← `target_cost`
- `overview.budget_spent` ← `actual_cost`
- `overview.budget_spent_rate` ← `cost_progress_ratio × 100`
- `overview.revenue_goal` ← `target_revenue`
- `overview.revenue_actual` ← `actual_revenue`
- `overview.revenue_achievement_rate` ← `revenue_progress_ratio × 100`
- `overview.roas_goal` ← `target_roas × 100`
- `overview.roas_actual` ← `actual_roas × 100`

---

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
