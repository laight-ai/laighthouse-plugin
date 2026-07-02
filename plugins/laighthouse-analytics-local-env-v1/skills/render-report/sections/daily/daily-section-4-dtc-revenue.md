# Daily Section 4: Daily Revenue in DTC

**report_type:** `daily`
**MCP 도구:** `get_sales_performance_daily` (mtd_sales_daily, start_date=week_start, end_date=target_date)

## 필요 데이터
- `mtd_sales_daily.labels`: 날짜 레이블 배열 — 예: ["2026-03-26", ..., "2026-04-01"]
- `mtd_sales_daily.revenue`: DTC Revenue 배열 ($)

## HTML

```html
<!-- DAILY SECTION 4: Daily Revenue in DTC -->
<div style="background:white; border:1px solid #e2e8f0; padding:20px 24px; margin-bottom:16px;">
  <div style="font-size:15px; font-weight:700; color:#1e293b; margin-bottom:16px;">Daily Revenue in DTC</div>
  <div style="position:relative; height:260px;">
    <canvas id="dtcRevenueChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// Daily Section 4: DTC Revenue 라인 차트
(function(){
  const ctx = document.getElementById('dtcRevenueChart');
  if(!ctx) return;
  const d = {MTD_SALES_DAILY_DATA}; // MCP 데이터 JSON 치환
  // d = { labels:[...], revenue:[...] }
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: d.labels,
      datasets: [{
        label: 'Revenue',
        data: d.revenue,
        borderColor: '#60a5fa',
        backgroundColor: 'transparent',
        pointBackgroundColor: '#60a5fa',
        pointRadius: 3,
        tension: 0.3
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: {
        y: { beginAtZero: true, ticks: { callback: v => '$'+v.toLocaleString() } }
      }
    }
  });
})();
```
