# MTD Section 1: 월 목표 카드

**report_type:** `mtd` (항상 포함) — naver 기반 default generator 브랜드 전용(다형식품 등).

**별도 MCP 호출 아님 — mtd-section-2(목표 달성 현황)와 같은 `get_naver_target_progress` 응답을 재사용한다.**

`report-backend`의 `schemas/component.py::TargetProgression`은 `name="목표 달성 현황"` 컴포넌트
하나뿐이고 (`default/_mtd_components.py::build_target_progression`이 컴포넌트를 1개만 만든다),
프론트엔드가 그 데이터 하나를 **두 개의 시각 블록**으로 나눠 그린다:
1. 이 파일(mtd-section-1) — 상단 "월 목표" 요약 스트립. `target_cost`/`target_revenue`/`target_roas`만 표시.
2. `mtd-section-2-achievement.md` — 하단 "목표 달성 현황" 카드. target/actual/진행률 표시.

**따라서 mtd-section-2를 렌더링할 때는 반드시 이 mtd-section-1도 그 바로 위에 함께 렌더링한다** —
이 둘은 항상 쌍으로 나온다. mtd-section-2 호출 시 이미 받은 응답을 그대로 여기서도 사용하면 되고,
별도로 다시 호출할 필요 없다.

## MCP 도구 호출: `get_naver_target_progress` (mtd-section-2와 동일 호출 재사용)

```json
{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date" }
```

> ⚠️ **`target_progress`(범용 툴)를 여기 쓰지 않는다.** `target_progress`는 v1 로직
> (`services/target_progress.py`)을 감싸는데, v1은 `aw_compiled`/`fb_compiled`(Google/Meta 광고
> 플랫폼) 실적 테이블에서 target/actual을 가져오므로 naver 전용 브랜드(다형식품 등)는 매출/ROAS
> 목표와 실적이 전부 0으로 나온다 (2026-07-10 확인된 버그). `get_naver_target_progress`는 v2
> (`services/v2/target_progress.py`)를 감싸며, naver 브랜드의 media_mix 예산 + naver 광고 실적을
> 그대로 반영한다 — report-backend `default` generator의 "목표 달성 현황"이 실제로 재현하는 계산과
> 동일한 소스다.

## 필요 데이터 (MCP)

응답 필드를 그대로 매핑한다 (roas는 비율값이므로 표시 시 × 100):
- `monthly_budget_goal` ← `target_cost`
- `monthly_revenue_goal` ← `target_revenue`
- `monthly_roas_goal` ← `target_roas × 100` (비율 → %, 예: 5.06 → 506%)

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