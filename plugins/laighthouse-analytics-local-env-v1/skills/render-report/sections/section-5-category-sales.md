# Section 5: 카테고리별 매출액 비교

**트리거 키워드:** `카테고리별 매출액`

## MCP 도구 호출: ⚠️ 매칭되는 generic 도구 없음

카테고리 단위 매출 집계(2단계: 카테고리-1차/2차)는 laighthouse-prism에 `/v2/naver/item-sales`
(daily/monthly, `NaverItemDimension.CATEGORY_1ST`/`CATEGORY_2ND` group-by)로 이미 구현되어 있으나,
이 엔드포인트는 naver 전용 테이블(`nvss_item_perf`) 기반이라 **naver 전용 MCP 도구를 만들지 말라는
지침에 따라 MCP tool로 노출하지 않는다.** 현재 노출된 `get_sku_sales_daily`/`get_sku_sales_monthly`는
SKU(개별 상품) 단위이고 카테고리 롤업/할인율/환불율 필드가 없어 대체 불가.
→ 이 섹션은 데이터 소스가 확정되기 전까지 "데이터 준비 중" 카드로 대체한다.

## 필요 데이터 (MCP)
- `category_sales.labels`: 카테고리 배열 (예: ['국내분유','커피','단백질보충제','우유/요거트','두유','기타'])
- `category_sales.prev_label`: 전월 레이블 (예: '26년 3월')
- `category_sales.curr_label`: 당월 레이블 (예: '26년 4월')
- `category_sales.prev`: 전월 매출 배열 (USD)
- `category_sales.curr`: 당월 매출 배열 (USD)
- `category_sales.growth`: MoM 증감률 배열 (%, 소수 1자리)

## HTML

```html
<!-- SECTION 5: 카테고리별 매출액 비교 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">카테고리별 매출액 비교</div>
  <div style="position:relative; height:280px;">
    <canvas id="categoryChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// Section 5: 카테고리별 매출액 비교 차트
(function(){
  const ctx = document.getElementById('categoryChart');
  if(!ctx) return;
  const d = {CATEGORY_SALES_DATA}; // MCP 데이터 JSON 치환
  // d = { labels:[...], prev_label:'', curr_label:'', prev:[...], curr:[...], growth:[...] }

  const chart = new Chart(ctx, {
    type:'bar',
    data:{
      labels: d.labels,
      datasets:[
        { label: d.prev_label||'전월', data:d.prev, backgroundColor:'#60a5fa' },
        { label: d.curr_label||'당월', data:d.curr, backgroundColor:'#fb923c' }
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{ position:'top' },
        tooltip:{ callbacks:{ label: c => c.dataset.label+': '+fmtUSD(c.raw) } }
      },
      scales:{ y:{ ticks:{ callback: v => fmtUSD(v) } } }
    }
  });

  // 당월 막대 위에 증감률 텍스트 표시
  const growthPlugin = {
    id:'growthLabel',
    afterDatasetsDraw(ch){
      const c = ch.ctx;
      const meta = ch.getDatasetMeta(1);
      meta.data.forEach((bar, i)=>{
        const g = d.growth[i];
        if(g===undefined) return;
        c.save();
        c.fillStyle = g>=0 ? '#16a34a' : '#dc2626';
        c.font = 'bold 11px sans-serif';
        c.textAlign = 'center';
        c.fillText((g>=0?'+':'')+g+'%', bar.x, bar.y-6);
        c.restore();
      });
    }
  };
  Chart.register(growthPlugin);
  chart.update();
})();
```
