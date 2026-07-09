# Section 1: 월 목표 카드

**트리거 키워드:** `월 목표`

## MCP 도구 호출: `target_progress`

```json
{ "brand_name": "...", "month": "YYYY-MM" }
```
(campaign_type 미지정 = 전체 캠페인 기준)

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
