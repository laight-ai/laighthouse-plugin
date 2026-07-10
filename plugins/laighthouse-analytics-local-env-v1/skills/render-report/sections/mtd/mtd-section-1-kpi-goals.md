# MTD Section 1: 월 목표 카드

**report_type:** `mtd` (항상 포함) — naver 기반 default generator 브랜드 전용(다형식품 등).

**별도 MCP 호출 아님 — mtd-section-2(목표 달성 현황)와 같은 `target_progress` 응답을 재사용한다.**

`report-backend`의 `schemas/component.py::TargetProgression`은 `name="목표 달성 현황"` 컴포넌트
하나뿐이고 (`default/_mtd_components.py::build_target_progression`이 컴포넌트를 1개만 만든다),
프론트엔드가 그 데이터 하나를 **두 개의 시각 블록**으로 나눠 그린다:
1. 이 파일(mtd-section-1) — 상단 "월 목표" 요약 스트립. `items[].target`(=`target_full_month`)만 표시.
2. `mtd-section-2-achievement.md` — 하단 "목표 달성 현황" 카드. `target`/`actual`/진행률 표시.

**따라서 mtd-section-2를 렌더링할 때는 반드시 이 mtd-section-1도 그 바로 위에 함께 렌더링한다** —
이 둘은 항상 쌍으로 나온다. mtd-section-2 호출 시 이미 받은 응답을 그대로 여기서도 사용하면 되고,
별도로 다시 호출할 필요 없다.

## MCP 도구 호출: `target_progress` (mtd-section-2와 동일 호출 재사용)

```json
{ "brand_name": "...", "month": "YYYY-MM" }
```
(campaign_type 미지정 = 전체 캠페인 기준. 이 상단 스트립은 mtd-section-2의 카드(overview)와 동일한
target 값을 쓴다.)

## 필요 데이터 (MCP)
응답의 `items` 배열(3개: monthly_budget / monthly_revenue / monthly_roas)에서 `target_full_month`를 사용한다.
- `monthly_budget_goal` ← `items[metric=monthly_budget].target_full_month`
- `monthly_revenue_goal` ← `items[metric=monthly_revenue].target_full_month`
- `monthly_roas_goal` ← `items[metric=monthly_roas].target_full_month × 100` (소수 → %, 예: 2.2 → 220%)

## HTML

```html
<!-- SECTION 1: 월 목표 카드 -->
<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:16px;">
  <div class="card">
    <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 예산 목표</div>
    <div style="font-size:22px; font-weight:700; color:#1e293b;">{monthly_budget_goal}</div>
  </div>
  <div class="card">
    <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 매출 목표</div>
    <div style="font-size:22px; font-weight:700; color:#1e293b;">{monthly_revenue_goal}</div>
  </div>
  <div class="card">
    <div style="font-size:12px; color:#64748b; margin-bottom:8px;">월 ROAS 목표</div>
    <div style="font-size:22px; font-weight:700; color:#1e293b;">{monthly_roas_goal}%</div>
  </div>
</div>
```

## Script
없음 (정적 카드)
