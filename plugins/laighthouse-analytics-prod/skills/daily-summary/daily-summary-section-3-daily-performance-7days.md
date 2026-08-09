# Breezm Executive Daily Section 3: 최근 7일 성과 (Daily Performance, 7-Day)

**report_type:** `daily-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
기준일을 포함한 최근 7일 일자별 광고 성과. 매출은 Airbridge 매출, 광고 채널은
`Google Ads`/`Meta Ads`/`Naver Ads` 행.

## MCP 도구 호출: `get_ad_performance_daily_table` × 1 (section-4/5 공유)

```json
{ "brand_name": "breezm", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "media" }
```

- **`media` 파라미터를 생략한다** — 생략하면 이 도구는 google/meta/naver/airbridge(및
  이 보고서가 쓰지 않는 다른 매체, 예: `ga4`)를 **한 번의 호출로 전부** 반환한다. 예전에는
  매체별로 4번(`google`/`meta`/`naver` 각각 `group_by:"total"` + `airbridge`
  `group_by:"media"`) 나눠 불렀지만, 이제 이 호출 1개로 동일한 정보를 전부 얻는다:
  - `media`가 정확히 `"google"`/`"meta"`/`"naver"`인 행 — 매체당 날짜별로 **이미 합산된 한
    줄**이며, 이 행의 `cost`가 예전에 `group_by:"total"`로 받던 값과 동일하다.
  - `media`가 `"airbridge"`인 행 — 예전과 동일하게 날짜별·`channel`별로 여러 줄(Google
    Ads/Meta Ads/Naver Ads/Organic/그 외)이 온다.
  - `media`가 위 네 가지 외의 값(예: `ga4`)인 행은 이 섹션이 쓰지 않으므로 무시한다.
- **이 호출의 응답은 `daily-summary-section-4-daily-revenue-7days.md`(section-4)와
  `daily-summary-section-5-channel-performance.md`(section-5)가 그대로 재사용한다** — 세
  섹션이 각자 호출하지 않는다. section-4는 이 응답의 airbridge 행 전체를, section-5는 이
  응답의 마지막 이틀(target_date-1일, target_date)에 해당하는 행만 가져다 쓴다(section-5가
  필요로 하는 D-1~D0 범위는 이 섹션의 7일 범위 안에 완전히 포함된다).
- 기간은 **기준일(target_date)을 포함해 정확히 7일**(기준일-6일 ~ 기준일)이다. 도구 제한(31일
  이내)을 항상 만족한다.
- ⚠️ `campaign-type`을 넣지 않는다 — airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 문자열 enum 그대로 보낸다 (`"media"`).

## `list_promotions` — 별도 호출 없음, section-2의 공유 응답을 재사용

- 이 섹션은 `list_promotions`를 직접 호출하지 않는다 — `daily-summary-section-2-executive-summary.md`가
  3단계에서 1회 호출한 `list_promotions`(기준일 7일 전 ~ target_date) 응답을 그대로 재사용한다.
  이 섹션이 필요로 하는 범위(기준일 6일 전 ~ target_date)는 그 안에 완전히 포함되며, 범위
  밖(7일 전 하루치)에 걸리는 프로모션이 있어도 아래 인덱스 clamp 로직(`raw_end_idx < 0`이면
  제외)이 자동으로 걸러내므로 렌더링 결과는 별도 호출했을 때와 동일하다.

## 필요 데이터 (일자별 집계)

각 날짜(총 7일)에 대해:
- `광고비` = 공유 응답에서 `media`가 `google`/`meta`/`naver`인 세 행의 해당 날짜 `cost` 합
- `매출` = 공유 응답에서 `media`가 `airbridge`인 행 중 해당 날짜 광고 채널(`Google
  Ads`/`Meta Ads`/`Naver Ads`) 행의 `airbridge_revenue` 합
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비 0이면 N/A)
- 날짜 레이블은 `M/D(요일)` 형식으로 만든다 (예: `5/15(금)`).

## 프로모션 오버레이 (브래킷 방식)

차트 아래에 프로모션 시작~종료 구간을 가로 브래킷(┃───┃)으로 표시하고, 라벨을 붙인다
(mtd-detailed-section-4-daily-revenue.md와 동일한 방식 — 겹치는 프로모션은 별도 줄로 쌓고,
라벨은 잘라내지 않으며 차트 경계를 벗어나면 좌/우 정렬로 적응한다). **카테고리 축의
`getPixelForValue(i)`는 그 날짜 "칸의 중앙"을 반환하므로, 브래킷 좌우 끝을 각 날짜 영역의
실제 경계에 맞추려면 밴드 폭의 절반만큼 좌우로 보정해야 한다** — 아래 Script 참고.

### 데이터 가공 (이 단계만 예외적으로 허용 — 상위 "데이터 처리 원칙" 참고)

1. `list_promotions` 응답의 `items[]`(각 `date_begin`/`date_end`/`title`)를 받는다.
2. **`labels` 배열의 7일은 항상 연속된 달력 날짜**이므로, 인덱스는 "찾기"가 아니라 **날짜
   차이를 직접 계산**해서 구한다 — 애매하게 "해당하는 인덱스를 찾는다"고만 하면 정확한 날짜
   매칭 로직 없이 잘못 계산되는 문제가 생길 수 있다. 정확한 계산법:
   - `raw_start_idx = (date_begin − labels[0]의 날짜).일수차`
   - `raw_end_idx = (date_end − labels[0]의 날짜).일수차`
   - `start_idx = max(0, raw_start_idx)` — 프로모션이 `labels[0]`보다 먼저 시작했으면 0으로
     클램프한다(즉 `raw_start_idx`가 음수면 0).
   - `end_idx = min(6, raw_end_idx)` — 프로모션이 `labels[6]`보다 늦게 끝나면 6으로
     클램프한다(즉 `raw_end_idx`가 6보다 크면 6).
3. `labels` 범위와 전혀 겹치지 않는 프로모션은 제외한다 — 즉 `raw_end_idx < 0`이거나
   `raw_start_idx > 6`이면 이 프로모션 자체를 결과 배열에 넣지 않는다.
4. `range_label`은 `"{시작월}/{시작일}~{종료월}/{종료일}"` 형식으로 만든다 (같은 달이면 뒤쪽
   월은 생략 가능: `"5/9~5/11"`). **이 라벨은 클램핑 전의 원래 `date_begin`/`date_end`를
   그대로 쓴다** — 클램핑된 `start_idx`/`end_idx`에 대응하는 날짜로 바꿔 쓰지 않는다.
5. 겹치는 프로모션이 여러 개면 각각을 별도의 행(브래킷 줄)으로 쌓는다 — 하나로 합치지 않는다.
6. 위 1~5단계는 전부 기계적 날짜 매칭·클램핑이며 프로모션 존재 여부를 임의로 추정하지 않으므로
   상위 "데이터 처리 원칙"과 충돌하지 않는다.

### 응답 데이터 구조 (가공 후)

```json
{
  "daily_promotions_ranges": [
    { "title": "5월 가정의 달 세일", "start_idx": 0, "end_idx": 2, "range_label": "5/9~5/11" }
  ]
}
```
(`start_idx`/`end_idx`는 `labels` 배열의 인덱스. 프로모션이 없으면 빈 배열 `[]`.)

## HTML

```html
<!-- BREEZM EXECUTIVE DAILY SECTION 3: 최근 7일 성과 (DAILY PERFORMANCE 7-DAY) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">최근 7일 성과</div>
  <div style="display:flex; justify-content:center; flex-wrap:wrap; gap:20px; margin-bottom:16px; font-size:12px; color:#334155;">
    <span style="display:flex; align-items:center; gap:6px;"><span style="width:12px; height:12px; background:#93c5fd; display:inline-block; border-radius:2px;"></span>광고비</span>
    <span style="display:flex; align-items:center; gap:6px;"><span style="width:12px; height:12px; background:#94a3b8; display:inline-block; border-radius:2px;"></span>매출</span>
    <span style="display:flex; align-items:center; gap:6px;"><span style="width:16px; height:2px; background:#ef4444; display:inline-block;"></span>ROAS</span>
  </div>
  <div style="position:relative; height:320px;">
    <canvas id="daily7dayChart"></canvas>
  </div>
  <!-- 프로모션 브래킷 오버레이 — daily_promotions_ranges가 빈 배열이면 이 div 자체를 렌더링하지 않는다. -->
  <div id="daily7dayPromoWrap" style="position:relative; margin-top:4px;"></div>
</div>
```

## Script

```javascript
// Breezm Executive Daily Section 3: 최근 7일 성과 혼합 차트
(function(){
  const ctx = document.getElementById('daily7dayChart');
  if(!ctx) return;
  const d = {DAILY_7DAY_CHART_DATA}; // { labels:[...], ad_cost:[...], revenue:[...], roas:[...] }
  const promos = {DAILY_7DAY_PROMOTIONS_RANGES_DATA}; // [{title, start_idx, end_idx, range_label}, ...] — 없으면 []

  const chart = new Chart(ctx, {
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

  // 프로모션 브래킷 오버레이 렌더링
  const wrap = document.getElementById('daily7dayPromoWrap');
  if (wrap && promos && promos.length) {
    const rowHeight = 40;
    wrap.style.height = (rowHeight * promos.length) + 'px';
    const xScale = chart.scales.x;
    const chartWidth = xScale.right - xScale.left;
    const n = d.labels.length;
    // 카테고리 축의 getPixelForValue(i)는 "그 날짜 칸의 중앙"을 반환한다 — 브래킷을 날짜
    // 영역 좌우 끝에 맞추려면 밴드 폭의 절반만큼 좌/우로 보정해야 한다.
    const bandWidth = chartWidth / n;
    const leftEdge = i => xScale.getPixelForValue(i) - bandWidth / 2;
    const rightEdge = i => xScale.getPixelForValue(i) + bandWidth / 2;

    promos.forEach((p, row) => {
      const xStart = leftEdge(p.start_idx);
      const xEnd = rightEdge(p.end_idx);
      const width = Math.max(xEnd - xStart, 2);
      const top = row * rowHeight;
      const centerX = xStart + width / 2;

      const bar = document.createElement('div');
      bar.style.cssText = `position:absolute; top:${top+6}px; left:${xStart}px; width:${width}px; height:6px; border-top:1px solid #94a3b8; border-left:1px solid #94a3b8; border-right:1px solid #94a3b8;`;
      wrap.appendChild(bar);

      // 라벨: 절대 잘라내지 않는다. 우선 중앙 정렬 위치를 계산해보고, 차트 좌/우 경계를
      // 벗어나면 브래킷의 왼쪽/오른쪽 끝에 맞춰 정렬을 바꾼다.
      const label = document.createElement('div');
      label.textContent = p.title + ' (' + p.range_label + ')';
      label.style.cssText = `position:absolute; top:${top+14}px; white-space:nowrap; font-size:11px; color:#64748b;`;
      wrap.appendChild(label);

      const labelWidth = label.offsetWidth;
      const centeredLeft = centerX - labelWidth / 2;
      if (centeredLeft < 0) {
        label.style.left = xStart + 'px';
      } else if (centeredLeft + labelWidth > chartWidth) {
        label.style.left = (xEnd - labelWidth) + 'px';
      } else {
        label.style.left = centeredLeft + 'px';
      }
    });
  }
})();
```

## 렌더링 규칙
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 7일 전부 표시한다 (건너뛰거나 제외하지 않는다). 매출이 0원인 날이 있어도 그대로 0으로
  그린다 (추정/보간 금지).
- Legend는 Chart.js 기본 legend를 쓰지 않고, 위 HTML의 커스텀 legend를 쓴다 — **광고비/매출은
  박스, ROAS는 라인 마커**이며 순서는 광고비 → 매출 → ROAS로 고정한다 (ROAS를 박스로 그리지
  않는다 — mtd-detailed-section-3에서 정립한 관례와 동일).
- Y축(₩) 눈금은 원 단위 숫자에 `₩` 접두어 + 천 단위 콤마로 표시한다 (만원/억원 등 축약 단위
  금지).
- **ROAS 축(우측, y2)은 항상 0%부터 시작한다**(`min:0`) — 최고점(`max`)은 지정하지 않아
  데이터 실황에 따라 자동으로 조정된다. `min`을 지정하지 않으면 Chart.js가 데이터 범위에
  맞춰 자동으로 축을 잡는데, ROAS 값이 전부 100% 이상인 경우 축이 100%쯤부터 시작해서
  선이 잘려 보이는 것처럼 보이는 문제가 생길 수 있다.
- **커서를 올렸을 때 표시되는 tooltip에도** 광고비/매출은 `₩` 접두어 + 천 단위 콤마, ROAS는
  `%` 접미사를 붙인다 (위 Script의 `plugins.tooltip.callbacks.label` 참고).
- 첫 airbridge 응답에서 실제 `channel` 값들을 확인하고, 상수와 다르면 조용히 0을 만들지 말고
  차트 아래에 불일치를 명시한다.
- `daily_promotions_ranges`가 빈 배열이면 프로모션 오버레이 영역(`daily7dayPromoWrap`) 자체를
  렌더링하지 않는다 — 빈 여백만 남기지 않는다.
- 브래킷 좌우 끝은 **날짜 영역(밴드) 전체**에 맞춘다 — 카테고리 중심점이 아니라 밴드 폭의
  절반만큼 보정한 좌우 경계를 쓴다 (위 Script의 `leftEdge`/`rightEdge` 참고).
- 프로모션이 여러 개(겹치거나 인접) 있으면 위에서부터 순서대로 세로로 쌓아 그린다(행간격 40px).
- 라벨은 절대 잘라내지 않는다 — 중앙 정렬이 차트 좌/우 경계를 벗어나면 브래킷 왼쪽 끝/오른쪽
  끝 기준으로 자동 전환한다 (라벨이 브래킷 자체 범위를 벗어나는 것은 허용).