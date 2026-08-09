# Breezm Executive MTD Section 3: 월별 광고 성과 (Monthly Ad Performance)

**report_type:** `mtd-summary` — **브리즘(airbridge 기반) 전용** (항상 포함). 최근
6개월(당월 포함), 연-월 단위. 매출은 Airbridge 매출, 광고 채널은
`Google Ads`/`Meta Ads`/`Naver Ads` 행.

## MCP 도구 호출: `get_ad_performance_monthly_table` × 1 (`media` 생략, section-4/5 공유)

```json
{ "brand_name": "breezm", "start_month": "5개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "group_by": "media", "day_offset": "target_date.day" }
```

- **`media` 파라미터를 생략한다** — 생략하면 이 도구는 google/meta/naver/airbridge(및 이
  보고서가 쓰지 않는 다른 매체, 예: `ga4`)를 **한 번의 호출로 전부** 반환한다. 예전에는
  매체별로 4번(`google`/`meta`/`naver` 각각 `group_by:"total"` + `airbridge`
  `group_by:"media"`) 나눠 불렀지만, 이제 이 호출 1개로 동일한 정보를 전부 얻는다:
  - `media`가 정확히 `"google"`/`"meta"`/`"naver"`인 행 — 매체당 월별로 **이미 합산된 한
    줄**이며, 이 행의 `cost`가 예전에 `group_by:"total"`로 받던 값과 동일하다.
  - `media`가 `"airbridge"`인 행 — 예전과 동일하게 월별·`channel`별로 여러 줄(Google
    Ads/Meta Ads/Naver Ads/Organic/그 외)이 온다.
  - `media`가 위 네 가지 외의 값(예: `ga4`)인 행은 이 섹션이 쓰지 않으므로 무시한다.
- **이 호출의 응답은 `mtd-summary-section-4-revenue-trend.md`(section-4)와
  `mtd-summary-section-5-channel-comparison.md`(section-5)가 그대로 재사용한다** — 세
  섹션이 각자 호출하지 않는다. section-4는 이 응답을 6개월 그대로, section-5는 이 응답의
  마지막 2개월(전월, 당월)에 해당하는 행만 가져다 쓴다(section-5가 필요로 하는 전월~당월
  범위는 이 섹션의 6개월 범위 안에 완전히 포함된다).
- 기간 span은 6개월 (도구 제한 24개월 이내). **`day_offset: target_date.day`를 반드시 넣는다** —
  당월(진행 중인 달)은 이 값이 없으면 target_date가 아니라 실제 오늘 날짜까지 누적된 데이터를
  반환해, 섹션 1(목표 달성 현황)의 target_date 기준 수치와 어긋나는 문제가 생길 수 있다. `day_offset`
  을 넣으면 당월 데이터가 다른 섹션과 동일하게 target_date까지만 잘려서 온다.
- ⚠️ `campaign-type`을 넣지 않는다 — airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 문자열 enum 그대로 보낸다 (`"media"`).

## 필요 데이터 (월별 집계)

각 월에 대해:
- `광고비` = 공유 응답에서 `media`가 `google`/`meta`/`naver`인 세 행의 해당 월 `cost` 합
- `매출` = 공유 응답에서 `media`가 `airbridge`인 행 중 해당 월 광고 채널(`Google
  Ads`/`Meta Ads`/`Naver Ads`) 행의 `airbridge_revenue` 합
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비 0이면 N/A)

## HTML

```html
<!-- BREEZM EXECUTIVE MTD SECTION 3: 월별 광고 성과 (MONTHLY AD PERFORMANCE) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">월별 광고 성과 (최근 6개월)</div>
  <div style="display:flex; justify-content:center; flex-wrap:wrap; gap:20px; margin-bottom:16px; font-size:12px; color:#334155;">
    <span style="display:flex; align-items:center; gap:6px;"><span style="width:12px; height:12px; background:#93c5fd; display:inline-block; border-radius:2px;"></span>광고비</span>
    <span style="display:flex; align-items:center; gap:6px;"><span style="width:12px; height:12px; background:#94a3b8; display:inline-block; border-radius:2px;"></span>매출</span>
    <span style="display:flex; align-items:center; gap:6px;"><span style="width:16px; height:2px; background:#ef4444; display:inline-block;"></span>ROAS</span>
  </div>
  <div style="position:relative; height:320px;">
    <canvas id="typeBMonthlyChart"></canvas>
  </div>
  <div style="font-size:12px; color:#64748b; margin-top:10px;">
    <div>{TYPE_B_MONTHLY_CHART_FOOTNOTE_CURRENT_MONTH}</div>
    <div>{TYPE_B_MONTHLY_CHART_FOOTNOTE_ZERO_FILL}</div>
  </div>
</div>
```

## Script

```javascript
// Breezm Executive MTD Section 3: 월별 광고 성과 혼합 차트
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
      plugins:{
        legend:{ display:false },
        tooltip:{
          callbacks:{
            label: ctx => {
              const v = ctx.parsed.y;
              return ctx.dataset.label === 'ROAS'
                ? `ROAS: ${Number(v).toLocaleString()}%`
                : `${ctx.dataset.label}: ₩${Number(v).toLocaleString()}`;
            }
          }
        }
      },
      scales:{
        y:  { position:'left',  ticks:{ callback: v => '₩' + Number(v).toLocaleString() } },
        y2: { position:'right', grid:{ drawOnChartArea:false }, min:0,
              ticks:{ callback: v => v+'%' } }
      }
    }
  });
})();
```

## 렌더링 규칙
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- **최근 6개월 고정 표시**: 기간 내 어떤 응답에도 행이 없는 월(광고비·매출 모두 없음)도
  labels에서 제외하지 않고 값을 0으로 채워 항상 6개월 전체를 표시한다 (데이터 적재가 늦게
  시작된 브랜드에서 앞쪽 월들이 통째로 비는 경우 포함). 광고비만 있고 airbridge 매출이 없는
  월은 매출/ROAS만 0으로 두고 광고비 막대는 실제 값으로 그린다.
- 첫 airbridge 응답에서 실제 `channel` 값들을 확인하고, 상수와 다르면 조용히 0을 만들지 말고
  차트 아래에 불일치를 명시한다.
- 당월 레이블에 부분월임을 표기한다 (예: "26년 7월 (진행 중)").
- Y축 눈금은 원래 숫자(천 단위 콤마)에 `₩` 접두어만 붙인다 (예: `₩64,845,000`). 억/천만원 같은
  축약 단위로 바꾸지 않는다.
- **ROAS 축(우측, y2)은 항상 0%부터 시작한다**(`min:0`) — 최고점(`max`)은 지정하지
  않아 데이터 실황에 따라 자동으로 조정된다. `min`을 지정하지 않으면 ROAS 값이 전부
  100% 이상인 경우 축이 100%쯤부터 시작해서 선이 잘려 보이는 것처럼 보이는 문제가 생길 수 있다.
- **커서를 올렸을 때 표시되는 tooltip에도** 광고비/매출은 `₩` 접두어 + 천 단위 콤마, ROAS는
  `%` 접미사를 붙인다 (위 Script의 `plugins.tooltip.callbacks.label` 참고).
- **차트 아래 각주는 두 개의 독립된 줄**로 표시한다:
  - `{TYPE_B_MONTHLY_CHART_FOOTNOTE_CURRENT_MONTH}`: 항상 표시한다.
    `* 이번달({YY}년 {MM}월)의 데이터는 1일부터 기준일인 {MM}월 {DD}일까지의 수치입니다.` 형식
    (연/월/기준일은 실제 target_date로 채운다).
  - `{TYPE_B_MONTHLY_CHART_FOOTNOTE_ZERO_FILL}`: 광고비 또는 매출이 0으로 채워진 월이 있을
    때만 작성한다. 아래 **고정 문구**를 그대로 쓴다 — 어떤 달인지 구체적으로 나열하지 않는다:
    `* 광고비 또는 매출 데이터가 정상적으로 연동되지 않은 경우, 제대로 표시되지 않을 수 있습니다.`
    0으로 채워진 월이 없으면 이 줄 자체를 생략한다(빈 문자열).