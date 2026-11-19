/* 보고서 표 부품 JS — 검색 + 페이지 나누기 표. 빌더가 템플릿에 인라인한다(report_kit.inline_assets).
 * 전역: window.LHKit.pagedTable (report_kit.js와 함께 써도 되고 따로 써도 된다)
 */
(function () {
  const K = window.LHKit = window.LHKit || {};

  /* 검색 + 페이지 나누기 표 — 정적 HTML이라 행 전체(<tr> HTML + 검색용 소문자 텍스트)를 심어 두고 브라우저에서 거른다.
   * opts: {rows:[{search, html}], tbody, pager, count(요소 id), colspan, pageSize(기본 10), unit(개수 단위),
   *        global(검색 input·페이지 버튼이 부르는 window 함수 접두 — <global>Goto/<global>Search)} */
  K.pagedTable = function (opts) {
    const rows = opts.rows || [];
    const pageSize = opts.pageSize || 10;
    const tbody = document.getElementById(opts.tbody);
    const pager = document.getElementById(opts.pager);
    const count = opts.count ? document.getElementById(opts.count) : null;
    if (!tbody || !pager) return;
    const g = opts.global || '__lhTable';
    let term = '', page = 1;

    function button(label, to, o) {
      o = o || {};
      const look = o.active ? 'background:#3b82f6; border-color:#3b82f6; color:white;'
                            : 'background:white; border-color:#e2e8f0; color:#64748b;';
      return `<button ${o.disabled ? 'disabled' : ''} style="border:1px solid #e2e8f0; border-radius:6px; min-width:28px; padding:0 6px; height:28px; font-size:12px; cursor:${o.disabled ? 'default' : 'pointer'}; ${look}" onclick="window.${g}Goto && window.${g}Goto(${to})">${label}</button>`;
    }

    function render() {
      const list = term ? rows.filter(r => r.search.includes(term)) : rows;
      const total = Math.max(1, Math.ceil(list.length / pageSize));
      page = Math.min(Math.max(1, page), total);
      const start = (page - 1) * pageSize;
      const shown = list.slice(start, start + pageSize);
      tbody.innerHTML = shown.length ? shown.map(r => r.html).join('')
        : `<tr><td colspan="${opts.colspan}" style="text-align:center; color:#94a3b8; padding:20px;">검색 결과가 없습니다.</td></tr>`;
      // 페이지 번호 접기 — 1 … 4 5 [6] 7 8 … 47 (첫/끝 + 현재 ±2만, 나머지는 …)
      const pages = [];
      for (let i = 1; i <= total; i++) {
        if (i === 1 || i === total || Math.abs(i - page) <= 2) pages.push(i);
        else if (pages[pages.length - 1] !== '…') pages.push('…');
      }
      let html = button('‹', page - 1, { disabled: page === 1 });
      pages.forEach(p => {
        html += p === '…' ? '<span style="width:20px; text-align:center; font-size:12px; color:#94a3b8;">…</span>'
                          : button(String(p), p, { active: p === page });
      });
      pager.innerHTML = html + button('›', page + 1, { disabled: page === total });
      if (count) {
        count.textContent = list.length
          ? `총 ${list.length.toLocaleString()}개 ${opts.unit || ''} 중 ${(start + 1).toLocaleString()}–${(start + shown.length).toLocaleString()}`
          : '';
      }
    }

    window[g + 'Goto'] = function (p) { page = p; render(); };
    window[g + 'Search'] = function (v) { term = (v || '').trim().toLowerCase(); page = 1; render(); };
    render();
  };
})();
