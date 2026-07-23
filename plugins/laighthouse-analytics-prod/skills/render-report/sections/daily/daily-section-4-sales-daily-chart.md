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

### 필요 데이터 (MCP)
- `sales_daily.labels`: 날짜 레이블 배열 — 예: `["4/22(수)", ..., "4/28(화)"]` (요일은 이 스킬이
  `logdate`로부터 계산)
- `sales_daily.revenue`: 매출 배열 (원) ← `revenue`
- `sales_daily.ad_spend`: 광고비 배열 (원) ← `ad_cost`
- `sales_daily.roas`: ROAS 배열 (%) ← `revenue / ad_cost × 100`

### HTML
```html
<!-- DAILY SECTION 4 (naver): 최근 7일 성과 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">최근 7일 성과</div>
  <div style="position:relative; height:300px;">
    <canvas id="naverSalesDailyChart"></canvas>
  </div>

  <!-- 날짜 선택 탭 (스크린샷 Daily_1 하단 참고) — 순수 시각적 요소, 클릭 동작은 옵션 -->
  <div style="display:grid; grid-template-columns:repeat(7,1fr); gap:1px; background:#e2e8f0; border:1px solid #e2e8f0; margin-top:14px; font-size:12px;">
    <!-- sales_daily.labels 배열을 순회하며 아래 셀 반복 -->
    <div style="background:{TAB_BG}; color:{TAB_COLOR}; text-align:center; padding:8px 4px;">{day_label}</div>
  </div>
</div>
```

### Script
```javascript
(function(){
  const ctx = document.getElementById('naverSalesDailyChart');
  if(!ctx) return;
  const d = {SALES_DAILY_DATA}; // { labels:[...], revenue:[...], ad_spend:[...], roas:[...] }
  new Chart(ctx, {
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
})();
```

### 렌더링 규칙 (분기 B)
- 날짜 탭 셀: `target_date`에 해당하는 셀만 `TAB_BG=#fee2e2`(연한 빨강), `TAB_COLOR=#dc2626`
  (스크린샷의 26(일) 하이라이트 참고 — 실제로는 그날이 "일요일"이라서가 아니라 **report의
  기준일(target_date)이라서** 강조되는 것이니, 요일과 무관하게 target_date 셀만 강조한다).
  나머지 셀은 `TAB_BG=white`, `TAB_COLOR=#374151`.
  ⚠️ 스크린샷에는 이 6일치 탭 아래 실제 내용이 비어 있다 — 클릭 시 무언가를 보여주는 실제
  인터랙션 사양은 확인되지 않았으므로, 이 스킬은 **순수 장식용 날짜 스트립**으로만 렌더링한다
  (클릭 핸들러를 만들지 않는다). 추후 실제 동작이 필요해지면 별도 요구사항으로 추가한다.
