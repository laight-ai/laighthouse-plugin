# Daily Section 6: Performance by Campaign

**report_type:** `daily`
**MCP 도구:** `get_sales_by_campaign_monthly` (start_month=current_month, end_month=current_month, day_offset=target_date.day)

## 필요 데이터
- `sales_by_campaign`: 캠페인 배열
  ```json
  [
    {
      "media": "Google Ads",
      "campaign": "Auto_Gen_D2C_BottomFunnel_Rev_PerfMax - High Performing + Other",
      "impression": 3548,
      "click": 62,
      "ctr": 1.75,
      "cost": 53,
      "revenue": 46,
      "roas": 86.8
    }
  ]
  ```

## HTML

```html
<!-- DAILY SECTION 6: Performance by Campaign -->
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
        <option value="10">10개</option>
        <option value="20">20개</option>
        <option value="50">50개</option>
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
        <!-- {sales_by_campaign} 배열을 순회하며 아래 행 반복 -->
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

  <!-- 페이지네이션 -->
  <div id="campaignPagination" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:14px; font-size:13px; color:#64748b;">
  </div>
</div>
```

## Script

```javascript
// 공통 테이블 유틸 (한 번만 정의, 중복 방지)
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

    // 페이지네이션
    const pgEl = document.getElementById(tableId.replace('Table','') + 'Pagination') ||
                 document.getElementById(tableId + 'Pagination');
    if(pgEl){
      pgEl.innerHTML = '';
      const prev = document.createElement('button');
      prev.textContent = '‹';
      prev.disabled = page <= 1;
      prev.style.cssText = 'border:1px solid #e2e8f0;background:white;padding:4px 10px;border-radius:4px;cursor:pointer;';
      prev.onclick = () => { state.page = page - 1; window._tableState[tableId] = state; window.renderTablePage(tableId); };
      pgEl.appendChild(prev);

      for(let i=1; i<=totalPages; i++){
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

// Campaign 테이블 초기화
window.initTable('campaignTable');
```
