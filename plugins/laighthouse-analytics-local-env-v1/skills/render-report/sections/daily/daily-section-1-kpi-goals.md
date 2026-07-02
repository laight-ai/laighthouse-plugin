# Daily Section 1: 월 목표 카드

**report_type:** `daily`
**MCP 도구:** `target-progress` → `sales` 데이터

## 필요 데이터
- `sales.budget_goal`: Monthly Budget Plan ($)
- `sales.revenue_goal`: Monthly Revenue Target ($)
- `sales.roas_goal`: Monthly ROAS Target (%)

## HTML

```html
<!-- DAILY SECTION 1: 월 목표 카드 -->
<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0; border:1px solid #e2e8f0; margin-bottom:16px; background:white;">
  <div style="padding:20px 24px; border-right:1px solid #e2e8f0;">
    <div style="font-size:12px; color:#3b82f6; font-weight:500; margin-bottom:10px;">Monthly Budget Plan</div>
    <div style="font-size:28px; font-weight:700; color:#1e293b;">${sales.budget_goal}</div>
  </div>
  <div style="padding:20px 24px; border-right:1px solid #e2e8f0;">
    <div style="font-size:12px; color:#3b82f6; font-weight:500; margin-bottom:10px;">Monthly Revenue Target</div>
    <div style="font-size:28px; font-weight:700; color:#1e293b;">$ {sales.revenue_goal}</div>
  </div>
  <div style="padding:20px 24px;">
    <div style="font-size:12px; color:#3b82f6; font-weight:500; margin-bottom:10px;">Monthly ROAS Target</div>
    <div style="font-size:28px; font-weight:700; color:#1e293b;">{sales.roas_goal} %</div>
  </div>
</div>
```

## Script
없음 (정적 카드)
