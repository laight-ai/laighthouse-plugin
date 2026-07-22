# MTD Section 9: 캠페인별 성과

**report_type:** `mtd` (항상 포함)

## MCP 도구 호출: `get_naver_campaign_performance`

```json
{ "brand_name": "...", "start_date": "월초", "end_date": "target_date" }
```
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`). 캠페인×채널 단위 groupby/합산/
  roas·ctr·cpc·avg_price 계산과 정렬(`-roas,-ad_cost,-revenue,campaign,channel`)을 **서버에서 이미
  끝낸 상태**로 반환한다 — LLM이 raw row를 그룹핑하거나 비율을 계산할 필요가 없다.
- 응답 `items[]`가 곧 `campaign_performance` 배열이다 (`campaign`/`channel`/`revenue`/`ad_cost`/
  `roas`/`impressions`/`clicks`/`ctr`/`cpc`/`purchases`/`avg_price` 필드 그대로 사용, 그대로 렌더링).

## 필요 데이터 (MCP)
- `campaign_performance`: 캠페인 배열
  ```json
  [
    { "campaign": "05_GT케이(SPBR)_MO", "channel": "NVSHOP", "revenue": 1320543, "ad_cost": 129801,
      "roas": 1017, "impressions": 12778, "clicks": 53, "ctr": 0.41, "cpc": 2449.08,
      "purchases": 17, "avg_price": 77679 }
  ]
  ```
- `roas`, `ctr`는 % 단위 숫자, `cpc`/`avg_price`는 원 단위

## HTML

```html
<!-- MTD SECTION 9: 캠페인별 성과 -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title" style="margin-bottom:0;">캠페인별 성과</div>
    <div style="display:flex; align-items:center; gap:8px;">
      <div style="display:flex; align-items:center; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input type="text" placeholder="검색" oninput="filterTable('mtdCampaignTable', this.value)"
          style="border:none; background:transparent; font-size:13px; color:#374151; outline:none; width:100px;">
      </div>
      <select onchange="changePageSize('mtdCampaignTable', this.value)"
        style="border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; font-size:13px; color:#374151; background:#f8fafc;">
        <option value="10">10개</option>
        <option value="20">20개</option>
        <option value="50">50개</option>
      </select>
    </div>
  </div>

  <div style="overflow-x:auto;">
    <table id="mtdCampaignTable">
      <thead>
        <tr>
          <th>캠페인</th>
          <th>네이버 광고 채널명</th>
          <th style="text-align:right;">매출</th>
          <th style="text-align:right;">광고비</th>
          <th style="text-align:right;">ROAS</th>
          <th style="text-align:right;">노출</th>
          <th style="text-align:right;">클릭</th>
          <th style="text-align:right;">CTR</th>
          <th style="text-align:right;">CPC</th>
          <th style="text-align:right;">구매</th>
          <th style="text-align:right;">평균단가</th>
        </tr>
      </thead>
      <tbody id="mtdCampaignTableBody">
        <!-- campaign_performance 배열을 순회하며 아래 행 반복 -->
        <tr>
          <td>{campaign}</td>
          <td>{channel}</td>
          <td style="text-align:right;">{revenue_fmt}</td>
          <td style="text-align:right;">{ad_cost_fmt}</td>
          <td style="text-align:right;">{roas}%</td>
          <td style="text-align:right;">{impressions_fmt}</td>
          <td style="text-align:right;">{clicks_fmt}</td>
          <td style="text-align:right;">{ctr}%</td>
          <td style="text-align:right;">{cpc_fmt}</td>
          <td style="text-align:right;">{purchases}</td>
          <td style="text-align:right;">{avg_price_fmt}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div id="mtdCampaignTablePagination" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:14px; font-size:13px; color:#64748b;"></div>
</div>
```

## Script

```javascript
// 공통 테이블 유틸 (한 번만 정의, 중복 방지 — sections/daily/daily-section-6-campaign-table.md와 동일)
if(!window._tableUtils){
  window._tableUtils = true;
  window._tableState = {};

  window.filterTable = function(tableId, keyword) {
    const state = window._tableState[tableId] || {};
    state.keyword = keyword.toLowerCase();
    state.page = 1;
    window._tableState[tableId] = state;
    window.renderTablePage(tableId);
  };

  window.changePageSize = function(tableId, size) {
    const state = window._tableState[tableId] || {};
    state.pageSize = parseInt(size);
    state.page = 1;
    window._tableState[tableId] = state;
    window.renderTablePage(tableId);
  };

  window.renderTablePage = function(tableId) {
    const state = window._tableState[tableId] || {};
    const allRows = state.allRows || [];
    const keyword = state.keyword || '';
    const pageSize = state.pageSize || 10;
    const page = state.page || 1;

    const filtered = keyword
      ? allRows.filter(r => r.textContent.toLowerCase().includes(keyword))
      : allRows;

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
      prev.textContent = '‹';
      prev.disabled = page <= 1;
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
      next.textContent = '›';
      next.disabled = page >= totalPages;
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

// 캠페인별 성과 테이블 초기화
window.initTable('mtdCampaignTable');
```

## 렌더링 규칙
- 금액/노출/클릭 필드는 `toLocaleString()` 천 단위 콤마 포맷
- 데이터 건수가 많으므로 기본 페이지 크기 10개로 시작