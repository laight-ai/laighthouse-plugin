# Section 3: 월별 광고 성과 차트

**트리거 키워드:** `월별 광고 성과`

## 필요 데이터 (MCP)
최근 6개월 배열:
- `monthly_chart.labels`: 연월 레이블 배열 (예: ['25년 11월', ..., '26년 4월'])
- `monthly_chart.ad_cost`: 광고비 배열 (숫자, 원)
- `monthly_chart.revenue`: 매출 배열 (숫자, 원)
- `monthly_chart.roas`: ROAS 배열 (숫자, %)

## HTML

```html
<!-- SECTION 3: 월별 광고 성과 차트 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">월별 광고 성과</div>
  <div style="position:relative; height:320px;">
    <canvas id="monthlyChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// Section 3: 월별 광고 성과 혼합 차트
(function(){
  const ctx = document.getElementById('monthlyChart');
  if(!ctx) return;
  const d = {MONTHLY_CHART_DATA}; // MCP 데이터 JSON 치환
  // d = { labels:[...], ad_cost:[...], revenue:[...], roas:[...] }
  new Chart(ctx, {
    data: {
      labels: d.labels,
      datasets: [
        { type:'bar',  label:'광고비', data:d.ad_cost,  backgroundColor:'#93c5fd', yAxisID:'y' },
        { type:'bar',  label:'매출',   data:d.revenue,  backgroundColor:'#94a3b8', yAxisID:'y' },
        { type:'line', label:'ROAS',   data:d.roas,
          borderColor:'#ef4444', backgroundColor:'transparent',
          pointBackgroundColor:'#ef4444', tension:0.3, yAxisID:'y2' }
      ]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ position:'top' } },
      scales:{
        y:  { position:'left',  ticks:{ callback: v => fmtUSD(v) } },
        y2: { position:'right', grid:{ drawOnChartArea:false },
              ticks:{ callback: v => v+'%' } }
      }
    }
  });
})();
```
