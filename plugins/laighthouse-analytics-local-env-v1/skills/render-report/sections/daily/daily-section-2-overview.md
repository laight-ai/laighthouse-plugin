# Daily Section 2: Overview: Sales Campaign Performance

**report_type:** `daily`
**MCP 도구:** `target-progress` → `sales` 데이터

## 필요 데이터
- `sales.period_progress_pct`: 기간 진행률 (%) — 예: 3.3
- `sales.period_label`: 기간 레이블 — 예: "1/30 days"
- `sales.budget_utilization_pct`: Monthly Budget Utilization (%)
- `sales.budget_utilization_diff`: 목표 대비 차이 (%p) — 음수면 빨강
- `sales.budget_goal`, `sales.budget_spent`: 목표/현재 ($)
- `sales.revenue_achievement_pct`: Monthly Revenue Achievement (%)
- `sales.revenue_achievement_diff`: 목표 대비 차이 (%p)
- `sales.revenue_goal`, `sales.revenue_actual`: 목표/현재 ($)
- `sales.roas_achievement_pct`: Monthly ROAS Achievement (%)
- `sales.roas_achievement_diff`: 목표 대비 차이 (%p)
- `sales.roas_goal`, `sales.roas_actual`: 목표/현재 (%)

## HTML

```html
<!-- DAILY SECTION 2: Overview -->
<div style="background:white; border:1px solid #e2e8f0; padding:20px 24px; margin-bottom:16px;">
  <div style="font-size:15px; font-weight:700; color:#1e293b; margin-bottom:16px;">Overview: Sales Campaign Performance</div>

  <!-- Period Progress 바 -->
  <div style="background:#f8fafc; border-radius:8px; padding:14px 18px; margin-bottom:16px;">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
      <span style="font-size:12px; color:#64748b; background:#e2e8f0; border-radius:4px; padding:2px 8px;">Period Progress</span>
    </div>
    <div style="display:flex; align-items:center; gap:16px;">
      <span style="font-size:22px; font-weight:700; color:#1e293b; min-width:60px;">{sales.period_progress_pct}%</span>
      <span style="font-size:13px; color:#3b82f6; font-weight:600; min-width:80px;">{sales.period_label}</span>
      <div style="flex:1; position:relative; height:10px; background:#e2e8f0; border-radius:99px; overflow:visible;">
        <div style="height:100%; width:{sales.period_progress_pct}%; background:#3b82f6; border-radius:99px; position:relative;">
          <span style="position:absolute; right:-18px; top:-14px; font-size:11px; color:#3b82f6; font-weight:600; white-space:nowrap;">{sales.period_progress_pct}%</span>
        </div>
        <span style="position:absolute; left:0; bottom:-16px; font-size:11px; color:#94a3b8;">0%</span>
        <span style="position:absolute; right:0; bottom:-16px; font-size:11px; color:#94a3b8;">100%</span>
      </div>
    </div>
  </div>

  <!-- 3개 달성현황 카드 -->
  <div style="display:grid; grid-template-columns:repeat(3,1fr); border:1px solid #e2e8f0; border-radius:8px; overflow:hidden; margin-top:8px;">

    <div style="padding:18px 20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">Monthly Budget Utilization</div>
      <div style="font-size:26px; font-weight:700; color:#1e293b; margin-bottom:4px;">
        {sales.budget_utilization_pct}%
        <span style="font-size:13px; font-weight:600; color:{diff_color(sales.budget_utilization_diff)};">
          {sales.budget_utilization_diff}%p
        </span>
      </div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px; margin-top:10px;">
        <div><div style="color:#94a3b8;">Target</div><div style="font-weight:600;">${sales.budget_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">Current</div><div style="font-weight:600;">${sales.budget_spent}</div></div>
      </div>
    </div>

    <div style="padding:18px 20px; border-right:1px solid #e2e8f0; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">Monthly Revenue Achievement</div>
      <div style="font-size:26px; font-weight:700; color:#1e293b; margin-bottom:4px;">
        {sales.revenue_achievement_pct}%
        <span style="font-size:13px; font-weight:600; color:{diff_color(sales.revenue_achievement_diff)};">
          {sales.revenue_achievement_diff}%p
        </span>
      </div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px; margin-top:10px;">
        <div><div style="color:#94a3b8;">Target</div><div style="font-weight:600;">${sales.revenue_goal}</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">Current</div><div style="font-weight:600;">${sales.revenue_actual}</div></div>
      </div>
    </div>

    <div style="padding:18px 20px; text-align:center;">
      <div style="font-size:12px; color:#64748b; margin-bottom:8px;">Monthly ROAS Achievement</div>
      <div style="font-size:26px; font-weight:700; color:#1e293b; margin-bottom:4px;">
        {sales.roas_achievement_pct}%
        <span style="font-size:13px; font-weight:600; color:{diff_color(sales.roas_achievement_diff)};">
          {sales.roas_achievement_diff}%p
        </span>
      </div>
      <div style="display:flex; justify-content:center; gap:24px; font-size:12px; margin-top:10px;">
        <div><div style="color:#94a3b8;">Target</div><div style="font-weight:600;">{sales.roas_goal}%</div></div>
        <div style="width:1px; background:#e2e8f0;"></div>
        <div><div style="color:#94a3b8;">Current</div><div style="font-weight:600;">{sales.roas_actual}%</div></div>
      </div>
    </div>

  </div>
</div>
```

## Script
없음 (정적 카드)

## 렌더링 규칙
- `diff_color(v)`: v < 0 → `#ef4444` (빨강), v > 0 → `#16a34a` (초록), 0 → `#6b7280` (회색)
- diff 값은 항상 부호 포함 표시: `-2.4%p`, `+1.2%p`
- **Monthly ROAS Achievement 메인 수치**: `actual_mtd × 100` (예: `0.87 × 100 = 87%`)
- **Monthly ROAS Achievement diff**: `(actual_mtd × 100) - (target_mtd × 100)` 단순 차이 (예: `87 - 220 = -133%p`)
