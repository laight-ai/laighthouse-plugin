# MTD-type-b Section 2: 월별 광고 성과

**report_type:** `mtd` — **분기 B(type-b) 전용** (항상 포함). 최근 6개월(당월 포함),
연-월 단위. 매출은 Airbridge 매출, 광고 채널은 `Google Ads`/`Meta Ads`/`Naver Ads` 행.

## MCP 도구 호출: `get_ad_performance_monthly_table` × 4

```json
{ "brand_name": "브리즘", "start_month": "5개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "google", "group_by": "total" }
{ "brand_name": "브리즘", "start_month": "5개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "meta", "group_by": "total" }
{ "brand_name": "브리즘", "start_month": "5개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "naver", "group_by": "total" }
{ "brand_name": "브리즘", "start_month": "5개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "airbridge", "group_by": "media" }
```

- 기간 span은 6개월 (도구 제한 24개월 이내). `day_offset`은 넣지 않는다 — 당월은 데이터가 있는
  날까지의 진행분이며, 차트에 당월이 부분월임을 표기한다.
- ⚠️ `campaign-type`을 넣지 않는다 — airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 문자열 enum 그대로 보낸다 (`"total"`/`"media"`).

## 필요 데이터 (월별 집계)

각 월에 대해:
- `광고비` = google/meta/naver 세 응답의 해당 월 `cost` 합
- `매출` = airbridge 응답의 해당 월 광고 채널(`Google Ads`/`Meta Ads`/`Naver Ads`) 행
  `airbridge_revenue` 합
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비 0이면 N/A)

## HTML

```html
<!-- MTD-TYPE-B SECTION 2: 월별 광고 성과 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">월별 광고 성과 (최근 6개월)</div>
  <div style="position:relative; height:320px;">
    <canvas id="typeBMonthlyChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// MTD-type-b Section 2: 월별 광고 성과 혼합 차트
(function(){
  const ctx = document.getElementById('typeBMonthlyChart');
  if(!ctx) return;
  const d = {TYPE_B_MONTHLY_CHART_DATA}; // { labels:[...], ad_cost:[...], revenue:[...], roas:[...] }
  new Chart(ctx, {
    data: {
      labels: d.labels,
      datasets: [
        { type:'bar',  label:'광고비', data:d.ad_cost,  backgroundColor:'#93c5fd', yAxisID:'y', order:2 },
        { type:'bar',  label:'매출',   data:d.revenue,  backgroundColor:'#94a3b8', yAxisID:'y', order:2 },
        { type:'line', label:'ROAS',   data:d.roas,
          borderColor:'#ef4444', backgroundColor:'transparent',
          pointBackgroundColor:'#ef4444', tension:0.3, yAxisID:'y2', order:1 }
      ]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ position:'top' } },
      scales:{
        y:  { position:'left',  ticks:{ callback: v => Number(v).toLocaleString() } },
        y2: { position:'right', grid:{ drawOnChartArea:false },
              ticks:{ callback: v => v+'%' } }
      }
    }
  });
})();
```

## 렌더링 규칙
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 첫 airbridge 응답에서 실제 `channel` 값들을 확인하고, 상수와 다르면 조용히 0을 만들지 말고
  차트 아래에 불일치를 명시한다.
- 당월 레이블에 부분월임을 표기한다 (예: "26년 7월 (진행 중)").
