# MTD Section 2: 상품별 누적 판매액

**report_type:** `mtd` (항상 포함)

## 필요 데이터 (MCP)
- `product_cumulative_sales`: 카테고리 배열
  ```json
  [
    { "category": "국내분유", "sales": 64295126, "discount_rate": 91.75, "refund_rate": 41.86, "mom": 49.19 },
    { "category": "커피", "sales": 44081771, "discount_rate": 92.80, "refund_rate": 19.78, "mom": 47.20 }
  ]
  ```
- `sales`, `discount_rate`(할인율 %), `refund_rate`(환불금액 비율 %), `mom`(MoM % 증감, 음수 가능)

## HTML

```html
<!-- MTD SECTION 2: 상품별 누적 판매액 -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title" style="margin-bottom:0;">상품별 누적 판매액</div>
    <div style="display:flex; align-items:center; gap:8px;">
      <div style="display:flex; align-items:center; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input id="productSalesSearch" type="text" placeholder="검색" oninput="filterTable('productSalesTable', this.value)"
          style="border:none; background:transparent; font-size:13px; color:#374151; outline:none; width:100px;">
      </div>
      <select onchange="changePageSize('productSalesTable', this.value)"
        style="border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; font-size:13px; color:#374151; background:#f8fafc;">
        <option value="10">10개</option>
        <option value="20">20개</option>
        <option value="50">50개</option>
      </select>
    </div>
  </div>

  <div style="overflow-x:auto;">
    <table id="productSalesTable">
      <thead>
        <tr>
          <th>상품 카테고리 (s)</th>
          <th style="text-align:right;">판매액</th>
          <th style="text-align:right;">할인율</th>
          <th style="text-align:right;">환불금액 비율</th>
          <th style="text-align:right;">MoM(%)</th>
        </tr>
      </thead>
      <tbody id="productSalesTableBody">
        <!-- product_cumulative_sales 배열을 순회하며 아래 행 반복 -->
        <tr>
          <td>{category}</td>
          <td style="text-align:right;">{sales_fmt}</td>
          <td style="text-align:right;">{discount_rate}%</td>
          <td style="text-align:right;">{refund_rate}%</td>
          <td style="text-align:right; color:{mom_color};">{mom_label}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div id="productSalesTablePagination" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:14px; font-size:13px; color:#64748b;"></div>
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

// 상품별 누적 판매액 테이블 초기화
window.initTable('productSalesTable');
```

## 렌더링 규칙
- `sales`는 `toLocaleString()`으로 천 단위 콤마 포맷 (원 단위, 접미사 없음)
- `mom`이 양수면 `#16a34a`(초록) + `▲ +{mom}%`, 음수면 `#dc2626`(빨강) + `▼ {mom}%`
- 데이터가 없으면 "데이터 준비 중" 카드로 대체
