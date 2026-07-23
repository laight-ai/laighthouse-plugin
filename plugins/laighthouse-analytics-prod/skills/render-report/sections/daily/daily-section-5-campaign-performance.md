# Daily Section 5: 캠페인 성과

**report_type:** `daily` (항상 포함) — daily-section-1과 동일한 분기 규칙을 따른다.

⚠️ **이 파일은 기존 "daily-section-6-campaign-table.md"를 대체한다.** 섹션 재구성으로 옛
section 5(Daily Revenue in DTC, daily-section-4와 내용이 겹쳐 완전히 삭제됨)가 없어지면서
번호가 하나씩 당겨졌고, naver 분기의 설계도 **채널 단위 표 → 캠페인 단위 표**로 바뀌었다
(예전엔 5개 채널 요약 + 불확실한 "적정 광고비" 컬럼이 있었으나, 그 컬럼의 계산식을 확인할 수
없었고 mtd(MK)의 캠페인별 성과(mtd-section-9)와도 형식이 달라 일관성이 없었다 — 이번 재설계로
mtd-section-9와 동일한 패턴을 그대로 재사용하도록 정리했다).

---

## 분기 A: Google/Meta 브랜드 (변경 없음)

**MCP 도구:** `get_sales_by_campaign_monthly` (start_month=current_month, end_month=current_month, day_offset=target_date.day)

### 필요 데이터
- `sales_by_campaign`: 캠페인 배열
  ```json
  [
    { "media": "Google Ads", "campaign": "Auto_Gen_D2C_BottomFunnel_Rev_PerfMax - High Performing + Other",
      "impression": 3548, "click": 62, "ctr": 1.75, "cost": 53, "revenue": 46, "roas": 86.8 }
  ]
  ```

### HTML
```html
<!-- DAILY SECTION 5 (Google/Meta): Performance by Campaign -->
<div style="background:white; border:1px solid #e2e8f0; padding:20px 24px; margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div style="font-size:15px; font-weight:700; color:#1e293b;">Performance by Campaign</div>
    <div style="display:flex; align-items:center; gap:8px;">
      <div style="display:flex; align-items:center; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input id="campaignSearch" type="text" placeholder="검색" oninput="filterTable('campaignTable', this.value)"
          style="border:none; background:transparent; font-size:13px; color:#374151; outline:none; width:100px;">
      </div>
      <select id="campaignPageSize" onchange="changePageSize('campaignTable', this.value)"
        style="border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; font-size:13px; color:#374151; background:#f8fafc;">
        <option value="10">10개</option><option value="20">20개</option><option value="50">50개</option>
      </select>
    </div>
  </div>
  <div style="overflow-x:auto;">
    <table id="campaignTable" style="width:100%; border-collapse:collapse; font-size:13px;">
      <thead>
        <tr style="border-bottom:1px solid #e2e8f0;">
          <th style="padding:10px 12px; text-align:left; color:#64748b; font-weight:500;">Media</th>
          <th style="padding:10px 12px; text-align:left; color:#64748b; font-weight:500;">Campaign</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">Impression</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">Click</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">CTR (%)</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">Cost ($)</th>
          <th style="padding:10px 12px; text-align:right; color:#3b82f6; font-weight:500;">Revenue ($)</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">ROAS (%)</th>
        </tr>
      </thead>
      <tbody id="campaignTableBody">
        <tr style="border-bottom:1px solid #f1f5f9;">
          <td style="padding:10px 12px; color:#3b82f6; font-weight:500;">{media}</td>
          <td style="padding:10px 12px; color:#3b82f6;">{campaign}</td>
          <td style="padding:10px 12px; text-align:right;">{impression}</td>
          <td style="padding:10px 12px; text-align:right;">{click}</td>
          <td style="padding:10px 12px; text-align:right;">{ctr}</td>
          <td style="padding:10px 12px; text-align:right;">{cost}</td>
          <td style="padding:10px 12px; text-align:right;">{revenue}</td>
          <td style="padding:10px 12px; text-align:right;">{roas}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div id="campaignPagination" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:14px; font-size:13px; color:#64748b;"></div>
</div>
```

### Script
```javascript
window.initTable('campaignTable');
```
(공통 테이블 유틸은 daily-section-4/6 어느 쪽이든 먼저 로드된 곳에서 한 번만 정의됨 — 아래
"공통 Script" 참고)

---

## 분기 B: naver 브랜드 ⭐ 재설계 (채널 단위 → 캠페인 단위)

mtd(MK)의 `mtd-section-9-campaign-performance.md`와 **거의 동일한 포맷**이지만, 날짜 범위가
"월초~target_date"가 아니라 **target_date 하루뿐**이다.

### MCP 도구 호출: `get_naver_campaign_performance`

```json
{ "brand_name": "...", "start_date": "target_date", "end_date": "target_date" }
```

- naver 전용 MCP 도구. 캠페인×채널 단위로 이미 groupby/합산/roas·ctr·cpc·avg_price 계산과
  정렬(`-roas,-ad_cost,-revenue,campaign,channel`)이 **서버에서 끝난 상태**로 반환된다.
- ⚠️ **naver 검색광고(SA) 3개 채널(BRS/PLINK/NVSHOP)만 다룬다** — GFA 애드부스트/디스플레이는
  캠페인 구조가 없는 프로그래매틱 디스플레이 상품이라 이 도구에 데이터가 없다. GFA 채널의 일별
  성과를 보려면 daily-section-2(목표 달성 현황)의 전체 합산 수치로만 확인 가능하다 (개별 채널
  분해는 이번 섹션 재구성에서 제외되었다 — 이전 버전의 "적정 광고비" 포함 채널 요약 표는 계산식
  불확실 문제로 삭제됨).
- 응답의 `ctr`/`roas`는 이미 percentage-scale이다 (예: 1017 → 1017%) — × 100 하지 않는다.
- `cpm` 필드는 이 도구에 없으므로 이 스킬이 직접 계산한다: `cpm = ad_cost / impressions × 1000`.

### 필요 데이터 (MCP + 가공)
- `campaign_performance`: 캠페인 배열
  ```json
  [
    { "campaign": "00_통합(BS)_MO", "channel": "BRS", "revenue": 4441630, "ad_cost": 494112,
      "roas": 898.91, "impressions": 5901, "clicks": 686, "ctr": 11.63, "cpc": 720.28,
      "cpm": 83.74, "purchases": 66 }
  ]
  ```
  (`cpm`은 위 공식으로 이 스킬이 추가 — 원본 응답의 `avg_price`는 이 표에서 쓰지 않는다,
  요청된 metric 목록에 없음)

### HTML

```html
<!-- DAILY SECTION 5 (naver): 캠페인 성과 -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title" style="margin-bottom:0;">캠페인 성과</div>
    <div style="display:flex; align-items:center; gap:8px;">
      <div style="display:flex; align-items:center; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input type="text" placeholder="검색" oninput="filterTable('naverCampaignTable', this.value)"
          style="border:none; background:transparent; font-size:13px; color:#374151; outline:none; width:100px;">
      </div>
      <select onchange="changePageSize('naverCampaignTable', this.value)" style="border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; font-size:13px; color:#374151; background:#f8fafc;">
        <option value="10">10개</option><option value="20">20개</option><option value="50">50개</option>
      </select>
    </div>
  </div>

  <div style="overflow-x:auto;">
    <table id="naverCampaignTable">
      <thead>
        <tr>
          <th>광고 채널</th>
          <th>캠페인</th>
          <th style="text-align:right;">노출</th>
          <th style="text-align:right;">클릭</th>
          <th style="text-align:right;">광고비</th>
          <th style="text-align:right;">CPC</th>
          <th style="text-align:right;">CTR</th>
          <th style="text-align:right;">CPM</th>
          <th style="text-align:right;">구매건수</th>
          <th style="text-align:right;">매출</th>
          <th style="text-align:right;">ROAS</th>
        </tr>
      </thead>
      <tbody id="naverCampaignTableBody">
        <!-- campaign_performance 배열을 순회하며 아래 행 반복 -->
        <tr>
          <td>{channel_label}</td>
          <td>{campaign}</td>
          <td style="text-align:right;">{impressions_fmt}</td>
          <td style="text-align:right;">{clicks_fmt}</td>
          <td style="text-align:right;">{ad_cost_fmt}</td>
          <td style="text-align:right;">{cpc_fmt}</td>
          <td style="text-align:right;">{ctr}%</td>
          <td style="text-align:right;">{cpm_fmt}</td>
          <td style="text-align:right;">{purchases}</td>
          <td style="text-align:right;">{revenue_fmt}</td>
          <td style="text-align:right;">{roas}%</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div id="naverCampaignTablePagination" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:14px; font-size:13px; color:#64748b;"></div>
</div>
```

### Script
```javascript
window.initTable('naverCampaignTable');
```

---

## 공통 Script (두 분기가 공유 — 페이지 전체에서 한 번만 정의)

```javascript
if(!window._tableUtils){
  window._tableUtils = true;
  window._tableState = {};

  window.filterTable = function(tableId, keyword) {
    const state = window._tableState[tableId] || {};
    state.keyword = keyword.toLowerCase(); state.page = 1;
    window._tableState[tableId] = state; window.renderTablePage(tableId);
  };
  window.changePageSize = function(tableId, size) {
    const state = window._tableState[tableId] || {};
    state.pageSize = parseInt(size); state.page = 1;
    window._tableState[tableId] = state; window.renderTablePage(tableId);
  };
  window.renderTablePage = function(tableId) {
    const state = window._tableState[tableId] || {};
    const allRows = state.allRows || [];
    const keyword = state.keyword || '';
    const pageSize = state.pageSize || 10;
    const page = state.page || 1;
    const filtered = keyword ? allRows.filter(r => r.textContent.toLowerCase().includes(keyword)) : allRows;
    const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
    const start = (page - 1) * pageSize;
    const pageRows = filtered.slice(start, start + pageSize);
    const tbody = document.getElementById(tableId + 'Body');
    if(!tbody) return;
    allRows.forEach(r => r.style.display = 'none');
    pageRows.forEach(r => r.style.display = '');
    const pgEl = document.getElementById(tableId + 'Pagination');
    if(pgEl){
      pgEl.innerHTML = '';
      const prev = document.createElement('button');
      prev.textContent = '‹'; prev.disabled = page <= 1;
      prev.style.cssText = 'border:1px solid #e2e8f0;background:white;padding:4px 10px;border-radius:4px;cursor:pointer;';
      prev.onclick = () => { state.page = page - 1; window._tableState[tableId] = state; window.renderTablePage(tableId); };
      pgEl.appendChild(prev);
      const maxButtons = 6;
      let startPage = Math.max(1, page - Math.floor(maxButtons / 2));
      let endPage = Math.min(totalPages, startPage + maxButtons - 1);
      startPage = Math.max(1, endPage - maxButtons + 1);
      for(let i=startPage; i<=endPage; i++){
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.style.cssText = `border:1px solid ${i===page?'#3b82f6':'#e2e8f0'};background:${i===page?'#3b82f6':'white'};color:${i===page?'white':'#374151'};padding:4px 10px;border-radius:4px;cursor:pointer;`;
        btn.onclick = ((_i) => () => { state.page = _i; window._tableState[tableId] = state; window.renderTablePage(tableId); })(i);
        pgEl.appendChild(btn);
      }
      const next = document.createElement('button');
      next.textContent = '›'; next.disabled = page >= totalPages;
      next.style.cssText = 'border:1px solid #e2e8f0;background:white;padding:4px 10px;border-radius:4px;cursor:pointer;';
      next.onclick = () => { state.page = page + 1; window._tableState[tableId] = state; window.renderTablePage(tableId); };
      pgEl.appendChild(next);
    }
  };
  window.initTable = function(tableId) {
    const tbody = document.getElementById(tableId + 'Body');
    if(!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('tr'));
    window._tableState[tableId] = { allRows: rows, page: 1, pageSize: 10, keyword: '' };
    window.renderTablePage(tableId);
  };
}
```

## 렌더링 규칙 (분기 B)
- `channel_label` 매핑: `BRS`→네이버 브랜드검색, `PLINK`→네이버 파워링크, `NVSHOP`→네이버 쇼핑검색.
- 금액/노출/클릭 필드는 `toLocaleString()` 천 단위 콤마 포맷.
- ⚠️ **`ad_cost`(광고비)가 10,000원 미만인 캠페인 행은 표에서 제외한다** (2026-07-23 추가) —
  `get_naver_campaign_performance` 응답을 받은 뒤, 렌더링 전에 `ad_cost >= 10000`인 행만
  필터링한다. 소액 테스트성 캠페인이나 노출만 있고 예산이 거의 소진되지 않은 캠페인을 표에서
  걸러내기 위함이다. 이 필터링은 표시 목적의 후처리이며, daily-section-2(목표 달성 현황) 등
  다른 섹션의 합계 수치에는 영향을 주지 않는다(그 섹션들은 필터링 이전의 전체 합계를 그대로
  쓴다).
- 필터링 후 행이 하나도 남지 않으면 "이번 기간 10,000원 이상 집행된 캠페인이 없음" 안내 카드로
  대체한다 (빈 테이블로 남기지 않음).
- 매출이 0인 캠페인도 (광고비 조건을 만족하면) 그대로 표시한다 — 광고비만 나가고 전환이 없는
  캠페인도 중요한 신호다.
