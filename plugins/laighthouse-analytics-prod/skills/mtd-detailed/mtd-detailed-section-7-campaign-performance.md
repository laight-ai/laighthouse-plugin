# Breezm MTD Section 7: 캠페인 성과 (Campaign Performance)

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 매체-캠페인 단위, MTD
(월초~target_date).

## MCP 도구 호출: `get_ad_performance_daily_table` × 4 (google/meta/naver/airbridge, 각각 `group_by: "campaign"`)

```json
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "google", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "meta", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "naver", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "airbridge", "group_by": "campaign" }
```

- **매체별로 4번 나눠 부른다 — `media`를 생략하지 않는다.** `group_by:"campaign"`처럼 행
  granularity가 캠페인 단위인 호출은, `total`/`media` 같은 저(低)카디널리티 `group_by`와
  달리 `media`를 생략하면 응답에 불필요한 매체의 행까지 전부 섞여 응답 크기가 매체 수만큼
  곱해진다 — MTD처럼 날짜 범위가 길면(월초~target_date, 최대 한 달치) 캠페인 수가 많은
  브랜드에서 응답이 모델 컨텍스트에 담기 어려울 정도로 커질 수 있다(실측: 같은 도구 계열의
  `group_by:"ad"` 호출이 7일치만으로도 76만자를 넘긴 사례가 있었다). 이 섹션은 캠페인 단위
  granularity이므로 매체별 개별 호출로 응답을 각 매체 범위 안으로 좁게 유지한다.
- ⚠️ `campaign-type` 금지 — 넣으면 airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 문자열 `"campaign"` 그대로 보낸다.

## 필요 데이터 (캠페인별 집계)

**매체 지표** (google/meta/naver 각 응답에서, 캠페인별로 일별 행을 합산):
- `노출` = `impression` 합 / `클릭` = `click` 합 / `광고비` = `cost` 합
- `CTR` = 클릭 ÷ 노출 × 100 (노출 0이면 N/A)

**airbridge 지표** (airbridge 응답에서 캠페인별 합산):
- `매출` = `airbridge_revenue` 합 / `예약 완료` = `reservation` 합

⚠️ **응답 행이 많을 때(캠페인 수가 많거나 기간이 길 때)는 SKILL.md의 「실행 방식 절대
지침」에 추가된 Bash 예외를 따른다** — 각 매체 응답을 받은 즉시 파일로 남기지 않는 1회성
Bash 명령(grep/awk/jq 등)으로 캠페인별 합산·정렬까지 마친 뒤, 그 결과 소표만 컨텍스트에
올린다. 원본 행을 손으로 옮겨 적거나 머릿속으로 합산하지 않으며, 절대 근사치로 채우지 않는다.

**조인**: 캠페인 이름 **정확 일치(exact match)**로 매체 행과 airbridge 행을 잇는다.
- 매체 쪽에만 있는 캠페인 → 매출/예약 완료 칸은 `-`
- airbridge 쪽에만 있는(매칭 실패) 캠페인 → 표에 포함하지 않는다 (개별 캠페인명·매출을 각주에
  나열하지 않는다 — 아래 고정 안내 문구로 갈음한다).

**파생 지표**:
- `예약 완료 CPA` = 광고비 ÷ 예약 완료 (예약 완료 0이면 N/A)
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비 0이면 N/A)

## HTML

```html
<!-- BREEZM MTD SECTION 7: 캠페인 성과 (CAMPAIGN PERFORMANCE) -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title">캠페인 성과 ({M}월 1일~{M}월 {D}일)</div>
    <input id="mtdCampaignSearch" style="border:1px solid #e2e8f0; border-radius:8px; padding:6px 12px; font-size:12px; color:#374151; width:180px;" placeholder="검색" oninput="window.__mtdCampaignSearch && window.__mtdCampaignSearch(this.value)">
  </div>
  <div style="overflow-x:auto;">
    <table>
      <thead><tr>
        <th style="text-align:center; border-right:1px solid #e2e8f0;">매체</th><th style="text-align:center; border-right:1px solid #e2e8f0;">캠페인</th><th style="text-align:center;">노출</th><th style="text-align:center;">클릭</th><th style="text-align:center;">CTR</th>
        <th style="text-align:center;">광고비</th><th style="text-align:center;">매출</th><th style="text-align:center;">예약 완료</th><th style="text-align:center;">예약 완료 CPA</th><th style="text-align:center;">ROAS</th>
      </tr></thead>
      <tbody id="mtdCampaignTableBody">
        <!-- 실제 행은 JS가 {MTD_CAMPAIGN_ROWS} 배열에서 검색어로 거른 뒤 10개씩 잘라 여기
             채운다. 정적 예시 행을 직접 넣지 않는다 — 아래 "필요 데이터"에서 각 행을 이미
             완성된 <tr>...</tr> HTML 문자열 + 검색용 텍스트로 미리 만들어 배열에 담아야
             한다 (광고비 내림차순). 각 행의 형식은 아래와 같다: -->
        <!--
        <tr>
          <td style="border-right:1px solid #e2e8f0;">{channel}</td><td style="text-align:left; border-right:1px solid #e2e8f0;">{campaign}</td><td>{노출}</td><td>{클릭}</td><td>{CTR}</td>
          <td>{광고비}</td><td>{매출}</td><td>{예약_완료}</td><td>{CPA}</td><td>{ROAS}</td>
        </tr>
        -->
      </tbody>
    </table>
  </div>
  <!-- 페이지네이션: 10개씩, 페이지 크기 변경 드롭다운 없음. 버튼은 JS가 동적으로 그린다. -->
  <div id="mtdCampaignPager" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:16px;"></div>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">
    * 데이터 수집 체계에 따라, 일부 캠페인이 표시되지 않을 수 있습니다.
  </p>
</div>
```

## Script

```javascript
// Breezm MTD Section 7: 캠페인 성과 표 — 검색 + 페이지네이션
// 정적 HTML 한 번에 생성되는 보고서라 "검색창 입력 → 서버에 다시 물어본다"나 "페이지 버튼
// 클릭 → 서버에서 다른 페이지를 받아온다" 방식은 동작하지 않는다. 전체 행을 미리
// <tr>...</tr> HTML 문자열 + 검색용 텍스트로 만들어 심어두고, 검색어 입력과 페이지 버튼
// 클릭 모두 이 스크립트가 클라이언트에서 직접 처리한다.
(function(){
  const rows = {MTD_CAMPAIGN_ROWS};
  // rows: [{ search: "매체명 캠페인명" (소문자, 부분일치 대상), html: "<tr>...</tr>" }, ...]
  // 광고비 내림차순으로 이미 정렬되어 있어야 한다. search 필드는 매체명과 캠페인명을
  // 소문자로 이어붙인 문자열이다 (예: "naver ads 브랜드검색/mo_2025").

  const pageSize = 10;
  const tbody = document.getElementById('mtdCampaignTableBody');
  const pager = document.getElementById('mtdCampaignPager');
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
    return `<button ${disabled} style="border:1px solid #e2e8f0; border-radius:6px; width:28px; height:28px; font-size:12px; cursor:${opts.disabled?'default':'pointer'}; ${active}" onclick="window.__mtdCampaignGoto && window.__mtdCampaignGoto(${page})">${label}</button>`;
  }

  function render() {
    const list = filteredRows();
    const totalPages = Math.max(1, Math.ceil(list.length / pageSize));
    currentPage = Math.min(Math.max(1, currentPage), totalPages);
    const start = (currentPage - 1) * pageSize;
    const pageRows = list.slice(start, start + pageSize);

    tbody.innerHTML = pageRows.length
      ? pageRows.map(r => r.html).join('')
      : `<tr><td colspan="10" style="text-align:center; color:#94a3b8; padding:20px;">검색 결과가 없습니다.</td></tr>`;

    let html = pagerButton('‹', currentPage - 1, { disabled: currentPage === 1 });
    for (let i = 1; i <= totalPages; i++) {
      html += pagerButton(String(i), i, { active: i === currentPage });
    }
    html += pagerButton('›', currentPage + 1, { disabled: currentPage === totalPages });
    pager.innerHTML = html;
  }

  window.__mtdCampaignGoto = function(page){ currentPage = page; render(); };
  window.__mtdCampaignSearch = function(value){
    currentTerm = (value || '').trim().toLowerCase();
    currentPage = 1;
    render();
  };

  render();
})();
```

## 렌더링 규칙
- 카드 제목의 `{M}`/`{D}`는 데이터 기간에 맞춰 채운다 — 둘 다 `target_date` 기준이며, 시작은
  항상 당월 1일이므로 `{M}월 1일~{M}월 {D}일` 형식에서 두 `{M}`은 같은 값(당월)이고 `{D}`는
  `target_date`의 일(day)이다 (예: 기준일이 7월 15일이면 "7월 1일~7월 15일").
- 표의 첫 열은 "매체"로 표기하고, 두 번째 열은 "캠페인"으로 표기한다. **매체 열과 캠페인
  열 사이, 캠페인 열과 노출 열 사이에 각각 세로 구분선**(`border-right:1px solid #e2e8f0;`)
  을 넣는다. 캠페인 열은 이름이 길 수 있으므로 **좌측 정렬**한다(매체 열과 그 외 지표
  열은 중앙 정렬 그대로 유지한다).
- **모든 헤더 `<th>`에 `text-align:center`를 명시한다** — 공통 스타일시트의 `th` 기본값이
  좌측 정렬(`text-align:left`)이라, 명시하지 않으면 지표 이름이 좌측에 붙어 보인다(캠페인
  열 헤더도 마찬가지로 중앙 정렬한다 — 좌측 정렬은 헤더가 아니라 본문 셀에만 적용한다).
- **검색과 페이지네이션은 실제로 작동해야 한다.** 서버 없이 한 번에 생성되는 정적 HTML이므로,
  "첫 10개만 적어넣고 검색창·페이지 버튼은 장식으로 둔다" 방식은 **금지**한다. 필터·정렬을
  마친 전체 캠페인을 각각 완성된 `<tr>...</tr>` HTML 문자열 + 검색용 텍스트(매체명+캠페인명,
  소문자)로 만들어 `{MTD_CAMPAIGN_ROWS}` 배열에 전부 담고, 위 Script가 검색어로 거른 뒤
  10개씩 잘라 보여주게 한다. 검색은 매체/캠페인 이름 **부분일치**(대소문자 무관)로 동작하며,
  검색어가 바뀌면 1페이지로 되돌아간다. 페이지 크기를 바꾸는 드롭다운은 만들지 않는다.
- 각주는 위 HTML에 적힌 고정 문구를 그대로 쓴다 — 매칭 실패한 캠페인명이나 매출액을 개별
  나열하지 않는다.
- 비율/ROAS/CTR은 % 소수점 1자리, 금액(광고비/매출/예약 완료 CPA)은 천 단위 콤마 원화, N/A는 문자 그대로.
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 캠페인명을 정규화/부분일치로 "맞춰서" 조인하지 않는다 — 정확 일치만 쓰고, 나머지는 위 조인
  규칙을 따른다.