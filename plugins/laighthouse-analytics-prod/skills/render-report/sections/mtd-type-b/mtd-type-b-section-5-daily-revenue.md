# MTD-type-b Section 5: 일일 매출 현황

**report_type:** `mtd` — **분기 B(type-b) 전용** (항상 포함). 월초~target_date 일별
광고 매출 vs 전체 매출. 매출은 Airbridge 매출.

## MCP 도구 호출: `get_ad_performance_daily_table` × 1

```json
{ "brand_name": "브리즘", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "airbridge", "group_by": "media" }
```

- MTD 범위이므로 도구 제한(31일 이내)을 항상 만족한다. ⚠️ `campaign-type` 금지.

## 필요 데이터 (일별 집계)

각 일자에 대해:
- `광고 매출` = 광고 채널(`Google Ads`/`Meta Ads`/`Naver Ads`) 행의 `airbridge_revenue` 합
- `전체 매출` = 모든 `channel` 행의 `airbridge_revenue` 합

## HTML

```html
<!-- MTD-TYPE-B SECTION 5: 일일 매출 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">일일 매출 현황 (MTD)</div>
  <div style="position:relative; height:320px;">
    <canvas id="typeBDailyRevenueChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// MTD-type-b Section 5: 일일 매출 혼합 차트
(function(){
  const ctx = document.getElementById('typeBDailyRevenueChart');
  if(!ctx) return;
  const d = {TYPE_B_DAILY_REVENUE_DATA}; // { labels:[...], ad_revenue:[...], total_revenue:[...] }
  new Chart(ctx, {
    data: {
      labels: d.labels,
      datasets: [
        { type:'bar',  label:'전체 매출', data:d.total_revenue, backgroundColor:'#93c5fd', order:2 },
        { type:'line', label:'광고 매출', data:d.ad_revenue,
          borderColor:'#16a34a', backgroundColor:'transparent',
          pointBackgroundColor:'#16a34a', tension:0.3, order:1 }
      ]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ position:'top' } },
      scales:{ y:{ ticks:{ callback: v => Number(v).toLocaleString() } } }
    }
  });
})();
```

## 렌더링 규칙
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다 — 중간에 매출 0원인
  날이 있어도 그대로 0으로 그린다 (추정/보간 금지).
- 실제 `channel` 값이 상수와 다르면 조용히 0을 만들지 말고 차트 아래에 불일치를 명시한다.
