# MTD Section 7: 일일 카테고리별 매출 현황

**report_type:** `mtd` (항상 포함).

## MCP 도구 호출: `get_naver_item_sales_daily`

```json
{ "brand_name": "...", "group_by": "category_3rd", "start_date": "당월초", "end_date": "target_date" }
```
> ⚠️ **`group_by`는 문자열 enum이다 — `"category_3rd"`를 글자 그대로, 언더스코어로 보낸다 (하이픈
> `category-3rd` 아님).** 허용값은 `"product"` / `"category_1st"` / `"category_2nd"` /
> `"category_3rd"` / `"category_4th"` 다섯 개뿐이다. `"3rd"`의 서수를 숫자로 바꾸거나 `-3` 같은 정수로
> 변환해서 보내면 잘못된 호출이다 (실제로 반복 재현된 오류 — 절대 숫자로 바꾸지 않는다).
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`, `/v2/naver/item-sales/daily` 래퍼)
- mtd-section-6와 동일 호출 결과를 재사용 — `items[]`를 `(logdate, product_category_3rd)`로
  그룹핑해 `sum(sales_amount)`, 매출 상위 5개 카테고리만 시리즈로 렌더링

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
<!-- SECTION 7: 일일 카테고리별 매출 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">일일 카테고리별 매출 현황</div>
  <div style="position:relative; height:300px;">
    <canvas id="dailyChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// Section 7: 일일 카테고리별 매출 멀티라인 차트
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
          callbacks:{ label: c => c.dataset.label+': '+Number(c.raw).toLocaleString() }
        }
      },
      scales:{ y:{ ticks:{ callback: v => Number(v).toLocaleString() } } }
    }
  });
})();
```
