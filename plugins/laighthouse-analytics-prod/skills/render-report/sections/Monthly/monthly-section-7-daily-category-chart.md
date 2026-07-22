# Monthly Section 7: 일일 카테고리별 매출 현황

**report_type:** `monthly` (항상 포함).

mtd(MK)의 `mtd-section-6-daily-category-chart.md`와 **동일한 포맷/차트**(멀티라인)다. 유일한
차이는 날짜 범위다 — mtd는 월초부터 기준일(target_date)까지만 그리지만, monthly는 항상
**월초부터 월말까지 전체**를 그린다.

## MCP 도구 호출: `get_naver_item_sales_daily`

```json
{ "brand_name": "...", "start_date": "대상월 1일", "end_date": "대상월 말일" }
```

> ⚠️ **`group_by` 파라미터를 보내지 않는다.** enum 문자열 인자가 토크나이저 버그로 계속 숫자로
> 잘못 잘려 들어가는 문제 때문에 도구에서 `group_by`를 통째로 제거했다 — 서버가 항상
> `category_3rd` 기준으로 그룹핑해서 반환한다. `group_by` 키 자체를 요청 JSON에 넣지 않는다.
- naver 전용 MCP 도구 (`/v2/naver/item-sales/daily` 래퍼). `items[]`를
  `(logdate, product_category_3rd)`로 그룹핑해 `sum(sales_amount)`, 매출 상위 5개 카테고리만
  시리즈로 렌더링한다.
- monthly-section-6(카테고리별 월간 매출액 비교)와 **상위 카테고리 선정 기준을 통일**한다 —
  이 섹션의 5개 라인은 monthly-section-6에서 뽑은 "상위 5개 카테고리"와 동일한 카테고리로
  맞춘다 (두 섹션이 서로 다른 카테고리를 보여주면 보고서 읽는 사람이 혼란스러워짐).

## 필요 데이터 (MCP)
- `daily_sales.labels`: 날짜 배열 (예: ['2026-03-01', ..., '2026-03-31'])
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
<!-- MONTHLY SECTION 7: 일일 카테고리별 매출 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">일일 카테고리별 매출 현황</div>
  <div style="position:relative; height:300px;">
    <canvas id="monthlyDailyCategoryChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// Section 7: 일일 카테고리별 매출 멀티라인 차트 (월 전체)
(function(){
  const ctx = document.getElementById('monthlyDailyCategoryChart');
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

## 렌더링 규칙
- `canvas id`는 `monthlyDailyCategoryChart`로 한다 (mtd(MK)의 `dailyChart`와 id 중복 방지).
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체한다.
