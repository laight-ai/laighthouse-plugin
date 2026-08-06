# MTD Section 1: 월 목표 카드

**report_type:** `mtd` (항상 포함) — naver 기반 default generator 브랜드 전용(다형식품 등).

**별도 MCP 호출 아님 — mtd-section-2(목표 달성 현황)와 같은 `get_target_progress_v2` 응답을 재사용한다.**

`report-backend`의 `schemas/component.py::TargetProgression`은 `name="목표 달성 현황"` 컴포넌트
하나뿐이고 (`default/_mtd_components.py::build_target_progression`이 컴포넌트를 1개만 만든다),
프론트엔드가 그 데이터 하나를 **두 개의 시각 블록**으로 나눠 그린다:
1. 이 파일(mtd-section-1) — 상단 "월 목표" 요약 스트립. `target_cost`/`target_revenue`/`target_roas`만 표시.
2. `mtd-section-2-achievement.md` — 하단 "목표 달성 현황" 카드. target/actual/진행률 표시.

**따라서 mtd-section-2를 렌더링할 때는 반드시 이 mtd-section-1도 그 바로 위에 함께 렌더링한다** —
이 둘은 항상 쌍으로 나온다. mtd-section-2 호출 시 이미 받은 응답을 그대로 여기서도 사용하면 되고,
별도로 다시 호출할 필요 없다.

## MCP 도구 호출: `get_target_progress_v2` (mtd-section-2와 동일 호출 재사용)

```json
{ "brand_name": "...", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }
```

> ℹ️ `get_target_progress_v2` 응답은 markdown이다 — `month`/`as_of_date`/`media` 헤더 라인 뒤에
> 행(cost/revenue/roas) × 열(target|actual|progress_ratio) 표가 온다. `target_cost`는 cost 행의 target 열,
> `actual_roas`는 roas 행의 actual 열에 대응하는 식으로 읽는다. 해당 월 예산(media_mix)이 없으면 예외 대신
> "No naver budget/target available for {month}." 메시지 한 줄이 반환된다.

> ⚠️ **`target_progress`(범용 툴)를 여기 쓰지 않는다 — `get_target_progress_v2`를 쓴다.**
> `get_target_progress_v2`는 report-backend `default` generator의 "목표 달성 현황"이 실제로
> 재현하는 계산과 동일한 소스다.

## 필요 데이터 (MCP)

응답 필드를 그대로 매핑한다 (roas는 비율값이므로 표시 시 × 100):
- `monthly_budget_goal` ← `target_cost`
- `monthly_revenue_goal` ← `target_revenue`
- `monthly_roas_goal` ← `target_roas × 100` (비율 → %, 예: 5.06 → 506%)
