# Breezm Executive MTD Section 4: 매출 추이 (Revenue Trend)

**report_type:** `executive-mtd` — **브리즘(airbridge 기반, type-b) 전용** (항상 포함). 최근 6개월(당월 포함)
라인 차트. 매출은 Airbridge 매출.

## MCP 도구 호출: `get_ad_performance_monthly_table` × 1

```json
{ "brand_name": "breezm", "start_month": "5개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "airbridge", "group_by": "media", "day_offset": "target_date.day" }
```

- 기간 span 6개월 (당월 포함, 고정). **`day_offset: target_date.day`를 반드시 넣는다**. ⚠️ `campaign-type` 금지.

## 필요 데이터 (월별 집계)

최근 6개월(당월 포함)을 **고정적으로 포함**한다 — 데이터가 없는 월도 labels에서 제외하지 않고
값을 0으로 채운다.

각 월에 대해:
- `광고 매출` = 광고 채널(`Google Ads`/`Meta Ads`/`Naver Ads`) 행의 `airbridge_revenue` 합
- `전체 매출` = **모든** `channel` 행의 `airbridge_revenue` 합 (광고 채널 외 채널 포함)
- airbridge 응답에 해당 월 행이 전혀 없으면 `광고 매출`/`전체 매출` 모두 **0**으로 기록한다.

## HTML

```html
<!-- BREEZM EXECUTIVE MTD SECTION 4: 매출 추이 (REVENUE TREND) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">매출 추이 (6개월)</div>
  <div style="display:flex; justify-content:center; flex-wrap:wrap; gap:20px; margin:16px 0 24px; font-size:12px; color:#334155;">
    <span style="display:flex; align-items:center; gap:6px;"><span style="width:16px; height:2px; background:#3b82f6; display:inline-block;"></span>전체 매출</span>
    <span style="display:flex; align-items:center; gap:6px;"><span style="width:16px; height:2px; background:#16a34a; display:inline-block;"></span>광고 매출</span>
  </div>
  <div style="position:relative; height:320px;">
    <canvas id="typeBRevenueTrendChart"></canvas>
  </div>
  <div style="font-size:12px; color:#64748b; margin-top:10px;">
    <div>{TYPE_B_REVENUE_TREND_FOOTNOTE_MTD}</div>
    <div>{TYPE_B_REVENUE_TREND_FOOTNOTE_DEFINITION}</div>
    <div>{TYPE_B_REVENUE_TREND_FOOTNOTE_ZERO_FILL}</div>
  </div>
</div>
```

## Script

```javascript
// Breezm Executive MTD Section 4: 매출 추이 라인 차트
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
      plugins:{
        legend:{ display:false },
        tooltip:{
          callbacks:{
            label: ctx => `${ctx.dataset.label}: ₩${Number(ctx.parsed.y).toLocaleString()}`
          }
        }
      },
      scales:{ y:{ ticks:{ callback: v => '₩' + Number(v).toLocaleString() } } }
    }
  });
})();
```

## 렌더링 규칙
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- **최근 6개월 고정 표시**: 데이터가 없는 월도 labels에서 제외하지 않고 값을 0으로 채워 항상
  6개월 전체를 표시한다 (데이터 적재가 늦게 시작된 브랜드에서 앞쪽 월들이 통째로 비는 경우 포함).
- 실제 `channel` 값이 광고 채널 상수와 다르면 조용히 0을 만들지 말고 차트 아래에 불일치를 명시한다.
- **커서를 올렸을 때 표시되는 tooltip에도** `₩` 접두어 + 천 단위 콤마를 붙인다 (위 Script의
  `plugins.tooltip.callbacks.label` 참고).
- 당월 레이블에 부분월임을 표기한다 (예: `26년 7월 (진행 중)`).
- **차트 아래 각주**: 세 개의 독립된 줄(`*`로 시작하는 문장 세 개)을 아래 **순서 그대로**
  표시한다 — 하나로 이어 붙이지 않는다.
  1. `{TYPE_B_REVENUE_TREND_FOOTNOTE_MTD}`: 항상 표시한다. 첫 번째 줄이다.
     `* 이번달({YY}년 {MM}월)의 데이터는 1일부터 기준일인 {MM}월 {DD}일까지의 수치입니다.` 형식
     (기준일은 실제 `target_date`로 채운다). "진행 중(MTD)" 같은 표현은 쓰지 않는다.
  2. `{TYPE_B_REVENUE_TREND_FOOTNOTE_DEFINITION}`: 항상 표시한다. 두 번째 줄이다. 다음 고정
     문구를 그대로 쓴다: `* '전체 매출'은 광고 매출과 자연 구매 매출을 합친 전체 매출을
     의미합니다.`
  3. `{TYPE_B_REVENUE_TREND_FOOTNOTE_ZERO_FILL}`: 값이 0으로 채워진 월이 있을 때만 작성한다.
     세 번째 줄이다. 아래 **고정 문구**를 그대로 쓴다 — 어떤 달인지, 어떤 사유인지 구체적으로
     나열하지 않는다: `* 매출 데이터가 정상적으로 연동되지 않은 경우, 제대로 표시되지 않을 수
     있습니다.` 0으로 채워진 월이 없으면 이 줄 자체를 생략한다(빈 문자열).