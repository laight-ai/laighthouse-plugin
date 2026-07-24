# Monthly Section 1: 월 목표 카드

**report_type:** `monthly` (항상 포함) — naver 기반 default generator 브랜드 전용(남양유업 등).
mtd(MK)와 완전히 동일한 포맷/HTML을 쓴다 — 차이는 오직 `as_of_date`뿐이다 (mtd는 기준일까지,
monthly는 항상 해당 월의 **마지막 날**).

**별도 MCP 호출 아님 — monthly-section-2(목표 달성 현황)와 같은 `get_naver_target_progress`
응답을 재사용한다.**

`report-backend`의 `schemas/component.py::TargetProgression`은 `name="목표 달성 현황"` 컴포넌트
하나뿐이고, 프론트엔드가 그 데이터 하나를 **두 개의 시각 블록**으로 나눠 그린다:
1. 이 파일(monthly-section-1) — 상단 "월 목표" 요약 스트립. `target_cost`/`target_revenue`/
   `target_roas`만 표시.
2. `monthly-section-2-achievement.md` — 하단 "목표 달성 현황" 카드. target/actual/진행률 표시.

**따라서 monthly-section-2를 렌더링할 때는 반드시 이 monthly-section-1도 그 바로 위에 함께
렌더링한다** — 이 둘은 항상 쌍으로 나온다.

## MCP 도구 호출: `get_naver_target_progress` (monthly-section-2와 동일 호출 재사용)

```json
{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "해당 월의 마지막 날 (예: 2026-03-31)" }
```

> ⚠️ **`as_of_date`는 mtd 보고서와 달리 항상 해당 월의 말일로 고정한다.** monthly 보고서는
> full month(월 전체) 실적을 다루므로, 부분월(MTD) 커트오프 개념이 없다. 사용자가 대상 월
> (예: "2026년 3월")만 지정하면 그 달의 마지막 날짜(2026-03-31)를 `as_of_date`로 계산해 넣는다.
>
> ⚠️ **범용 `target_progress`(v1)를 여기 쓰지 않는다.** v1은 `aw_compiled`/`fb_compiled`
> (Google/Meta 실적 테이블)에서 target/actual을 가져오므로 naver 전용 브랜드는 매출/ROAS 목표·
> 실적이 전부 0으로 나온다. `get_naver_target_progress`(v2)가 naver 브랜드의 media_mix 예산 +
> naver 광고 실적을 그대로 반영하는 유일한 정확한 소스다.

## 필요 데이터 (MCP)

응답 필드를 그대로 매핑한다 (roas는 비율값이므로 표시 시 × 100):
- `monthly_budget_goal` ← `target_cost`
- `monthly_revenue_goal` ← `target_revenue`
- `monthly_roas_goal` ← `target_roas × 100` (비율 → %, 예: 4.32 → 432%)

## PPT 섹션

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
