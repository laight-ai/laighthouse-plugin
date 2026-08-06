# MTD Section 2: 목표 달성 현황

**report_type:** `mtd` (항상 포함) — naver 기반 default generator 브랜드 전용(다형식품 등).
Meta/Google 브랜드(Saturday Skin, Aqua Glow)의 daily 보고서는 이 파일을 쓰지 않는다 —
`shared/sections/daily/daily-section-2-overview.md`가 별도로 존재한다.

---

## MCP 도구 호출: `get_target_progress_v2`

```json
{ "brand_name": "...", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }
```

> ℹ️ `get_target_progress_v2` 응답은 markdown이다 — `month`/`as_of_date`/`media` 헤더 라인 뒤에
> 행(cost/revenue/roas) × 열(target|actual|progress_ratio) 표가 온다. `target_cost`는 cost 행의 target 열,
> `actual_roas`는 roas 행의 actual 열에 대응하는 식으로 읽는다. 해당 월 예산(media_mix)이 없으면 예외 대신
> "No naver budget/target available for {month}." 메시지 한 줄이 반환된다.

> ⚠️ **범용 `target_progress` 툴을 여기 쓰지 않는다 — `get_target_progress_v2`를 쓴다.**
> `get_target_progress_v2`는 report-backend
> `default/_mtd_components.py::build_target_progression`(nvad+nvgfa_ad+nvgfa_dp+nvss 합산)이 실제로
> 계산하는 것과 동일한 소스다 — `campaign_type`(sales/branding) 개념 자체가 없다.
>
> 이 도구는 target과 actual을 **한 번의 호출로 모두** 반환한다 (`get_ad_performance_daily_table`을
> 별도로 합산할 필요 없음 — 이전 버전에서 썼던 우회 계산은 더 이상 필요 없다).

---

## 필요 데이터

응답 필드를 그대로 매핑한다 (`target_roas`/`actual_roas`/`*_progress_ratio`는 비율값이므로 표시 시 × 100):

- `overview.budget_goal` ← `target_cost`
- `overview.budget_spent` ← `actual_cost`
- `overview.budget_spent_rate` ← `cost_progress_ratio × 100`
- `overview.revenue_goal` ← `target_revenue`
- `overview.revenue_actual` ← `actual_revenue`
- `overview.revenue_achievement_rate` ← `revenue_progress_ratio × 100`
- `overview.roas_goal` ← `target_roas × 100`
- `overview.roas_actual` ← `actual_roas × 100`

---
