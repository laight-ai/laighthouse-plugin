# Breezm MTD Section 4: 일일 매출 현황 (Daily Revenue)

**report_type:** `mtd` — **브리즘(airbridge 기반, type-b) 전용** (항상 포함). 월초~target_date
일별 광고 매출 vs 전체 매출. 매출은 Airbridge 매출.

## MCP 도구 호출: `get_ad_performance_daily_table` × 1

```json
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "airbridge", "group_by": "media" }
```

- MTD 범위이므로 도구 제한(31일 이내)을 항상 만족한다. ⚠️ `campaign-type` 금지.

## MCP 도구 호출: `list_promotions`

```json
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date" }
```
- 위 `get_ad_performance_daily_table`과 정확히 같은 날짜 범위로 1회만 추가 호출한다.

## 필요 데이터 (일별 집계)

각 일자에 대해:
- `광고 매출` = 광고 채널(`Google Ads`/`Meta Ads`/`Naver Ads`) 행의 `airbridge_revenue` 합
- `전체 매출` = 모든 `channel` 행의 `airbridge_revenue` 합

`{TYPE_B_DAILY_REVENUE_DATA}.labels`의 각 원소는 문자열이 아니라 **`[날짜, 요일]` 2개짜리
배열**이어야 한다 (Chart.js가 배열 라벨을 두 줄로 렌더링하는 것을 이용해 날짜 아래에 요일을
표시한다). 날짜는 `M/D` 형식(예: `7/1`), 요일은 `(요일)` 형식(예: `(수)`)이다. 월초부터
기준일까지 **하루도 건너뛰지 않고 전부** 포함한다(격일 표기 금지).

## 프로모션 오버레이

차트 아래에 프로모션 시작~종료 구간을 가로 브래킷(┃───┃)으로 표시하고 중앙에
"{프로모션명} ({시작}~{종료})" 라벨을 붙인다.

### 데이터 가공 (이 단계만 예외적으로 허용 — 상위 "데이터 처리 원칙" 참고)

1. `list_promotions` 응답의 `items[]`(각 `date_begin`/`date_end`/`title`)를 받는다.
2. 각 프로모션에 대해, `labels` 배열에서 `date_begin`/`date_end`에 해당하는 인덱스를 찾는다.
   `date_begin`이 `labels[0]`보다 이르면 `start_idx=0`으로 clamp, `date_end`가 `labels[last]`보다
   늦으면 `end_idx=labels.length-1`로 clamp한다 (차트 범위 밖으로 삐져나온 구간은 보이는 부분만
   표시).
3. `date_begin`/`date_end`가 `labels`의 범위와 전혀 겹치지 않는(완전히 범위 밖) 프로모션은
   제외한다.
4. `range_label`은 `"{date_begin의 월}월 {date_begin의 일}일~{date_end의 일}일"` 형식으로 만든다
   (같은 달이면 월을 한 번만 표시. 월이 걸치면 "{시작월}월 {시작일}일~{종료월}월 {종료일}일"로
   둘 다 표시).
5. 겹치는 프로모션이 여러 개면 각각을 별도의 행(브래킷 줄)으로 쌓는다 — 하나로 합치지 않는다.
6. 위 1~5단계는 전부 기계적 날짜 매칭·클램핑이며 프로모션 존재 여부를 임의로 추정하지 않으므로
   상위 "데이터 처리 원칙"과 충돌하지 않는다.

### 응답 데이터 구조 (가공 후)

```json
{
  "daily_promotions_ranges": [
    { "title": "5월 가정의달 세일", "start_idx": 0, "end_idx": 10, "range_label": "5월 1일~11일" }
  ]
}
```
(`start_idx`/`end_idx`는 `labels` 배열의 인덱스. 프로모션이 없으면 빈 배열 `[]`.)

## HTML

```html
<!-- BREEZM MTD SECTION 4: 일일 매출 현황 (DAILY REVENUE) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">일일 매출 현황 ({MM}월 1일~{MM}월 {DD}일)</div>
  <div style="display:flex; justify-content:center; flex-wrap:wrap; gap:20px; margin-bottom:16px; font-size:12px; color:#334155;">
    <span style="display:flex; align-items:center; gap:6px;"><span style="width:16px; height:2px; background:#3b82f6; display:inline-block;"></span>전체 매출</span>
    <span style="display:flex; align-items:center; gap:6px;"><span style="width:16px; height:2px; background:#16a34a; display:inline-block;"></span>광고 매출</span>
  </div>
  <div style="position:relative; height:320px;">
    <canvas id="typeBDailyRevenueChart"></canvas>
  </div>
  <!-- 프로모션 브래킷 오버레이 — daily_promotions_ranges가 빈 배열이면 이 div 자체를 렌더링하지 않는다.
       캔버스와 정확히 같은 폭의 형제 요소로 둔다 — margin/offset을 주지 않아야 xScale.getPixelForValue() 좌표와 그대로 맞는다. -->
  <div id="typeBDailyRevenuePromoWrap" style="position:relative; margin-top:4px;"></div>
  <p style="font-size:11px; color:#64748b; margin-top:8px;">* '전체 매출'은 오거닉 매출과 광고 매출을 합친 전체 매출을 의미합니다.</p>
</div>
```

## Script

```javascript
// Breezm MTD Section 4: 일일 매출 라인 차트
(function(){
  const ctx = document.getElementById('typeBDailyRevenueChart');
  if(!ctx) return;
  const d = {TYPE_B_DAILY_REVENUE_DATA}; // { labels:[[날짜,요일], ...], ad_revenue:[...], total_revenue:[...] }
  const promos = {TYPE_B_DAILY_PROMOTIONS_RANGES_DATA}; // [{title, start_idx, end_idx, range_label}, ...] — 없으면 []
  const chart = new Chart(ctx, {
    data: {
      labels: d.labels,
      datasets: [
        { type:'line', label:'전체 매출', data:d.total_revenue,
          borderColor:'#3b82f6', backgroundColor:'transparent',
          pointBackgroundColor:'#3b82f6', tension:0.3, order:2 },
        { type:'line', label:'광고 매출', data:d.ad_revenue,
          borderColor:'#16a34a', backgroundColor:'transparent',
          pointBackgroundColor:'#16a34a', tension:0.3, order:1 }
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
      scales:{
        x: { ticks: { maxRotation: 0, minRotation: 0, autoSkip: false } },
        y: { ticks: { stepSize: 5000000, callback: v => '₩' + Number(v).toLocaleString() } }
      }
    }
  });

  // 프로모션 브래킷 오버레이 렌더링
  // 주의: typeBDailyRevenuePromoWrap은 캔버스와 폭이 정확히 같은 형제 요소여야 한다 — 그래야
  // xScale.getPixelForValue()가 반환하는 "캔버스 기준 픽셀 위치"를 그대로(보정 없이) 써도
  // 이 wrap div 안에서 같은 x좌표를 가리킨다. margin-left 등으로 wrap을 들여쓰면 좌표가 틀어진다.
  const wrap = document.getElementById('typeBDailyRevenuePromoWrap');
  if (wrap && promos && promos.length) {
    const rowHeight = 40;
    wrap.style.height = (rowHeight * promos.length) + 'px';
    const xScale = chart.scales.x;
    const chartWidth = xScale.right - xScale.left;

    promos.forEach((p, row) => {
      const xStart = xScale.getPixelForValue(p.start_idx);
      const xEnd = xScale.getPixelForValue(p.end_idx);
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
        // 브래킷이 왼쪽에 붙은 경우 — 브래킷 왼쪽 끝부터 출력
        label.style.left = xStart + 'px';
      } else if (centeredLeft + labelWidth > chartWidth) {
        // 브래킷이 오른쪽에 붙은 경우 — 브래킷 오른쪽 끝에서 끝나도록 출력
        label.style.left = (xEnd - labelWidth) + 'px';
      } else {
        // 충분히 여유 있는 경우 — 브래킷 중앙 정렬
        label.style.left = centeredLeft + 'px';
      }
    });
  }
})();
```

## 렌더링 규칙
- 카드 제목의 `{MM}`/`{DD}`는 데이터 기간에 맞춰 채운다 — 둘 다 `target_date` 기준이며, 시작은
  항상 당월 1일이므로 `{MM}월 1일~{MM}월 {DD}일` 형식에서 두 `{MM}`은 같은 값(당월)이고 `{DD}`는
  `target_date`의 일(day)이다 (예: 기준일이 7월 15일이면 "7월 1일~7월 15일").
- 차트 아래 "'전체 매출'은 오거닉 매출과 광고 매출을 합친 전체 매출을 의미합니다." 각주는
  **항상** 표시한다 (조건부 아님).
- 전체 매출/광고 매출 모두 **라인**으로 그린다 (막대 아님). Legend는 Chart.js 기본 legend를 쓰지
  않고, 위 HTML의 커스텀 라인 legend(두 항목 모두 짧은 선 마커)를 쓴다.
- X축은 월초~기준일 **하루도 건너뛰지 않고 전부** 표시한다(`autoSkip: false`). 각 눈금은 위쪽에
  날짜(`M/D`), 아래쪽에 요일(`(요일)`)을 두 줄로 중앙 정렬 표시한다(`labels`를 `[날짜, 요일]`
  배열로 준다 — 위 "필요 데이터" 참고).
- Y축 눈금은 **500만원(5,000,000원) 단위**로 고정한다(`stepSize: 5000000`)이며, 값은 원 단위
  숫자에 `₩` 접두어와 천 단위 콤마를 붙여 표시한다 (예: `₩15,000,000`) — 만원/억원 등 축약
  단위로 바꾸지 않는다.
- **커서를 올렸을 때 표시되는 tooltip에도** `₩` 접두어 + 천 단위 콤마를 붙인다 (위 Script의
  `plugins.tooltip.callbacks.label` 참고).
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다 — 중간에 매출 0원인
  날이 있어도 그대로 0으로 그린다 (추정/보간 금지).
- 실제 `channel` 값이 상수와 다르면 조용히 0을 만들지 말고 차트 아래에 불일치를 명시한다.
- `daily_promotions_ranges`가 빈 배열이면 프로모션 오버레이 영역(`typeBDailyRevenuePromoWrap`)
  자체를 렌더링하지 않는다 — 빈 여백만 남기지 않는다.
- 브래킷은 `┃───┃` 모양(양쪽에 짧은 세로 눈금 + 가로선)으로 그린다. 위 스크립트는 `border-left`/
  `border-right`로 세로 눈금을, `border-top`으로 가로선을 표현한다.
- 프로모션이 여러 개(겹치거나 인접) 있으면 위에서부터 순서대로 세로로 쌓아 그린다 (row 0, 1,
  2..., 행간격 40px).
- **브래킷 라벨은 절대 잘라내지 않는다**(`text-overflow:ellipsis` 금지, 전체 텍스트 항상 표시).
  대신 위치를 적응형으로 정렬한다: 중앙 정렬 시 차트 왼쪽 경계를 벗어나면 브래킷 왼쪽 끝부터,
  오른쪽 경계를 벗어나면 브래킷 오른쪽 끝에서 끝나도록, 그 외(여유가 충분한 경우)에는 브래킷
  중앙 정렬로 표시한다 — 라벨이 브래킷 자체의 좌우 범위를 벗어나는 것은 허용한다.
- ⚠️ **좌표계 주의**: `typeBDailyRevenuePromoWrap`은 캔버스와 폭이 정확히 같은 형제 요소로 둔다.
  `xScale.getPixelForValue(idx)`가 반환하는 픽셀 값은 "캔버스 왼쪽 끝을 0으로 하는" 좌표이므로,
  wrap에 별도의 margin/padding-left를 주지 않아야 브래킷이 차트의 실제 날짜 위치와 정확히
  일치한다.