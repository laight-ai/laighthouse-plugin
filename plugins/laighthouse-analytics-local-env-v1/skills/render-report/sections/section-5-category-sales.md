# Section 5: 카테고리별 매출액 비교

**트리거 키워드:** `카테고리별 매출액`

## MCP 도구 호출: `get_naver_category_sales`

```json
{
  "brand_name": "...", "start_date": "당월초", "end_date": "target_date",
  "prev_start_date": "전월초", "prev_end_date": "전월말"
}
```
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`). mtd-section-2와 동일 호출 —
  카테고리별 합산과 전월 대비 `mom`(=`category_sales.growth`)까지 서버에서 이미 계산되어 있다.
- `items[].sales`가 당월(`curr`), `mom`이 곧 `growth`다. `prev`(전월 매출)이 별도로 필요하면
  `prev_sales = sales / (1 + mom/100)`처럼 역산하지 말고, mtd-section-2 호출을 그대로 재사용한다.
- mtd-section-2(상품별 누적 판매액)와 동일 호출을 재사용할 수 있다 (중복 호출 방지)

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
