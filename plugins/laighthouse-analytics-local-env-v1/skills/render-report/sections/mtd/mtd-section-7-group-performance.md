# MTD Section 7: 그룹별 성과

**report_type:** `mtd` (항상 포함)

## 필요 데이터 (MCP)
- `group_performance`: 광고그룹 배열
  ```json
  [
    { "group": "002_브랜드_공용_통합", "impressions": 3528, "clicks": 108, "cpc": 346.41, "ad_cost": 37412, "revenue": 666438 },
    { "group": "0412_브랜드_단백질_단백질_영캐어", "impressions": 588, "clicks": 25, "cpc": 378.16, "ad_cost": 9454, "revenue": 258053 }
  ]
  ```

## HTML

```html
<!-- MTD SECTION 7: 그룹별 성과 -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title" style="margin-bottom:0;">그룹별 성과</div>
    <div style="display:flex; align-items:center; gap:8px;">
      <div style="display:flex; align-items:center; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input type="text" placeholder="검색" oninput="filterTable('mtdGroupTable', this.value)"
          style="border:none; background:transparent; font-size:13px; color:#374151; outline:none; width:100px;">
      </div>
      <select onchange="changePageSize('mtdGroupTable', this.value)"
        style="border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; font-size:13px; color:#374151; background:#f8fafc;">
        <option value="10">10개</option>
        <option value="20">20개</option>
        <option value="50">50개</option>
      </select>
    </div>
  </div>

  <div style="overflow-x:auto;">
    <table id="mtdGroupTable">
      <thead>
        <tr>
          <th>광고그룹</th>
          <th style="text-align:right;">노출</th>
          <th style="text-align:right;">클릭</th>
          <th style="text-align:right;">CPC</th>
          <th style="text-align:right;">광고비</th>
          <th style="text-align:right;">매출</th>
        </tr>
      </thead>
      <tbody id="mtdGroupTableBody">
        <!-- group_performance 배열을 순회하며 아래 행 반복 -->
        <tr>
          <td>{group}</td>
          <td style="text-align:right;">{impressions_fmt}</td>
          <td style="text-align:right;">{clicks_fmt}</td>
          <td style="text-align:right;">{cpc_fmt}</td>
          <td style="text-align:right;">{ad_cost_fmt}</td>
          <td style="text-align:right;">{revenue_fmt}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div id="mtdGroupTablePagination" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:14px; font-size:13px; color:#64748b;"></div>
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

// 그룹별 성과 테이블 초기화
window.initTable('mtdGroupTable');
```

## 렌더링 규칙
- 금액/노출/클릭 필드는 `toLocaleString()` 천 단위 콤마 포맷
- PDF 기준 15페이지 규모의 대량 데이터 전제 — 기본 페이지 크기 10개
