# Section 6: 일일 카테고리별 매출 현황

**트리거 키워드:** `일일 카테고리별`

## MCP 도구 호출: ⚠️ 매칭되는 generic 도구 없음 (section-5와 동일한 갭)

일별 카테고리별 매출 시계열도 section-5와 같은 이유로 매칭되는 generic MCP 도구가 없다
(`/v2/naver/item-sales/daily`는 naver 전용 endpoint라 MCP tool로 노출하지 않음).
→ "데이터 준비 중" 카드로 대체한다.

## 필요 데이터 (MCP)
- `daily_sales.labels`: 날짜 배열 (예: ['2026-04-01', ..., '2026-04-30'])
- `daily_sales.series`: 카테고리별 시계열 배열
  ```json
  [
    { "label": "국내분유", "color": "#3b82f6", "data": [숫자, ...] },
    { "label": "커피",     "color": "#ef4444", "data": [숫자, ...] },
    { "label": "단백질보충제", "color": "#22c55e", "data": [숫자, ...] },
    { "label": "우유/요거트", "color": "#eab308", "data": [숫자, ...] },
    { "label": "두유",     "color": "#a855f7", "data": [숫자, ...] }
  ]
  ```

## HTML

```html
<!-- SECTION 6: 일일 카테고리별 매출 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">일일 카테고리별 매출 현황</div>
  <div style="position:relative; height:300px;">
    <canvas id="dailyChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// Section 6: 일일 카테고리별 매출 멀티라인 차트
(function(){
  const ctx = document.getElementById('dailyChart');
  if(!ctx) return;
  const d = {DAILY_SALES_DATA}; // MCP 데이터 JSON 치환
  new Chart(ctx, {
    type:'line',
    data:{
      labels: d.labels,
      datasets: d.series.map(s=>({
        label: s.label, data: s.data,
        borderColor: s.color, backgroundColor:'transparent',
        pointRadius:2, tension:0.3
      }))
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{ position:'top' },
        tooltip:{
          mode:'index', intersect:false,
          callbacks:{ label: c => c.dataset.label+': '+fmtUSD(c.raw) }
        }
      },
      scales:{ y:{ ticks:{ callback: v => fmtUSD(v) } } }
    }
  });
})();
```
