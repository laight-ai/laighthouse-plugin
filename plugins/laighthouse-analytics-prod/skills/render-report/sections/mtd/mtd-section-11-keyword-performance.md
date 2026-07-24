# MTD Section 11: 키워드별 성과

**report_type:** `mtd` (항상 포함)

## MCP 도구 호출: `get_naver_keyword_performance`

```json
{ "brand_name": "...", "start_date": "월초", "end_date": "target_date" }
```
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`). 도구 내부가 페이지네이션을
  자동으로 다 돌며 raw row를 가져오고, `term`(키워드)별 groupby/합산/cpc·ctr·cpm·roas 계산과
  정렬(`-roas,-ad_cost,-revenue,keyword`)까지 **서버에서 이미 끝낸 상태**로 반환한다
  (`term == "-"`인 행은 서버에서 이미 제외됨).
- 응답 `items[]`가 곧 `keyword_performance` 배열이다 (`keyword`/`impressions`/`clicks`/`ad_cost`/
  `cpc`/`ctr`/`cpm`/`purchases`/`revenue`/`roas` 필드 그대로 사용).
- 키워드 수가 매우 많을 수 있으나(수백~수천 건) 이미 합산된 최종 행 목록이므로 다시 집계하지 않는다.

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
<!-- MTD SECTION 11: 키워드별 성과 -->
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
          <th style="text-align:right;">클릭율</th>
          <th style="text-align:right;">CPM</th>
          <th style="text-align:right;">구매건수</th>
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

// 키워드별 성과 테이블 초기화
window.initTable('mtdKeywordTable');
```

## 렌더링 규칙
- 금액/노출/클릭 필드는 `toLocaleString()` 천 단위 콤마 포맷
- 반환 키워드 수가 매우 많을 수 있음(PDF 기준 130페이지 규모) — `get_naver_keyword_performance`는
  절단 파라미터가 없고 합산·정렬된 전체 키워드를 반환하므로, 전부 받아 클라이언트 페이지네이션으로
  처리한다 (report-backend `build_keywords_table`도 상위 N 컷 없이 전체를 낸다)
- 노출/클릭/구매가 모두 0인 키워드도 그대로 표시 (성과 없음 상태 확인 목적)