# Breezm Creative Section 5: 최근 7일 소재 단위 누적 성과

**report_type:** `creative-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). **메타
(Meta Ads)만 대상**이다. 기준일(target_date)을 포함한 **최근 7일을 통째로 합산**해서,
매체/캠페인/광고그룹/광고(소재) 단위로 노출·클릭·CTR·광고비·매출·예약 완료·예약 완료 CPA·ROAS를
한 표에 보여준다. section-1(최우수 소재)·section-3/4(일별 차트)와 마찬가지로 **날짜별
비교가 아니라 7일 전체를 하나로 합친 누적 값**이다. ⚠️ 파일명의 "daily"는 이 보고서가
매일 갱신되는 데일리 보고서라는 맥락을 가리키는 것이며, **이 섹션 자체는 날짜별(일별)
데이터가 아니라 7일 누적값이다** — 혼동하지 않는다.

## MCP 도구 호출: 신규 호출 없음 — section-1의 공유 응답을 그대로 재사용

이 섹션은 section-1(최우수 소재)이 이미 호출한 아래 두 응답을 그대로 재사용한다 — **다시
호출하지 않는다**:

```json
{ "brand_name": "breezm", "media": "meta", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
```
```json
{ "brand_name": "breezm", "media": "airbridge", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
```

(`media="meta"`/`media="airbridge"` 각 1회 호출. 참고: section-1은 이 응답에서 **랭킹
1·2위만** 뽑아 썼지만, 이 섹션은 **모든 소재를 전부** 표에 나열한다는 점이 다르다 — 같은
원본 데이터를 다른 방식으로 가공하는 것이다.)

## 필요 데이터 (소재별, 최근 7일 합산 — section-1과 동일한 방식)

**매체 지표** (`media="meta"` 응답을 소재(`campaign_name`+`asset_group`+`ad_name`) 단위로
7일 합산):
- `노출` = `impression` 합 / `클릭` = `click` 합 / `광고비` = `cost` 합
- `CTR` = 클릭 ÷ 노출 × 100 (노출 0이면 N/A)

**airbridge 지표** (`media="airbridge"` 응답을 같은 소재 단위로 7일 합산):
- `매출` = `airbridge_revenue` 합 / `예약 완료` = `reservation` 합

**조인**: `campaign_name`+`asset_group`+`ad_name` **세 필드 모두 정확히 일치**해야 같은
소재로 본다 (section-1과 동일한 조인 규칙).
- 매체 쪽에만 있는 소재(airbridge 매칭 실패) → `매출`/`예약 완료`/`예약 완료 CPA`/`ROAS` 칸은 `-`.
- airbridge 쪽에만 있는(매체 쪽에 없는) 소재 → 노출/클릭/광고비를 알 수 없으므로 표에
  포함하지 않는다.

**파생 지표**:
- `예약 완료 CPA` = 광고비 ÷ 예약 완료 (예약 완료 0/없음이면 `-`)
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비 0이면 `-`)

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다(section-1에서 이미 호출했으므로 여기서는
해당 사항 없음 — 재사용만 확인).

## HTML

```html
<!-- BREEZM CREATIVE SECTION 5: 최근 7일 소재 단위 누적 성과 -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title">최근 7일 소재 단위 누적 성과</div>
    <input id="assetPerfSearch" style="border:1px solid #e2e8f0; border-radius:8px; padding:6px 12px; font-size:12px; color:#374151; width:180px;" placeholder="검색" oninput="window.__assetPerfSearch && window.__assetPerfSearch(this.value)">
  </div>
  <div style="overflow-x:auto;">
    <table style="border-collapse:collapse; font-size:12.5px; table-layout:fixed; width:auto;">
      <thead>
        <tr>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; white-space:nowrap; width:90px;">매체</th>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; width:260px;">캠페인</th>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; width:200px;">광고그룹</th>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; width:200px;">광고</th>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; white-space:nowrap; width:150px;">노출</th>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; white-space:nowrap; width:150px;">클릭</th>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; white-space:nowrap; width:150px;">CTR</th>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; white-space:nowrap; width:150px;">광고비</th>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; white-space:nowrap; width:150px;">매출</th>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; white-space:nowrap; width:150px;">예약 완료</th>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; white-space:nowrap; width:150px;">예약 완료 CPA</th>
          <th style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; background:#f8fafc; white-space:nowrap; width:150px;">ROAS</th>
        </tr>
      </thead>
      <tbody id="assetPerfTableBody">
        <!-- 실제 행은 JS가 {CREATIVE_ASSET_ROWS} 배열(검색어로 거른 뒤 10개씩)에서 채운다.
             정적 예시 행을 직접 넣지 않는다 — 각 행을 이미 완성된 <tr>...</tr> HTML 문자열 +
             검색용 텍스트(매체명+캠페인명+광고그룹명+광고명, 소문자)로 미리 만들어 배열에
             담아야 한다 (7일 합산 광고비 내림차순). ⚠️ **캠페인/광고그룹/광고 이름은 절대
             잘려서 표시되면 안 된다** — `-webkit-line-clamp`나 `text-overflow:ellipsis`
             같은 "말줄임표로 자르는" 방식은 쓰지 않는다 — 이름이 2줄을 넘으면 뒷부분이 통째로
             사라진다. 대신 넉넉한 고정폭 +
             `overflow-wrap:break-word`로 하이픈/언더스코어 등 자연스러운 경계에서
             줄바꿈되게 하고, 2줄을 넘어가면 3줄 이상으로 자연스럽게 넘치도록 둔다(잘리지
             않는 것이 줄 수를 맞추는 것보다 항상 우선한다). 각 행의 html 형식은 아래와
             같다: -->
        <!--
        <tr>
          <td style="border:1px solid #e2e8f0; padding:10px 14px; text-align:center; white-space:nowrap;">{media}</td>
          <td style="border:1px solid #e2e8f0; padding:10px 14px; text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4;">{campaign}</td>
          <td style="border:1px solid #e2e8f0; padding:10px 14px; text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4;">{asset_group}</td>
          <td style="border:1px solid #e2e8f0; padding:10px 14px; text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4;">{ad_name}</td>
          <td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{노출}</td>
          <td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{클릭}</td>
          <td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{CTR}</td>
          <td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{광고비}</td>
          <td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{매출}</td>
          <td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{예약_완료}</td>
          <td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{CPA}</td>
          <td style="border:1px solid #e2e8f0; padding:12px 14px; text-align:center; white-space:nowrap;">{ROAS}</td>
        </tr>
        -->
      </tbody>
    </table>
  </div>
  <div id="assetPerfPager" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:16px;"></div>
</div>
```

## Script

```javascript
// Breezm Creative Section 5: 소재 단위 누적 성과 표 — 검색 + 페이지네이션
// 정적 HTML 한 번에 생성되는 보고서라 "검색창 입력/페이지 버튼 클릭 → 서버에 다시 물어본다"
// 방식은 동작하지 않는다. 전체 행을 미리 <tr>...</tr> HTML 문자열 + 검색용 텍스트로 만들어
// 심어두고, 검색·페이지 전환 모두 이 스크립트가 클라이언트에서 직접 처리한다.
(function(){
  const rows = {CREATIVE_ASSET_ROWS};
  // rows: [{ search: "매체명 캠페인명 광고그룹명 광고명" (소문자), html: "<tr>...</tr>" }, ...]
  // 7일 합산 광고비 내림차순으로 이미 정렬되어 있어야 한다.

  const pageSize = 10;
  const tbody = document.getElementById('assetPerfTableBody');
  const pager = document.getElementById('assetPerfPager');
  if (!tbody || !pager) return;

  let currentTerm = '';
  let currentPage = 1;

  function filteredRows() {
    if (!currentTerm) return rows;
    return rows.filter(r => r.search.includes(currentTerm));
  }

  function pagerButton(label, page, opts) {
    opts = opts || {};
    const disabled = opts.disabled ? 'disabled' : '';
    const active = opts.active
      ? 'background:#3b82f6; border-color:#3b82f6; color:white;'
      : 'background:white; border-color:#e2e8f0; color:#64748b;';
    return `<button ${disabled} style="border:1px solid #e2e8f0; border-radius:6px; width:28px; height:28px; font-size:12px; cursor:${opts.disabled?'default':'pointer'}; ${active}" onclick="window.__assetPerfGoto && window.__assetPerfGoto(${page})">${label}</button>`;
  }

  function render() {
    const list = filteredRows();
    const totalPages = Math.max(1, Math.ceil(list.length / pageSize));
    currentPage = Math.min(Math.max(1, currentPage), totalPages);
    const start = (currentPage - 1) * pageSize;
    const pageRows = list.slice(start, start + pageSize);

    tbody.innerHTML = pageRows.length
      ? pageRows.map(r => r.html).join('')
      : `<tr><td colspan="12" style="text-align:center; color:#94a3b8; padding:20px;">검색 결과가 없습니다.</td></tr>`;

    let html = pagerButton('‹', currentPage - 1, { disabled: currentPage === 1 });
    for (let i = 1; i <= totalPages; i++) {
      html += pagerButton(String(i), i, { active: i === currentPage });
    }
    html += pagerButton('›', currentPage + 1, { disabled: currentPage === totalPages });
    pager.innerHTML = html;
  }

  window.__assetPerfGoto = function(page){ currentPage = page; render(); };
  window.__assetPerfSearch = function(value){
    currentTerm = (value || '').trim().toLowerCase();
    currentPage = 1;
    render();
  };

  render();
})();
```

## 렌더링 규칙
- **검색과 페이지네이션은 실제로 작동해야 한다.** 서버 없이 한 번에 생성되는 정적 HTML이므로,
  "첫 10개만 적어넣고 검색창·나머지 페이지는 장식으로 둔다" 방식은 **금지**한다. 필터·정렬을
  마친 전체 행을 각각 완성된 `<tr>...</tr>` HTML 문자열 + 검색용 텍스트(매체명+캠페인명+
  광고그룹명+광고명, 소문자)로 만들어 `{CREATIVE_ASSET_ROWS}` 배열에 전부 담고, 위 Script가
  검색어로 거른 뒤 10개씩 잘라 보여주게 한다. 검색은 **부분일치**(대소문자 무관)로 동작하며,
  검색어가 바뀌면 1페이지로 되돌아간다. 페이지당 10개, 하단에 페이지 번호/이동 버튼만
  표시한다. 페이지 크기를 바꾸는 드롭다운은 만들지 않는다.
- **정렬 순서**: 7일 합산 광고비 내림차순으로 전체 소재를 한 줄로 정렬한다.
- 매체/캠페인/광고그룹/광고 열은 좌측 정렬, 그 외 모든 지표 값은 중앙 정렬한다.
- **지표 열(노출/클릭/CTR/광고비/매출/예약 완료/예약 완료 CPA/ROAS)에는 `white-space:nowrap`을 반드시
  적용한다** — "예약 완료"처럼 짧은 한글 헤더도 열이 좁아지면 한 글자씩 세로로 줄바꿈되는
  문제가 발생할 수 있다.
- **식별열(매체/캠페인/광고그룹/광고)은 예외다.** ⚠️ **이름은 절대 잘려서 표시되면 안
  된다** — `-webkit-line-clamp`나 `text-overflow:ellipsis` 같은 "말줄임표로 자르는" 방식은
  **쓰지 않는다** — 2줄이 넘는 이름의 뒷부분이 통째로 사라질 수 있다. 이름이 안 잘리는 것은
  다른 report_type들에서도 이미 확정된 공통 원칙이다. 대신 다음을 따른다:
  1. 넉넉한 **고정 너비**(매체 90px, 캠페인 260px, 광고그룹/광고 각 200px)를 준다.
  2. `white-space:normal; overflow-wrap:break-word;`로 하이픈/언더스코어/공백 등 자연스러운
     경계에서 줄바꿈되게 한다(`word-break:break-word`는 쓰지 않는다 — 아무 글자에서나
     강제로 끊어서 이름이 세로로 길게 쪼개지는 문제가 생길 수 있다).
  3. 이름이 **최대 두 줄 정도로 자연스럽게 들어가는 것을 기대**하지만, 정확히 2줄로 맞추는
     것 자체가 목표는 아니다 — 두 줄을 넘어가면 억지로 줄이지 말고 3줄 이상으로 자연스럽게
     넘치도록 둔다("잘리지 않는 것"이 "줄 수를 맞추는 것"보다 항상 우선한다).
- **`<table>`에는 `table-layout:fixed`를 반드시 준다** — `auto`(기본값)에서는 `width`가
  힌트에 불과해서 `nowrap`인 지표 열들이 공간을 다 차지하고 식별 열만 계속 짜부라지는
  문제가 생길 수 있다(이 문제를 막기 위해 지표 열(노출~ROAS) 8개 전부에도 `width:150px`를
  명시했다).
- ⚠️ **`<table>`에 `width:auto`도 반드시 같이 명시한다** — SKILL.md 공통 스타일시트의
  `table { width: 100%; ... }`가 전역으로 적용되는데, 개별 `<table>`에서 `width`를 따로
  지정하지 않으면 이 100%가 그대로 상속된다. **`table-layout:fixed`와 `width:100%`를 함께
  쓰면, 지정한 각 열의 픽셀 값이 절대값이 아니라 "100%를 나눠 갖는 비율"로 취급된다** —
  그래서 지표 열 폭을 아무리 늘려도 카드 폭(100%)에 맞춰 다시 비율로 쪼그라들어서 표가
  겹쳐 보이는 문제가 생길 수 있다. `width:auto`를 명시하면 테이블이 선언한 열 폭들의 합만큼
  실제로 넓어지고, 카드보다 넓어진 부분은 `overflow-x:auto`가 가로 스크롤로 처리한다.
- 열이 넓어져서 표 전체가 카드 폭을 넘어가면(자연스러운 상황) 카드를 감싸는
  `overflow-x:auto` 컨테이너가 가로 스크롤을 대신 처리한다.
- 비율(CTR/ROAS)은 % 소수점 1~2자리, 금액(광고비/매출/예약 완료 CPA)은 천 단위 콤마 원화, 노출/클릭/
  예약 완료는 정수, 값이 없으면 `-`.
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 소재명을 정규화/부분일치로 "맞춰서" 조인하지 않는다 — `campaign_name`+`asset_group`+
  `ad_name` 세 필드 정확 일치만 쓴다.