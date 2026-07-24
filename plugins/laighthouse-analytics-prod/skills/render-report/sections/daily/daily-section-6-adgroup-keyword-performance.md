# Daily Section 6: 광고 그룹 및 키워드 성과

**report_type:** `daily` (항상 포함) — daily-section-1과 동일한 분기 규칙을 따른다.

⚠️ **이 파일은 기존 "daily-section-7-asset-group-table.md"를 대체한다.** 번호가 하나 당겨졌고
(옛 section 5 DTC Revenue 삭제로), naver 분기는 **4단계 트리(채널→캠페인→광고그룹→키워드) →
2단계 트리(광고그룹→키워드)**로 축소 재설계되었다 — 채널/캠페인 레벨은 이제
daily-section-5(캠페인 성과)가 전담하므로, 이 섹션은 그보다 한 단계 더 깊은 광고그룹/키워드
드릴다운만 담당한다.

---

## 분기 A: Google/Meta 브랜드 (변경 없음)

⚠️ "Asset Group"은 Google Performance Max 캠페인 전용 개념이라 naver에는 대응 개념이 없고,
PMax는 키워드 타겟팅 자체가 없는 상품이라 "키워드" 열은 이 분기에는 적용되지 않는다 (에셋그룹
레벨까지만 존재).

**MCP 도구:** `get_sales_by_asset_group_monthly` (start_month=current_month, end_month=current_month, day_offset=target_date.day)

### 필요 데이터
- `sales_by_asset_group`: 에셋그룹 배열
  ```json
  [
    { "media": "Google Ads", "campaign": "Auto_Gen_D2C_BottomFunnel_Rev_PerfMax - High Performing + Other",
      "asset_group": "CITRUS Kiwi overlay pack assets", "impression": 509, "click": 15, "ctr": 2.95,
      "cost": 10, "revenue": 0 }
  ]
  ```
  ※ ROAS 컬럼 없음 (이미지 참조)

### HTML
```html
<!-- DAILY SECTION 6 (Google/Meta): Performance by Asset group -->
<div style="background:white; border:1px solid #e2e8f0; padding:20px 24px; margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div style="font-size:15px; font-weight:700; color:#1e293b;">Performance by Asset group</div>
    <div style="display:flex; align-items:center; gap:8px;">
      <div style="display:flex; align-items:center; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input id="assetSearch" type="text" placeholder="검색" oninput="filterTable('assetTable', this.value)"
          style="border:none; background:transparent; font-size:13px; color:#374151; outline:none; width:100px;">
      </div>
      <select id="assetPageSize" onchange="changePageSize('assetTable', this.value)"
        style="border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; font-size:13px; color:#374151; background:#f8fafc;">
        <option value="10">10개</option><option value="20">20개</option><option value="50">50개</option>
      </select>
    </div>
  </div>
  <div style="overflow-x:auto;">
    <table id="assetTable" style="width:100%; border-collapse:collapse; font-size:13px;">
      <thead>
        <tr style="border-bottom:1px solid #e2e8f0;">
          <th style="padding:10px 12px; text-align:left; color:#64748b; font-weight:500;">Media</th>
          <th style="padding:10px 12px; text-align:left; color:#64748b; font-weight:500;">Campaign</th>
          <th style="padding:10px 12px; text-align:left; color:#64748b; font-weight:500;">Asset Group</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">Impression</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">Click</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">CTR (%)</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">Cost ($)</th>
          <th style="padding:10px 12px; text-align:right; color:#64748b; font-weight:500;">Revenue ($)</th>
        </tr>
      </thead>
      <tbody id="assetTableBody">
        <tr style="border-bottom:1px solid #f1f5f9;">
          <td style="padding:10px 12px; color:#3b82f6; font-weight:500;">{media}</td>
          <td style="padding:10px 12px; color:#3b82f6; max-width:240px;">{campaign}</td>
          <td style="padding:10px 12px; color:#3b82f6;">{asset_group}</td>
          <td style="padding:10px 12px; text-align:right;">{impression}</td>
          <td style="padding:10px 12px; text-align:right;">{click}</td>
          <td style="padding:10px 12px; text-align:right;">{ctr}</td>
          <td style="padding:10px 12px; text-align:right;">{cost}</td>
          <td style="padding:10px 12px; text-align:right;">{revenue}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div id="assetPagination" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:14px; font-size:13px; color:#64748b;"></div>
</div>
```

### Script
```javascript
window.initTable('assetTable');
```

---

## 분기 B: naver 브랜드 ⭐ 재설계 (4단계 → 광고그룹·키워드 2단계 트리)

"광고그룹" 행 앞의 ▸ 아이콘을 누르면 그 그룹에 속한 키워드들이 펼쳐진다. daily-section-5(캠페인
성과)에서 이미 캠페인 단위를 다루므로, 여기서는 각 광고그룹이 어느 캠페인/채널에 속하는지를
**맨 왼쪽 "채널 / 캠페인" 컬럼**으로만 보여주고(2026-07-23: 참고용 표시일 뿐이지만 시인성을
위해 최좌측으로 이동함) 트리 자체는 광고그룹→키워드 2단계로 유지한다.

### MCP 도구 호출: `get_naver_sa_performance_daily` (동일 날짜로 2회 호출, `group_by`만 다름)

```json
// 1) 광고그룹 단위
{ "brand_name": "...", "start_date": "target_date", "end_date": "target_date", "group_by": "ad-group" }
// 2) 키워드 단위
{ "brand_name": "...", "start_date": "target_date", "end_date": "target_date", "group_by": "keyword" }
```

> ⚠️ **`get_naver_group_performance`/`get_naver_keyword_performance`(사전 집계 도구)를 여기 쓰지
> 않는다** — 이 도구들은 그룹/키워드명만 반환하고 **어느 광고그룹에 속하는지 연결 정보가 없다**
> (`get_naver_keyword_performance` 실제 호출 결과 확인, 2026-07-23: `keyword`/`impressions`/
> `clicks`/`ad_cost`/`cpc`/`ctr`/`cpm`/`purchases`/`revenue`/`roas`만 있고 `group_name`/
> `campaign_name` 필드 자체가 없음). 이 섹션처럼 **키워드를 소속 광고그룹 아래에 묶어서** 보여줘야
> 하는 트리에는 쓸 수 없다. 대신 원본 소스인 `get_naver_sa_performance_daily`를 `group_by`만
> 바꿔 호출한다 — 이 도구는 `ad-group`/`keyword` 레벨 응답 모두에 `nvr_media_type`(채널) +
> `campaign_name`(캠페인) + `group_name`(광고그룹, 키워드 레벨에서도 함께 옴)을 항상 반환하므로
> 부모-자식 매칭이 가능하다 (2026-07-22 실제 호출로 확인).
> 응답의 `ctr`/`cpc`/`cvr`/`roas` 필드는 이 레벨 호출에서 전부 `null`로 온다 — 이 스킬이
> `imp`/`click`/`cost_exc_vat`/`gross_conv_cnt`/`gross_conv_amnt`로부터 직접 계산한다.

### 데이터 가공 (이 단계만 예외적으로 허용 — 상위 "데이터 처리 원칙" 참고)

1. **키워드 레벨** 원본에서 `term == "-"`인 행은 제거한다 (키워드 미지정 매칭 트래픽).
2. **키워드 노드**를 `(nvr_media_type, campaign_name, group_name)`으로 그룹핑해, 같은 키를 가진
   **광고그룹 노드**(1번 호출 응답)의 자식으로 붙인다.
3. 각 노드(광고그룹/키워드 모두)에서 비율 지표를 계산한다:
   - `ctr = click / imp × 100`
   - `cpc = cost_exc_vat / click` (click이 0이면 `null`)
   - `cpm = cost_exc_vat / imp × 1000`
   - `roas = gross_conv_amnt / cost_exc_vat × 100` (cost가 0이면 `null`)
   - `광고비 = cost_exc_vat`, `구매건수 = gross_conv_cnt`, `매출 = gross_conv_amnt` 그대로.
4. `nvr_media_type` → 표시 라벨: `BRS`→네이버 브랜드검색, `PLINK`→네이버 파워링크,
   `NVSHOP`→네이버 쇼핑검색.
5. ⚠️ **`ad_cost`(광고비)가 10,000원 미만인 행은 표에서 제외한다** (2026-07-23 추가) — 광고그룹
   노드와 키워드 노드 각각에 독립적으로 적용한다 (부모 그룹이 10,000원 이상이어도 특정 키워드가
   10,000원 미만이면 그 키워드만 빠지고, 반대로 그룹 자체가 10,000원 미만이면 그 그룹과 모든
   하위 키워드가 통째로 빠진다). 필터링은 3번(비율 지표 계산) 이후, 최종 트리를 만들기 전에
   적용한다.
   - 키워드는 개별 단가가 작아 이 기준을 넘는 경우가 드물다 — 필터링 후 특정 광고그룹의 키워드가
     0개가 되면, 그 광고그룹 행은 (10,000원 기준을 만족해 자체는 표에 남아 있더라도) 펼치기
     아이콘(▸) 없이 렌더링한다 (펼쳐도 보여줄 키워드가 없으므로).
6. 위 1~5단계는 전부 기계적 매칭·합산·나눗셈·필터링이며 raw 값 자체를 임의로 보정·추정하지
   않으므로 상위 "데이터 처리 원칙"과 충돌하지 않는다.

### 응답 데이터 구조 (가공 후, 렌더링에 쓰는 최종 트리 형태)

```json
{
  "adgroup_hierarchy": [
    {
      "level": "group", "group": "02_분유(스토어)", "channel_label": "네이버 브랜드검색", "campaign": "00_통합(BS)_MO",
      "impressions": 1315, "clicks": 206, "ad_cost": 133321, "cpc": 647.19, "ctr": 15.66, "cpm": 101.4,
      "purchases": 81, "revenue": 7204020, "roas": 5403.6,
      "children": [
        { "level": "keyword", "keyword": "아기사랑수",
          "impressions": 320, "clicks": 41, "ad_cost": 26100, "cpc": 636.6, "ctr": 12.81, "cpm": 81.6,
          "purchases": 15, "revenue": 1230000, "roas": 4712.6 }
      ]
    }
  ]
}
```

### HTML

```html
<!-- DAILY SECTION 6 (naver): 광고 그룹 및 키워드 성과 -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title" style="margin-bottom:0;">광고 그룹 및 키워드 성과</div>
    <div style="display:flex; align-items:center; gap:8px;">
      <div style="display:flex; align-items:center; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; gap:6px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input type="text" placeholder="검색" oninput="filterHierarchyTable(this.value)"
          style="border:none; background:transparent; font-size:13px; color:#374151; outline:none; width:100px;">
      </div>
      <select onchange="changeHierarchyPageSize(this.value)" style="border:1px solid #e2e8f0; border-radius:6px; padding:6px 10px; font-size:13px; color:#374151; background:#f8fafc;">
        <option value="10">10개</option><option value="20">20개</option><option value="50">50개</option>
      </select>
    </div>
  </div>

  <div style="overflow-x:auto;">
    <table id="hierarchyTable">
      <thead>
        <tr>
          <th style="min-width:110px;">채널 / 캠페인</th>
          <th style="min-width:160px;">광고그룹</th>
          <th style="min-width:140px;">키워드</th>
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
      <tbody id="hierarchyTableBody">
        <!-- adgroup_hierarchy 배열을 순회하며 아래 2단계 행 패턴 반복 -->
        <!-- 광고그룹 행 (기본 펼침 O, data-depth=0) -->
        <tr class="h-row" data-depth="0" data-node-id="{group_node_id}" data-parent-id="">
          <td style="color:#94a3b8; font-size:12px;">{channel_label} / {campaign}</td>
          <td>
            <span class="h-toggle" onclick="toggleHierarchyRow('{group_node_id}')" style="cursor:pointer; display:inline-block; width:16px;">▸</span>
            {group}
          </td>
          <td style="color:#94a3b8;">전체</td>
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
        <!-- 키워드 행 (기본 숨김, data-depth=1, data-parent-id=광고그룹 node id, 토글 아이콘 없음) -->
        <tr class="h-row" data-depth="1" data-node-id="{keyword_node_id}" data-parent-id="{group_node_id}" style="display:none;">
          <td></td>
          <td></td>
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
  <div id="hierarchyPagination" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:14px; font-size:13px; color:#64748b;"></div>
</div>
```

### Script

```javascript
// 광고그룹(depth=0) 단위로 페이지네이션, 키워드(depth=1)는 그 안에서 펼치기/접기만 함
window._hierarchyExpanded = window._hierarchyExpanded || {};
window._hierarchyState = window._hierarchyState || { allGroupRows: [], page: 1, pageSize: 10, keyword: '' };

window.toggleHierarchyRow = function(nodeId) {
  const isExpanded = !!window._hierarchyExpanded[nodeId];
  window._hierarchyExpanded[nodeId] = !isExpanded;
  const icon = document.querySelector(`[data-node-id="${nodeId}"] .h-toggle`);
  if (icon) icon.textContent = isExpanded ? '▸' : '▾';
  document.querySelectorAll(`[data-parent-id="${nodeId}"]`).forEach(row => {
    row.style.display = isExpanded ? 'none' : '';
  });
};

window.collapseHierarchyChildren = function(nodeId) {
  window._hierarchyExpanded[nodeId] = false;
  const icon = document.querySelector(`[data-node-id="${nodeId}"] .h-toggle`);
  if (icon) icon.textContent = '▸';
  document.querySelectorAll(`[data-parent-id="${nodeId}"]`).forEach(row => { row.style.display = 'none'; });
};

window.filterHierarchyTable = function(keyword) {
  const state = window._hierarchyState;
  state.keyword = keyword.toLowerCase();
  state.page = 1;
  window.renderHierarchyPage();
};

window.changeHierarchyPageSize = function(size) {
  const state = window._hierarchyState;
  state.pageSize = parseInt(size);
  state.page = 1;
  window.renderHierarchyPage();
};

window.renderHierarchyPage = function() {
  const state = window._hierarchyState;
  const allGroups = state.allGroupRows || [];
  const keyword = state.keyword || '';
  const pageSize = state.pageSize || 10;
  const page = state.page || 1;

  // 검색은 광고그룹 행 자신의 텍스트(광고그룹명 + 채널/캠페인 참고 컬럼) 기준으로만 필터링한다
  // (하위 키워드까지 검색하려면 해당 그룹을 직접 펼쳐서 확인한다)
  const filtered = keyword ? allGroups.filter(g => g.textContent.toLowerCase().includes(keyword)) : allGroups;
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const start = (page - 1) * pageSize;
  const pageGroups = filtered.slice(start, start + pageSize);
  const pageGroupIds = new Set(pageGroups.map(g => g.getAttribute('data-node-id')));

  allGroups.forEach(g => {
    const nodeId = g.getAttribute('data-node-id');
    g.style.display = pageGroupIds.has(nodeId) ? '' : 'none';
    // 페이지가 바뀔 때마다 모든 그룹은 접힌 상태로 리셋한다 (이전 페이지의 펼침 상태가 남지 않도록)
    window.collapseHierarchyChildren(nodeId);
  });

  const pgEl = document.getElementById('hierarchyPagination');
  if (pgEl) {
    pgEl.innerHTML = '';
    const prev = document.createElement('button');
    prev.textContent = '‹'; prev.disabled = page <= 1;
    prev.style.cssText = 'border:1px solid #e2e8f0;background:white;padding:4px 10px;border-radius:4px;cursor:pointer;';
    prev.onclick = () => { state.page = page - 1; window.renderHierarchyPage(); };
    pgEl.appendChild(prev);
    const maxButtons = 6;
    let startPage = Math.max(1, page - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);
    startPage = Math.max(1, endPage - maxButtons + 1);
    for (let i = startPage; i <= endPage; i++) {
      const btn = document.createElement('button');
      btn.textContent = i;
      btn.style.cssText = `border:1px solid ${i===page?'#3b82f6':'#e2e8f0'};background:${i===page?'#3b82f6':'white'};color:${i===page?'white':'#374151'};padding:4px 10px;border-radius:4px;cursor:pointer;`;
      btn.onclick = ((_i) => () => { state.page = _i; window.renderHierarchyPage(); })(i);
      pgEl.appendChild(btn);
    }
    const next = document.createElement('button');
    next.textContent = '›'; next.disabled = page >= totalPages;
    next.style.cssText = 'border:1px solid #e2e8f0;background:white;padding:4px 10px;border-radius:4px;cursor:pointer;';
    next.onclick = () => { state.page = page + 1; window.renderHierarchyPage(); };
    pgEl.appendChild(next);
  }
};

window.initHierarchyTable = function() {
  const tbody = document.getElementById('hierarchyTableBody');
  if (!tbody) return;
  const groupRows = Array.from(tbody.querySelectorAll('.h-row[data-depth="0"]'));
  window._hierarchyState = { allGroupRows: groupRows, page: 1, pageSize: 10, keyword: '' };
  window.renderHierarchyPage();
};

window.initHierarchyTable();
```

## 렌더링 규칙 (분기 B)
- 광고그룹 정렬: 매출 내림차순 (`-revenue`), 동률이면 광고비 내림차순. 키워드도 같은 그룹 안에서
  동일하게 정렬.
- `cpc`가 `null`(클릭 0)이면 "-" 표시, `roas`가 `null`(광고비 0)이면 "-" 표시.
- 광고그룹 하나에 키워드가 많을 수 있으므로, 매출 상위 20개까지만 자식으로 붙이고 나머지는
  "외 {N}개 키워드" 안내 행으로 대체한다.
- ⚠️ **광고비(`ad_cost`) 10,000원 미만인 행은 광고그룹/키워드 레벨 모두에서 표에 나타나지
  않는다** (데이터 가공 5번 참고, 2026-07-23 추가). 필터링 후 광고그룹이 하나도 남지 않으면
  "이번 기간 10,000원 이상 집행된 광고그룹이 없음" 안내 카드로 대체한다 (빈 테이블로 남기지
  않음).
- 이 섹션은 daily-section-5(캠페인 성과)와 같은 3개 SA 채널(브랜드검색/파워링크/쇼핑검색)만
  다룬다 — GFA 채널은 광고그룹/키워드 구조가 없다.
- ⚠️ **페이지네이션 (2026-07-23 추가, 우측 상단 "↻ 새로고침" 버튼을 대체)**: 한 번에 표시되는
  **광고그룹(depth=0) 행 개수**를 10/20/50개 중 선택하는 드롭다운을 검색창 옆에 둔다 (기본값
  10개). daily-section-5(캠페인 성과)의 페이지네이션과 동일한 스타일/동작이다. 페이지네이션은
  광고그룹 단위로만 동작한다 — 키워드(depth=1) 행은 페이지 계산에 포함되지 않고, 화면에 보이는
  광고그룹을 펼칠 때만 그 아래에 추가로 나타난다.
  - 전체 광고그룹 개수가 선택된 페이지 크기를 초과하면 표 하단에 페이지 번호를 표시한다
    (초과하지 않으면 페이지네이션 영역을 비워둔다 — daily-section-5와 동일한 동작).
  - 페이지를 전환하면 이전 페이지에서 펼쳐뒀던 광고그룹은 전부 다시 접힌 상태로 리셋된다.
  - 검색은 **광고그룹 행 자신의 텍스트(광고그룹명 + 좌측 "채널 / 캠페인" 컬럼)만** 대상으로
    한다 — 하위 키워드명까지는 검색하지 않는다(2026-07-23: 페이지네이션 도입으로 검색 로직을
    daily-section-5와 통일하기 위해 단순화함). 특정 키워드를 찾으려면 해당 광고그룹을 직접
    펼쳐서 확인해야 한다.
  - ~~"↻ 새로고침" 버튼~~은 제거되었다 — 페이지네이션이 도입되면서 "전체 다시 보기"는 검색어를
    지우고 1페이지로 돌아가는 것으로 대체된다.

