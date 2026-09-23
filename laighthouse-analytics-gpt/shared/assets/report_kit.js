/* 보고서 공용 킷 JS — report_kit.py 가 만든 스펙을 그린다. 빌더가 템플릿에 인라인한다.
 * 전역: window.LHKit = { configure, fmt, mixedChart, stackChart, promoBrackets, treeTable }
 */
(function () {
  const K = {};
  let CURRENCY = '₩';
  const ZERO_DEC = ['₩', '¥', '원', 'KRW', 'JPY'];
  const SUFFIX = ['원', 'KRW', 'USD', 'JPY', 'EUR'];
  const CURRENCY_UNITS = ['₩', '$', '€', '£', '¥', '원', 'KRW', 'USD', 'JPY', 'EUR'];

  K.configure = function (opts) { if (opts && opts.currency) CURRENCY = opts.currency; };

  function money(v, cur) {
    cur = cur || CURRENCY;
    const dec = ZERO_DEC.includes(cur) ? 0 : 2;
    const body = Number(v).toLocaleString(undefined, { minimumFractionDigits: dec, maximumFractionDigits: dec });
    return SUFFIX.includes(cur) ? body + cur : cur + body;
  }
  function count(v) { return Math.round(Number(v)).toLocaleString(); }
  function pct(v, d) { return Number(v).toFixed(d == null ? 1 : d) + '%'; }
  function compact(v, unit) {
    // 축 눈금용 — 큰 수는 만/억 단위로 줄인다.
    const a = Math.abs(v);
    let s;
    if (a >= 1e8) s = (v / 1e8).toFixed(a >= 1e9 ? 0 : 1) + '억';
    else if (a >= 1e4) s = (v / 1e4).toFixed(a >= 1e5 ? 0 : 1) + '만';
    else s = Number(v).toLocaleString();
    if (unit === 'money') return SUFFIX.includes(CURRENCY) ? s + CURRENCY : CURRENCY + s;
    if (unit === 'pct') return v + '%';
    return s;
  }
  K.fmt = function (v, unit) {
    if (v == null || Number.isNaN(v)) return '-';
    if (unit === 'money') return money(v);
    if (unit === 'count') return count(v);
    if (unit === 'pct') return pct(v, 1);
    if (unit === 'pct2') return pct(v, 2);
    return Number(v).toLocaleString();
  };
  // ELT metric_units 기반 임의 지표 포맷
  function fmtMetric(v, unit) {
    if (v == null) return '—';
    if (unit === '%') return Number(v).toFixed(2) + '%';
    if (CURRENCY_UNITS.includes(unit)) return money(v, unit);
    const body = Number.isInteger(v) ? Number(v).toLocaleString()
      : Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 });
    return unit ? body + unit : body;
  }

  function legend(containerId, items) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = '';
    items.forEach(it => {
      const s = document.createElement('span');
      s.style.cssText = 'display:flex; align-items:center; gap:6px;';
      const sw = document.createElement('span');
      sw.style.cssText = it.line
        ? `width:16px; height:2px; background:${it.color}; display:inline-block;`
        : `width:12px; height:12px; background:${it.color}; display:inline-block; border-radius:2px;`;
      s.appendChild(sw);
      s.appendChild(document.createTextNode(it.label));
      el.appendChild(s);
    });
  }

  /* 혼합 차트: 막대(좌축) + 선(우축). spec = report_kit.perf_chart_spec() */
  K.mixedChart = function (canvasId, legendId, spec) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !spec || !spec.labels) return null;
    const datasets = spec.bars.map(b => ({
      type: 'bar', label: b.label, data: b.data, backgroundColor: b.color,
      borderRadius: 4, yAxisID: 'y', order: 2,
    }));
    datasets.push({
      type: 'line', label: spec.line.label, data: spec.line.data, borderColor: spec.line.color,
      backgroundColor: 'transparent', pointBackgroundColor: spec.line.color, pointRadius: 4,
      borderWidth: 2, tension: 0.3, yAxisID: 'y2', order: 1, spanGaps: true,
    });
    legend(legendId, spec.bars.map(b => ({ label: b.label, color: b.color }))
      .concat([{ label: spec.line.label, color: spec.line.color, line: true }]));
    return new Chart(ctx, {
      data: { labels: spec.labels, datasets },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: c => `${c.dataset.label}: ${K.fmt(c.parsed.y, c.dataset.yAxisID === 'y2' ? (spec.right === 'pct' ? 'pct2' : spec.right) : spec.left)}`,
              afterBody: items => {
                if (!items.length || !spec.extra) return [];
                const i = items[0].dataIndex;
                return spec.extra.map(e => `${e.label}: ${K.fmt(e.data[i], e.unit)}`);
              },
            },
          },
        },
        scales: {
          y: { position: 'left', beginAtZero: true, ticks: { callback: v => compact(v, spec.left) } },
          y2: { position: 'right', beginAtZero: true, grid: { drawOnChartArea: false },
                ticks: { callback: v => v + '%' } },
        },
      },
    });
  };

  /* 누적 막대: 매체별 추이. spec = report_kit.media_trend_spec() */
  K.stackChart = function (canvasId, legendId, spec) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !spec || !spec.series || !spec.series.length) return null;
    const datasets = spec.series.map(s => ({
      type: 'bar', label: s.label, data: s.data, backgroundColor: s.color,
      borderColor: '#ffffff', borderWidth: { top: 2, bottom: 0, left: 0, right: 0 }, borderSkipped: false,
      stack: 'total',
    }));
    legend(legendId, spec.series.map(s => ({ label: s.label, color: s.color })));
    return new Chart(ctx, {
      data: { labels: spec.labels, datasets },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: c => `${c.dataset.label}: ${K.fmt(c.parsed.y, spec.unit)}`,
              footer: items => {
                const t = items.reduce((a, it) => a + (it.parsed.y || 0), 0);
                return `합계 ${spec.metric}: ${K.fmt(t, spec.unit)}`;
              },
            },
          },
        },
        scales: {
          x: { stacked: true, ticks: { maxRotation: 0, minRotation: 0, autoSkip: true } },
          y: { stacked: true, beginAtZero: true, ticks: { callback: v => compact(v, spec.unit) } },
        },
      },
    });
  };

  /* 프로모션 브래킷: wrap은 캔버스와 폭이 같은 형제 div. band=true면 막대 차트(칸 경계 정렬). */
  K.promoBrackets = function (wrapId, chart, promos, band) {
    const wrap = document.getElementById(wrapId);
    if (!promos || !promos.length || !chart) { if (wrap) wrap.remove(); return; }
    if (!wrap) return;
    const rowHeight = 40;
    wrap.style.height = (rowHeight * promos.length) + 'px';
    const xScale = chart.scales.x;
    const chartWidth = xScale.right - xScale.left;
    const n = chart.data.labels.length;
    const half = band ? chartWidth / n / 2 : 0;
    promos.forEach((p, row) => {
      const s = Math.max(0, Math.min(n - 1, p.start_idx));
      const e = Math.max(0, Math.min(n - 1, p.end_idx));
      const xStart = xScale.getPixelForValue(s) - half;
      const xEnd = xScale.getPixelForValue(e) + half;
      const width = Math.max(xEnd - xStart, 2);
      const top = row * rowHeight;
      const centerX = xStart + width / 2;
      const bar = document.createElement('div');
      bar.style.cssText = `position:absolute; top:${top + 6}px; left:${xStart}px; width:${width}px; height:6px; border-top:1px solid #94a3b8; border-left:1px solid #94a3b8; border-right:1px solid #94a3b8;`;
      wrap.appendChild(bar);
      const label = document.createElement('div');
      label.textContent = p.title + ' (' + p.range_label + ')';
      label.style.cssText = `position:absolute; top:${top + 14}px; white-space:nowrap; font-size:11px; color:#64748b;`;
      wrap.appendChild(label);
      const lw = label.offsetWidth;
      const centered = centerX - lw / 2;
      if (centered < 0) label.style.left = xStart + 'px';
      else if (centered + lw > xScale.right) label.style.left = (xEnd - lw) + 'px';
      else label.style.left = centered + 'px';
    });
  };

  /* ── 계층 표 ──────────────────────────────────────────────────────────────
   * data = report_kit.build_tree(): {levels, metrics:[{key,unit}], cost, base, cur,
   *         nodes:[[name, curVals, baseVals, children], ...]}
   * 기능: ▶/▼ 펼치기(시작은 매체 단위), 지표 헤더 클릭 정렬(기본 광고비 내림차순),
   *       이름 검색(일치 항목의 상위 경로 자동 펼침), 지표 컬럼 선택, 자식 50개 단위 더 보기.
   */
  const PAGE = 50;
  K.treeTable = function (rootId, data, opts) {
    const root = document.getElementById(rootId);
    if (!root || !data || !data.nodes) return;
    opts = opts || {};
    const L = data.levels.length;
    const M = data.metrics;
    let idSeq = 0;
    function wrap(raw, depth, parent) {
      const n = { id: idSeq++, name: raw[0], cur: raw[1], base: raw[2], depth, parent, kids: [] };
      n.search = (parent ? parent.search + ' ' : '') + String(raw[0]).toLowerCase();
      n.kids = (raw[3] || []).map(k => wrap(k, depth + 1, n));
      return n;
    }
    const roots = data.nodes.map(r => wrap(r, 0, null));
    const costIdx = Math.max(0, M.findIndex(m => m.key === data.cost));
    const state = {
      sortIdx: costIdx, sortDir: -1, query: '',
      visible: new Set(M.map((_, i) => i)),
      open: new Set(), shown: {},
    };

    root.classList.add('lh-tree');
    root.innerHTML = `
      <div class="lh-tree-bar">
        <input type="search" class="lh-tree-search" placeholder="매체·캠페인·광고그룹·광고 검색">
        <div class="lh-tree-cols">
          <button type="button" class="lh-tree-colbtn">지표 선택 (<span class="lh-cnt"></span>/${M.length})</button>
          <div class="lh-tree-colmenu" hidden>
            <div class="lh-tree-colacts"><button type="button" data-act="all">전체 선택</button><button type="button" data-act="none">전체 해제</button></div>
            ${M.map((m, i) => `<label><input type="checkbox" data-i="${i}" checked> ${esc(m.key)}</label>`).join('')}
          </div>
        </div>
        <div class="lh-tree-acts"><button type="button" data-act="collapse">모두 접기</button></div>
      </div>
      <div class="lh-tree-scroll"><table class="lh-tree-table"><thead></thead><tbody></tbody></table></div>
      <div class="lh-tree-note">${esc(opts.note || '')}</div>`;
    const thead = root.querySelector('thead');
    const tbody = root.querySelector('tbody');
    const search = root.querySelector('.lh-tree-search');
    const menu = root.querySelector('.lh-tree-colmenu');
    const cnt = root.querySelector('.lh-cnt');

    function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

    function sortVal(n) { const v = n.cur[state.sortIdx]; return v == null ? -Infinity : v; }
    function sorted(list) {
      return list.slice().sort((a, b) => {
        const d = (sortVal(a) - sortVal(b)) * state.sortDir;
        return d !== 0 && !Number.isNaN(d) ? d : String(a.name).localeCompare(String(b.name));
      });
    }

    // 검색: 이름이 일치하는 노드 + 그 조상(펼침) + 그 자손(보임)
    function matchSet() {
      const q = state.query;
      if (!q) return null;
      const keep = new Set();
      const force = new Set();
      (function walk(list) {
        list.forEach(n => {
          if (String(n.name).toLowerCase().includes(q)) {
            keep.add(n.id);
            for (let p = n.parent; p; p = p.parent) { keep.add(p.id); force.add(p.id); }
            (function all(k) { k.forEach(c => { keep.add(c.id); all(c.kids); }); })(n.kids);
          }
          walk(n.kids);
        });
      })(roots);
      return { keep, force };
    }

    function delta(cur, base, unit) {
      if (cur == null || base == null) return '<div class="lh-d lh-d0">—</div>';
      let raw, sfx;
      if (unit === '%') { raw = cur - base; sfx = '%p'; }
      else { if (base === 0) return '<div class="lh-d lh-d0">—</div>'; raw = (cur - base) / Math.abs(base) * 100; sfx = '%'; }
      const shown = Math.round(raw * 10) / 10;
      if (shown === 0) return `<div class="lh-d lh-d0">0.0${sfx}</div>`;
      return `<div class="lh-d ${raw > 0 ? 'lh-up' : 'lh-down'}">${raw > 0 ? '▲' : '▼'} ${Math.abs(shown).toFixed(1)}${sfx}</div>`;
    }

    function renderHead() {
      const cols = M.map((m, i) => i).filter(i => state.visible.has(i));
      cnt.textContent = cols.length;
      thead.innerHTML = '<tr>' + data.levels.map(l => `<th class="lh-lv">${esc(l)}</th>`).join('') +
        cols.map(i => {
          const on = state.sortIdx === i;
          const arrow = on ? (state.sortDir < 0 ? '↓' : '↑') : '⇅';
          return `<th class="lh-m${on ? ' lh-sorted' : ''}" data-i="${i}" title="클릭해서 정렬">${esc(M[i].key)} <span class="lh-arrow">${arrow}</span></th>`;
        }).join('') + '</tr>';
      return cols;
    }

    function render() {
      const cols = renderHead();
      const ms = matchSet();
      const rows = [];
      (function walk(list, parentId) {
        let items = sorted(list);
        if (ms) items = items.filter(n => ms.keep.has(n.id));
        const limit = state.shown[parentId] || PAGE;
        items.slice(0, limit).forEach(n => {
          rows.push(rowHtml(n, cols, ms));
          const open = ms ? (ms.force.has(n.id) || state.open.has(n.id)) : state.open.has(n.id);
          if (open && n.kids.length) walk(n.kids, n.id);
        });
        if (items.length > limit) {
          const depth = list[0].depth;
          rows.push(`<tr class="lh-more"><td colspan="${L + cols.length}" style="padding-left:${12 + depth * 16}px"><button type="button" data-more="${parentId}">${items.length - limit}개 더 보기</button></td></tr>`);
        }
      })(roots, 'root');
      tbody.innerHTML = rows.join('') || `<tr><td colspan="${L + cols.length}" class="lh-empty">일치하는 항목이 없습니다.</td></tr>`;
    }

    function rowHtml(n, cols, ms) {
      const open = ms ? (ms.force.has(n.id) || state.open.has(n.id)) : state.open.has(n.id);
      let cells = '';
      for (let lv = 0; lv < L; lv++) {
        if (lv < n.depth) cells += '<td class="lh-lv"></td>';
        else if (lv === n.depth) {
          const tog = n.kids.length
            ? `<button type="button" class="lh-tog" data-id="${n.id}" aria-expanded="${open}">${open ? '▼' : '▶'}</button>`
            : '<span class="lh-tog-sp"></span>';
          cells += `<td class="lh-lv lh-name" title="${esc(n.name)}">${tog}<span>${esc(n.name)}</span></td>`;
        } else if (lv === n.depth + 1 && n.kids.length) cells += '<td class="lh-lv lh-all">전체</td>';
        else cells += '<td class="lh-lv"></td>';
      }
      cells += cols.map(i => `<td class="lh-m"><div class="lh-v">${fmtMetric(n.cur[i], M[i].unit)}</div>${delta(n.cur[i], n.base[i], M[i].unit)}</td>`).join('');
      return `<tr class="lh-depth${n.depth}">${cells}</tr>`;
    }

    root.addEventListener('click', e => {
      const t = e.target.closest('button, th.lh-m');
      if (!t || !root.contains(t)) return;
      if (t.classList.contains('lh-tog')) {
        const id = Number(t.dataset.id);
        if (state.open.has(id)) state.open.delete(id); else state.open.add(id);
        render();
      } else if (t.matches('th.lh-m')) {
        const i = Number(t.dataset.i);
        if (state.sortIdx === i) state.sortDir = -state.sortDir; else { state.sortIdx = i; state.sortDir = -1; }
        render();
      } else if (t.dataset.more) {
        const k = t.dataset.more === 'root' ? 'root' : Number(t.dataset.more);
        state.shown[k] = (state.shown[k] || PAGE) + PAGE;
        render();
      } else if (t.classList.contains('lh-tree-colbtn')) {
        menu.hidden = !menu.hidden;
      } else if (t.dataset.act === 'all' || t.dataset.act === 'none') {
        const on = t.dataset.act === 'all';
        menu.querySelectorAll('input[type=checkbox]').forEach(cb => {
          cb.checked = on; const i = Number(cb.dataset.i);
          if (on) state.visible.add(i); else state.visible.delete(i);
        });
        render();
      } else if (t.dataset.act === 'collapse') {
        state.open.clear(); render();
      }
    });
    menu.addEventListener('change', e => {
      const cb = e.target; const i = Number(cb.dataset.i);
      if (cb.checked) state.visible.add(i); else state.visible.delete(i);
      render();
    });
    document.addEventListener('click', e => {
      if (!menu.hidden && !e.target.closest('.lh-tree-cols')) menu.hidden = true;
    });
    let timer;
    search.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => { state.query = search.value.trim().toLowerCase(); render(); }, 150);
    });
    render();
  };

  window.LHKit = K;
})();
