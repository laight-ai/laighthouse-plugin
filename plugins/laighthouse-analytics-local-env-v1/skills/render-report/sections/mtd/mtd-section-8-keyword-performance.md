# MTD Section 8: 키워드별 성과

**report_type:** `mtd` (항상 포함)

## MCP 도구 호출: `get_ad_performance_monthly_table`

```json
{ "brand_name": "...", "start_month": "당월", "end_month": "당월", "group_by": "ad", "media": "naver", "day_offset": "target_date.day", "limit": 500 }
```
- `group_by="ad"` (naver의 ad_name=검색 키워드/term), `media="naver"`, `day_offset`으로 MTD 컷오프
- 반환은 마크다운 표 문자열 — 파싱해 아래 배열로 재구성 (`ad_name`→keyword, `cost`→ad_cost,
  `purchase_amount`→revenue, `purchase_count`→purchases, `impression`/`click`/`ctr`/`cpc`/`cpm`/`roas` 그대로)
- 키워드 수가 매우 많을 수 있어 `limit` 파라미터로 상위 N개(권장 500)로 절단 요청 권장

## 필요 데이터 (MCP)
- `keyword_performance`: 키워드 배열
  ```json
  [
    { "keyword": "알파카리그린티라떼", "impressions": 9076, "clicks": 659, "ad_cost": 353722,
      "cpc": 536.76, "ctr": 7.26, "cpm": 38973.34, "purchases": 183, "revenue": 8057615, "roas": 2278 },
    { "keyword": "경부단백질", "impressions": 556, "clicks": 0, "ad_cost": 0,
      "cpc": 0, "ctr": 0, "cpm": 0, "purchases": 0, "revenue": 0, "roas": 0 }
  ]
  ```

## HTML

```html
<!-- MTD SECTION 8: 키워드별 성과 -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title" style="margin-bottom:0;">키워드별 성과</div>
    <div style="display:flex; align-items:center; gap:8px;">
      <div style="display:flex; align-items:center; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input type="text" placeholder="검색" oninput="filterTable('mtdKeywordTable', this.value)"
          style="border:none; background:transparent; font-size:13px; color:#374151; outline:none; width:100px;">
      </div>
      <select onchange="changePageSize('mtdKeywordTable', this.value)"
        style="border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; font-size:13px; color:#374151; background:#f8fafc;">
        <option value="10">10개</option>
        <option value="20">20개</option>
        <option value="50">50개</option>
      </select>
    </div>
  </div>

  <div style="overflow-x:auto;">
    <table id="mtdKeywordTable">
      <thead>
        <tr>
          <th>키워드</th>
          <th style="text-align:right;">노출</th>
          <th style="text-align:right;">클릭</th>
          <th style="text-align:right;">광고비</th>
          <th style="text-align:right;">CPC</th>
          <th style="text-align:right;">클릭률</th>
          <th style="text-align:right;">CPM</th>
          <th style="text-align:right;">구매수</th>
          <th style="text-align:right;">매출</th>
          <th style="text-align:right;">ROAS</th>
        </tr>
      </thead>
      <tbody id="mtdKeywordTableBody">
        <!-- keyword_performance 배열을 순회하며 아래 행 반복 -->
        <tr>
          <td>{keyword}</td>
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

  <div id="mtdKeywordTablePagination" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:14px; font-size:13px; color:#64748b;"></div>
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

// 키워드별 성과 테이블 초기화
window.initTable('mtdKeywordTable');
```

## 렌더링 규칙
- 금액/노출/클릭 필드는 `toLocaleString()` 천 단위 콤마 포맷
- MCP가 반환하는 키워드 수가 매우 많을 수 있음(PDF 기준 130페이지 규모) — 클라이언트 페이지네이션으로
  처리하되, MCP 응답 자체가 너무 크면 상위 N개(예: 500개)로 절단해 요청하는 것을 권장
- 노출/클릭/구매가 모두 0인 키워드도 그대로 표시 (성과 없음 상태 확인 목적)
