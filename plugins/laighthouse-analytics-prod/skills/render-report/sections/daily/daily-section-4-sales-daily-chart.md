# Daily Section 4: 최근 7일 성과

**report_type:** `daily` (항상 포함) — daily-section-1과 동일한 분기 규칙을 따른다.

---

## 분기 A: Google/Meta 브랜드

**MCP 도구:** `get_sales_performance_daily` (start_date=week_start, end_date=target_date)

### 필요 데이터
- `sales_daily.labels`: 날짜 레이블 배열 — 예: `["3/26(Thu)", ..., "4/1(Wed)"]`
- `sales_daily.revenue`: 매출 배열 ($)
- `sales_daily.ad_spend`: 광고비 배열 ($)
- `sales_daily.roas`: ROAS 배열 (%)

### HTML
```html
<!-- DAILY SECTION 4 (Google/Meta): Sales Daily Chart -->
<div style="background:white; border:1px solid #e2e8f0; padding:20px 24px; margin-bottom:16px;">
  <div style="font-size:15px; font-weight:700; color:#1e293b; margin-bottom:16px;">
    Sales campaign: Daily performance in the last 7 days
  </div>
  <div style="position:relative; height:300px;">
    <canvas id="salesDailyChart"></canvas>
  </div>
</div>
```

### Script
```javascript
(function(){
  const ctx = document.getElementById('salesDailyChart');
  if(!ctx) return;
  const d = {SALES_DAILY_DATA};
  new Chart(ctx, {
    data: {
      labels: d.labels,
      datasets: [
        { type: 'bar', label: 'Revenue', data: d.revenue, backgroundColor: '#94a3b8', yAxisID: 'y', order: 2 },
        { type: 'bar', label: 'Ad Spend', data: d.ad_spend, backgroundColor: '#93c5fd', yAxisID: 'y', order: 3 },
        { type: 'line', label: 'ROAS', data: d.roas, borderColor: '#ef4444', backgroundColor: 'transparent',
          pointBackgroundColor: '#ef4444', pointRadius: 4, tension: 0.3, yAxisID: 'y2', order: 1 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: {
        y:  { position: 'left',  beginAtZero: true, ticks: { callback: v => '$'+v.toLocaleString() } },
        y2: { position: 'right', beginAtZero: true, grid: { drawOnChartArea: false }, ticks: { callback: v => v+'%' } }
      }
    }
  });
})();
```

---

## 분기 B: naver 브랜드 ⭐ 신규

**MCP 도구 호출: `get_naver_daily_attributed_sales`**

```json
{ "brand_name": "...", "start_date": "target_date - 6일", "end_date": "target_date" }
```

- naver 전용 MCP 도구. 브랜드 전체(5개 채널 합산) 일별 `ad_cost`/`clicks`/`purchases`/`revenue`를
  반환한다 — GFA VAT 조정 등 채널별 보정이 이미 서버에서 끝난 최종 집계값이다.
- `roas`는 이 스킬이 직접 계산한다: `revenue / ad_cost × 100`.

**MCP 도구 호출: `list_promotions`** (2026-07-24 추가 — 아래 "프로모션 오버레이" 참고)

```json
{ "brand_name": "...", "start_date": "target_date - 6일", "end_date": "target_date" }
```
- 위 `get_naver_daily_attributed_sales`와 정확히 같은 날짜 범위로 1회만 호출한다 (차트 데이터와
  별개 호출이지만, 같은 7일 구간이므로 재사용 없이 딱 한 번 더 호출하면 됨).

### 필요 데이터 (MCP)
- `sales_daily.labels`: 날짜 레이블 배열 — 예: `["4/22(수)", ..., "4/28(화)"]` (요일은 이 스킬이
  `logdate`로부터 계산)
- `sales_daily.revenue`: 매출 배열 (원) ← `revenue`
- `sales_daily.ad_spend`: 광고비 배열 (원) ← `ad_cost`
- `sales_daily.roas`: ROAS 배열 (%) ← `revenue / ad_cost × 100`

### 프로모션 오버레이 (2026-07-24 추가, 2026-07-24 셀 좌표 정렬 방식으로 재수정)

스크린샷 참고 — 차트 바로 아래에 날짜 수만큼 칸을 나눈 표를 놓고, 그 날짜가 프로모션 기간에
포함되면 프로모션명을 표시한다 (기존에 있던 "순수 장식용 날짜 스트립"을 실제 프로모션 표시로
교체한다 — 더 이상 빈 칸으로 두지 않는다). ⚠️ **칸의 너비/위치는 CSS로 단순 균등분할하지
않고, 차트의 실제 `xScale` 픽셀 좌표로 계산한다** — 처음에는 `grid-template-columns:
repeat(7,1fr)`로 균등분할했으나, 이 차트는 왼쪽(매출/광고비 원화)과 오른쪽(ROAS %) 양쪽에
Y축이 있어 실제 플롯 영역이 전체 폭보다 좁다. 균등분할 칸은 이 좁아진 플롯 영역과 어긋나
칸이 실제 막대 위치를 벗어나 보이는 문제가 있었다 — 아래 HTML/Script의 좌표 계산 방식으로
해결했다 (mtd-section-6/monthly-section-7의 프로모션 브래킷과 같은 `xScale.getPixelForValue()`
좌표계 원리를 셀 단위로 적용한 것).

**데이터 가공** (이 단계만 예외적으로 허용 — 상위 "데이터 처리 원칙" 참고):
1. `list_promotions` 응답의 `items[]`(각 `date_begin`/`date_end`/`title`)를 받는다.
2. `sales_daily.labels`의 각 날짜에 대해, `date_begin <= 그 날짜 <= date_end`를 만족하는
   프로모션이 있으면 그 `title`을 그 날짜의 셀 값으로 매핑한다 (`daily_promotions[i]`).
3. 같은 날짜에 프로모션이 2개 이상 겹치면, `title`을 줄바꿈으로 이어 붙인다 (셀 안에서 두 줄로
   표시 — 아래 HTML의 `white-space:pre-line` 참고). 겹치는 경우가 실제로는 드물다.
4. 프로모션이 없는 날짜는 빈 문자열(`""`)로 둔다.
5. 위 1~4단계는 전부 기계적 날짜 매칭이며 프로모션 존재 여부를 임의로 추정하지 않으므로 상위
   "데이터 처리 원칙"과 충돌하지 않는다.

**응답 데이터 구조 (가공 후)**
```json
{
  "daily_promotions": ["가정의 달 세일", "가정의 달 세일", "가정의 달 세일", "", "", "", "부처님 오신날"]
}
```
(배열 순서와 길이는 `sales_daily.labels`와 정확히 1:1 대응한다)

### HTML
```html
<!-- DAILY SECTION 4 (naver): 최근 7일 성과 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">최근 7일 성과</div>
  <div style="position:relative; height:300px;">
    <canvas id="naverSalesDailyChart"></canvas>
  </div>

  <!-- 날짜별 프로모션 현황 (2026-07-24 추가, 2026-07-24 재수정: CSS 그리드 등분 → 차트의
       실제 xScale 픽셀 좌표로 셀 위치/너비를 계산하는 방식으로 교체 — 차트 위 막대(bar) 영역과
       정확히 겹치도록 하기 위함. "날짜 탭"이라는 이름은 삭제, 이제 순수 표시용이 아니라 차트와
       좌표를 공유하는 오버레이다.) -->
  <div id="naverSalesDailyPromoWrap" style="position:relative; height:38px; margin-top:2px;"></div>
</div>
```

### Script
```javascript
(function(){
  const ctx = document.getElementById('naverSalesDailyChart');
  if(!ctx) return;
  const d = {SALES_DAILY_DATA}; // { labels:[...], revenue:[...], ad_spend:[...], roas:[...] }
  const promoTitles = {DAILY_PROMOTIONS_DATA}; // ["여름 특가","여름 특가","여름 특가","","","","회원의 날"] — d.labels와 1:1 대응, 없으면 전부 ""
  const targetDateIndex = {TARGET_DATE_INDEX}; // d.labels 안에서 target_date의 인덱스 (보통 마지막, 6)

  const chart = new Chart(ctx, {
    data: {
      labels: d.labels,
      datasets: [
        { type: 'bar', label: '매출', data: d.revenue, backgroundColor: '#94a3b8', yAxisID: 'y', order: 2 },
        { type: 'bar', label: '광고비', data: d.ad_spend, backgroundColor: '#93c5fd', yAxisID: 'y', order: 3 },
        { type: 'line', label: 'ROAS', data: d.roas, borderColor: '#ef4444', backgroundColor: 'transparent',
          pointBackgroundColor: '#ef4444', pointRadius: 4, tension: 0.3, yAxisID: 'y2', order: 1 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: {
        y:  { position: 'left',  beginAtZero: true, ticks: { callback: v => '₩'+v.toLocaleString() } },
        y2: { position: 'right', beginAtZero: true, grid: { drawOnChartArea: false }, ticks: { callback: v => v+'%' } }
      }
    }
  });

  // 날짜별 프로모션 셀 오버레이 (2026-07-24 재수정)
  // 주의: naverSalesDailyPromoWrap은 캔버스와 폭이 정확히 같은 형제 요소여야 한다 — mtd-section-6/
  // monthly-section-7의 프로모션 브래킷 오버레이와 동일한 좌표계 규칙이다. margin/padding으로
  // wrap을 들여쓰면 셀이 차트의 실제 막대 위치와 어긋난다.
  const wrap = document.getElementById('naverSalesDailyPromoWrap');
  if (wrap) {
    const xScale = chart.scales.x;
    const n = d.labels.length;
    // 카테고리 한 칸의 폭 = 인접한 두 카테고리 중심 사이의 픽셀 거리 (chartArea 폭을 n으로
    // 나누는 방식보다 Chart.js의 실제 카테고리 오프셋 방식에 더 정확히 맞는다)
    const step = n > 1 ? (xScale.getPixelForValue(1) - xScale.getPixelForValue(0)) : (chart.chartArea.right - chart.chartArea.left);

    for (let i = 0; i < n; i++) {
      const center = xScale.getPixelForValue(i);
      let left = center - step / 2;
      let right = center + step / 2;
      // 양 끝 칸은 차트의 실제 플롯 영역 경계(chartArea.left/right, 즉 Y축이 시작/끝나는
      // 지점)에 정확히 맞춰 clamp한다 — 그렇지 않으면 첫/마지막 칸이 축 경계를 살짝 넘어가
      // "선이 미완성으로 삐져나온" 것처럼 보인다 (2026-07-24 수정 사항).
      if (i === 0) left = chart.chartArea.left;
      if (i === n - 1) right = chart.chartArea.right;
      const width = right - left;

      const isTarget = i === targetDateIndex;
      const hasPromo = !!promoTitles[i];
      let bg = '#fff', color = '#374151';
      if (isTarget) { bg = '#fee2e2'; color = '#dc2626'; }
      else if (hasPromo) { bg = '#eff6ff'; color = '#1e3a8a'; }

      const cell = document.createElement('div');
      cell.style.cssText = `position:absolute; top:0; left:${left}px; width:${width}px; height:100%; box-sizing:border-box; border:1px solid #e2e8f0; display:flex; align-items:center; justify-content:center; text-align:center; background:${bg}; color:${color}; font-size:11px; font-weight:${(hasPromo||isTarget) ? 600 : 400}; line-height:1.3; padding:2px 4px;`;
      cell.textContent = promoTitles[i] || '';
      wrap.appendChild(cell);
    }
  }
})();
```

### 렌더링 규칙 (분기 B)
- ⚠️ **좌표계 (2026-07-24 재수정)**: 셀은 더 이상 CSS `grid-template-columns:repeat(7,1fr)`로
  균등 분할하지 않는다 — 그 방식은 차트의 실제 플롯 영역(양쪽 Y축 사이, y축 라벨 폭만큼 안쪽으로
  들어간 영역)과 셀 폭이 어긋난다. 대신 `xScale.getPixelForValue()`로 각 날짜 카테고리의 실제
  중심 픽셀을 구하고, 그 사이 거리(`step`)로 셀 폭을 계산한다. 첫 번째 칸의 왼쪽 끝과 마지막
  칸의 오른쪽 끝은 `chart.chartArea.left`/`chart.chartArea.right`(왼쪽/오른쪽 Y축이 시작하는
  지점)에 정확히 clamp해, 셀 전체 구간이 차트의 막대/라인 영역과 한 치의 오차 없이 겹치도록
  한다.
- 셀 테두리는 각 셀이 자기 몫만큼만 그린다 (`border:1px solid #e2e8f0`를 개별 셀에 적용) — 래퍼
  전체를 감싸는 별도 테두리를 두지 않는다 (래퍼 테두리를 두면 셀 내용보다 테두리가 더 넓게 보여
  "미완성"처럼 보이는 문제가 있었다, 2026-07-24 수정).
- `target_date`에 해당하는 셀만 `bg=#fee2e2`(연한 빨강), `color=#dc2626` — 요일과 무관하게
  report의 기준일이라서 강조되는 것이며, 프로모션 유무와는 별개 스타일이다.
- 나머지 셀 중 프로모션이 있는 날은 `bg=#eff6ff`(옅은 파랑), `color=#1e3a8a`(남색).
- 프로모션도 없고 target_date도 아닌 셀은 `bg=#fff`, `color=#374151`.
- **target_date이면서 동시에 프로모션이 있는 날은 target_date 강조(빨강 배경)를 우선한다** —
  두 스타일이 겹치면 기준일 표시가 더 중요하다. 이때도 프로모션명 텍스트는 그대로 표시한다
  (배경/글자색만 빨강으로, 텍스트 자체를 지우지 않음).
- 폰트는 11px, 셀 안에서 `display:flex`로 수평/수직 중앙 정렬한다. 프로모션명이 길면 자동으로
  줄바꿈된다(`line-height:1.3`으로 2줄까지 자연스럽게 들어감, 별도 truncate 불필요).
- 클릭 핸들러는 만들지 않는다 (여전히 순수 표시용 — 인터랙션은 이 스킬 범위 밖).
