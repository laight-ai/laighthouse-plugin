# Daily Section 4: Sales campaign: Daily performance in the last 7 days

**report_type:** `daily`
**MCP 도구:** `get_sales_performance_daily` (start_date=week_start, end_date=target_date)

## 필요 데이터
- `sales_daily.labels`: 날짜 레이블 배열 — 예: ["3/26(Thu)", "3/27(Fri)", ..., "4/1(Wed)"]
- `sales_daily.revenue`: 매출 배열 ($)
- `sales_daily.ad_spend`: 광고비 배열 ($)
- `sales_daily.roas`: ROAS 배열 (%)

## HTML

```html
<!-- DAILY SECTION 4: Sales Daily Chart -->
<div style="background:white; border:1px solid #e2e8f0; padding:20px 24px; margin-bottom:16px;">
  <div style="font-size:15px; font-weight:700; color:#1e293b; margin-bottom:16px;">
    Sales campaign: Daily performance in the last 7 days
  </div>
  <div style="position:relative; height:300px;">
    <canvas id="salesDailyChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// Daily Section 3: Sales Daily 혼합 차트
(function(){
  const ctx = document.getElementById('salesDailyChart');
  if(!ctx) return;
  const d = {SALES_DAILY_DATA}; // MCP 데이터 JSON 치환
  // d = { labels:[...], revenue:[...], ad_spend:[...], roas:[...] }
  new Chart(ctx, {
    data: {
      labels: d.labels,
      datasets: [
        {
          type: 'bar', label: 'Revenue', data: d.revenue,
          backgroundColor: '#94a3b8', yAxisID: 'y', order: 2
        },
        {
          type: 'bar', label: 'Ad Spend', data: d.ad_spend,
          backgroundColor: '#93c5fd', yAxisID: 'y', order: 3
        },
        {
          type: 'line', label: 'ROAS', data: d.roas,
          borderColor: '#ef4444', backgroundColor: 'transparent',
          pointBackgroundColor: '#ef4444', pointRadius: 4,
          tension: 0.3, yAxisID: 'y2', order: 1
        }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: {
        y:  { position: 'left',  beginAtZero: true,
              ticks: { callback: v => '$'+v.toLocaleString() } },
        y2: { position: 'right', beginAtZero: true,
              grid: { drawOnChartArea: false },
              ticks: { callback: v => v+'%' } }
      }
    }
  });
})();
```
