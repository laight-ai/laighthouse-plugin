# MTD Section 6.1: 카테고리별 월 누적 매출

**report_type:** `mtd` (항상 포함)

## MCP 도구 호출: `get_naver_category_sales`

```json
{
  "brand_name": "...", "start_date": "월초", "end_date": "target_date",
  "prev_start_date": "전월 동일구간 시작", "prev_end_date": "전월 동일구간 끝"
}
```
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`). `product_category_3rd`
  단위 groupby/합산, `discount_rate`/`refund_rate`/`mom` 계산, `sales` 내림차순 정렬까지
  **서버에서 이미 끝낸 상태**로 반환한다 (`prev_start_date`/`prev_end_date`를 주면 `mom`까지 계산됨).
- 응답 `items[]`가 곧 `product_cumulative_sales` 배열이다 (`category`/`sales`/`discount_rate`/
  `refund_rate`/`mom` 필드 그대로 사용; `mom`은 전월 데이터가 없으면 `null`).

## 필요 데이터 (MCP)
- `product_cumulative_sales`: 카테고리 배열
  ```json
  [
    { "category": "국내분유", "sales": 64295126, "discount_rate": 91.75, "refund_rate": 41.86, "mom": 49.19 },
    { "category": "커피", "sales": 44081771, "discount_rate": 92.80, "refund_rate": 19.78, "mom": 47.20 }
  ]
  ```
- `sales`, `discount_rate`(할인율 %), `refund_rate`(환불금액 비율 %), `mom`(MoM % 증감, 음수 가능)

## 본 테이블은 참조용으로만 사용하며, 프론트에서는 노출하지 않는다.

## Script

```javascript
// 공통 테이블 유틸 (한 번만 정의, 중복 방지 — shared/sections/daily/daily-section-6-campaign-table.md와 동일)
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

// 상품별 누적 판매액 테이블 초기화
window.initTable('productSalesTable');
```

## 렌더링 규칙
- `sales`는 `toLocaleString()`으로 천 단위 콤마 포맷 (원 단위, 접미사 없음)
- `mom`이 양수면 `#16a34a`(초록) + `▲ +{mom}%`, 음수면 `#dc2626`(빨강) + `▼ {mom}%`
- 데이터가 없으면 "데이터 준비 중" 카드로 대체