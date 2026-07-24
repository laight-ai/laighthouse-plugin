# MTD Section 2: 목표 달성 현황

**report_type:** `mtd` (항상 포함) — naver 기반 default generator 브랜드 전용(다형식품 등).
Meta/Google 브랜드(Saturday Skin, Aqua Glow)의 daily 보고서는 이 파일을 쓰지 않는다 —
`sections/daily/daily-section-2-overview.md`가 별도로 존재한다.

---

## MCP 도구 호출: `get_naver_target_progress`

```json
{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date" }
```

> ⚠️ **범용 `target_progress` 툴을 여기 쓰지 않는다 (2026-07-10 확인된 버그).** `target_progress`는
> v1 로직(`services/target_progress.py`)을 감싸는데, v1은 `aw_compiled`/`fb_compiled`(Google/Meta
> 광고 플랫폼) 실적 테이블에서 target/actual을 가져온다 — naver 전용 브랜드는 매출/ROAS 목표와 실적이
> 전부 0으로 나온다. `get_naver_target_progress`는 v2(`services/v2/target_progress.py`)를 감싸며,
> naver 브랜드의 media_mix 예산 + naver 광고 실적 그대로를 반영한다. 이것이 report-backend
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

## PPT 섹션

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
      "diff": "목표 {overview.revenue_goal} · 매출 {overview.revenue_actual}"
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
- `get_naver_target_progress`가 `ValueError`(예산 미설정, 404 매핑)를 내면 목표 관련 필드 전체를
  "목표 미설정"으로 표시한다 — 임의로 0을 만들어 넣지 않는다.
- `mtd-section-1-kpi-goals.md`는 이 섹션과 항상 쌍으로, 바로 위에 렌더링한다 (같은
  `get_naver_target_progress` 응답 재사용, 별도 재호출 없음).