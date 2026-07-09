# Section 3: 월별 광고 성과 차트

**트리거 키워드:** `월별 광고 성과`

## MCP 도구 호출: `get_ad_performance_monthly_table`

```json
{
  "brand_name": "...",
  "start_month": "5개월 전 YYYY-MM",
  "end_month": "당월 YYYY-MM",
  "group_by": "total",
  "media": null
}
```
- `group_by="total"` + `media` 미지정 → 브랜드 전체(google/meta/tiktok/naver 합산) 월별 1행씩, 6개월 범위면 6행 반환
- naver 브랜드도 이 generic 도구 하나로 커버됨 (media 필터에 `"naver"`가 이미 포함되어 있음 — 별도 naver 전용 도구를 만들지 않는다)
- 반환은 마크다운 표 문자열 — 파싱해 아래 배열로 재구성

## 필요 데이터 (MCP)
최근 6개월 배열 (위 응답의 month/cost/purchase_amount/roas 컬럼에서 매핑):
- `monthly_chart.labels`: 연월 레이블 배열 (예: ['25년 11월', ..., '26년 4월']) ← `month`
- `monthly_chart.ad_cost`: 광고비 배열 (숫자, 원) ← `cost`
- `monthly_chart.revenue`: 매출 배열 (숫자, 원) ← `purchase_amount`
- `monthly_chart.roas`: ROAS 배열 (숫자, %) ← `roas`

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
