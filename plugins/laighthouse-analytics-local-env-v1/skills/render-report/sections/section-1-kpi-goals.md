# Section 1: 월 목표 카드

**트리거 키워드:** `월 목표`

## 필요 데이터 (MCP)
- `monthly_budget_goal`: 월 예산 목표 (USD)
- `monthly_revenue_goal`: 월 매출 목표 (USD)
- `monthly_roas_goal`: 월 ROAS 목표 (%)

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
