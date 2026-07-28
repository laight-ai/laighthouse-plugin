# MTD-type-b Section 3: 매출 추이

**report_type:** `mtd` — **분기 B(type-b) 전용** (항상 포함). 최근 12개월(당월 포함)
라인 차트. 매출은 Airbridge 매출.

## MCP 도구 호출: `get_ad_performance_monthly_table` × 1

```json
{ "brand_name": "브리즘", "start_month": "11개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "airbridge", "group_by": "media" }
```

- 기간 span 12개월 (도구 제한 24개월 이내). ⚠️ `campaign-type` 금지.

## 필요 데이터 (월별 집계)

각 월에 대해:
- `광고 매출` = 광고 채널(`Google Ads`/`Meta Ads`/`Naver Ads`) 행의 `airbridge_revenue` 합
- `전체 매출` = **모든** `channel` 행의 `airbridge_revenue` 합 (광고 채널 외 채널 포함)

## HTML

```html
<!-- MTD-TYPE-B SECTION 3: 매출 추이 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">매출 추이 (최근 12개월)</div>
  <div style="position:relative; height:320px;">
    <canvas id="typeBRevenueTrendChart"></canvas>
  </div>
</div>
```

## Script

```javascript
// MTD-type-b Section 3: 매출 추이 라인 차트
(function(){
  const ctx = document.getElementById('typeBRevenueTrendChart');
  if(!ctx) return;
  const d = {TYPE_B_REVENUE_TREND_DATA}; // { labels:[...], ad_revenue:[...], total_revenue:[...] }
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: d.labels,
      datasets: [
        { label:'전체 매출', data:d.total_revenue,
          borderColor:'#3b82f6', backgroundColor:'transparent',
          pointBackgroundColor:'#3b82f6', tension:0.3 },
        { label:'광고 매출', data:d.ad_revenue,
          borderColor:'#16a34a', backgroundColor:'transparent',
          pointBackgroundColor:'#16a34a', tension:0.3 }
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
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- **빈 월 제외**: airbridge 응답에 행이 전혀 없는 월은 labels에서 **제외**하고, 차트 아래에
  "N월~M월은 데이터가 없어 차트에서 제외" 형태로 제외 월을 명시한다 (데이터 적재가 늦게 시작된
  브랜드에서 앞쪽 월들이 통째로 비는 경우). 남은 월이 1개뿐이면 라인 대신 포인트만 표시되는 것을
  허용한다.
- 실제 `channel` 값이 광고 채널 상수와 다르면 조용히 0을 만들지 말고 차트 아래에 불일치를 명시한다.
- 당월 레이블에 부분월임을 표기한다.
