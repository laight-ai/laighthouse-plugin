# Breezm Monthly Section 5: 캠페인 성과 비교 (M-1 vs M0)

**report_type:** `monthly-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 매체-캠페인
단위로 **전월(M-1)과 당월(M0)**을 비교한다 — `daily`의 section-4(캠페인 성과, D-1 vs D-0)와
같은 캠페인 단위 표이지만, 비교 시점이 하루가 아니라 한 달이다(section-4의 매체 성과 비교와
같은 M-1 vs M0 방식을 캠페인 단위로 적용한 버전).

## MCP 도구 호출: `get_ad_performance_monthly_table` × 1 (`media` 생략, 전월 vs 당월,
`day_offset`, `group_by: "campaign"`)

```json
{ "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "group_by": "campaign", "day_offset": "target_date.day" }
```

- **`media` 파라미터를 생략한다** — 예전에는 매체별로 4번(`google`/`meta`/`naver`/`airbridge`
  각각 `group_by:"campaign"`) 나눠 불렀지만, `media`를 생략하면 이 도구가 google/meta/naver/
  airbridge(및 이 보고서가 쓰지 않는 다른 매체)를 **한 번의 호출로 전부** `group_by:"campaign"`
  기준으로 반환한다 — 매체별 4호출과 동일한 행 구성(매체×캠페인×월)을 응답의 `media` 필드로
  구분해서 그대로 받는다.
- **`day_offset: target_date.day`를 반드시 넣는다** — 전월을 전체 월이 아니라 당월과 같은
  일자까지 자른 동일 기간으로 비교하기 위함이다. 이 한 번의 호출로 **전월 동기 값과
  당월(MTD) 값을 동시에** 받는다.
- `group_by: "campaign"`은 `get_ad_performance_monthly_table`에서 실제로 지원됨을 확인했다 —
  응답이 `month`별·`media`별·`campaign_name`별로 나뉘어 온다. google/meta/naver 행에는 `cost`뿐
  아니라 CTR 계산에 필요한 `impression`/`click`도 포함되어 있다.
- ⚠️ **실제로 확인된 데이터 특성**: 캠페인 단위 데이터는 매체마다 보존 기간이 다르다 —
  google/meta/naver(광고비 쪽)는 전월 데이터가 있어도, **airbridge(매출/예약 쪽)는 전월에
  개별 캠페인 행이 없고 `Organic` 집계 행만 있는 경우가 흔하다.** 즉 같은 캠페인이라도
  `광고비`는 M-1 값이 있는데 `매출`/`예약 완료`/`ROAS`는 M-1 값이 없는 식으로, **지표별로
  독립적으로** M-1 유무가 갈릴 수 있다 — 하나가 없다고 해서 나머지도 없다고 가정하지 않는다.
- ⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다 — airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 문자열 `"campaign"` 그대로 보낸다.
- 이 섹션의 `group_by:"campaign"` 응답은 section-3/4가 쓰는 `group_by:"media"` 응답과 행
  granularity(그룹 기준)가 다르므로 서로 공유하지 않는다 — 이 섹션만의 독립된 1회 호출이다.

## 필요 데이터 (캠페인별, M-1/M0 각각 별도로)

각 월(M-1, M0) 각각에 대해, 캠페인별로:

**매체 지표** (google/meta/naver 응답의 해당 월 행):
- `광고비` = `cost`
- `CTR` = `click` ÷ `impression` × 100 (노출 0이면 N/A)

**airbridge 지표** (airbridge 응답의 해당 월 행):
- `매출` = `airbridge_revenue` / `예약 완료` = `reservation`

**조인**: 캠페인 이름 **정확 일치(exact match)**로 매체 행과 airbridge 행을 잇는다 — **M-1과
M0을 각각 독립적으로 조인**한다.
- 매체 쪽에만 있는 캠페인 → 그 달의 매출/예약 완료 칸은 `-`
- airbridge 쪽에만 있는(매칭 실패) 캠페인 → 표에 포함하지 않는다 (개별 캠페인명·매출을 각주에
  나열하지 않는다 — 고정 안내 문구로 갈음한다).

**파생 지표** (월별로 각각 계산):
- `예약 완료 CPA` = 광고비 ÷ 예약 완료 (예약 완료 0이거나 `-`이면 `-`)
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비가 `-`이거나 0이면 `-`)

**표시 지표 순서(고정)**: 광고비 → CTR → 예약 완료 → 예약 완료 CPA → 매출 → ROAS, 총 6개 지표
(`daily-detailed-section-4/5`, `monthly-detailed-section-4`와 동일한 순서).

**변화량** (M0 값 아래에 표시, M-1 대비, 괄호로 감싼다):
- `광고비 변화율`, `예약 완료 변화율`, `매출 변화율` = (M0 − M-1) ÷ M-1 × 100, **%**로 표기.
- `CTR 변화` = M0 CTR − M-1 CTR, **%p**로 표기, 소수점 첫째 자리까지 반올림.
- `예약 완료 CPA 변화율` = (M0 CPA − M-1 CPA) ÷ M-1 CPA × 100, **%**로 표기.
- `ROAS 변화` = M0 ROAS − M-1 ROAS, **%p**로 표기, 소수점 첫째 자리까지 반올림.
- **M-1 값이 `-`이거나 0이어서 비교 자체가 불가능하면, 변화량 자리에 `(-)`를 표시한다** —
  `daily`/`executive-*` 계열 섹션들의 "변화량 자체를 표시하지 않는다"는 규칙과 달리, **이
  섹션은 비교 불가 상태를 명시적으로 `(-)`로 보여준다** (전월 캠페인 데이터 누락이 매우
  흔하기 때문에, 빈 줄보다 "비교 불가"임을 분명히 하는 쪽이 낫다고 판단함).

**필터**: M0 `광고비`가 **₩300,000 이하인 행은 표에서 제외**한다 (렌더링하지 않는다) —
`daily`의 ₩10,000 기준(하루 단위)보다 월 단위에 맞게 높였다.

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다.

## HTML

```html
<!-- BREEZM MONTHLY SECTION 5: 캠페인 성과 비교 및 전월 대비 증감율 (M-1 VS M0) -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title">캠페인 성과 비교 ({M1_YY}년 {M1_MM}월 vs {M0_YY}년 {M0_MM}월) 및 전월 대비 증감율</div>
    <input id="monthlyCampaignSearch" style="border:1px solid #e2e8f0; border-radius:8px; padding:6px 12px; font-size:12px; color:#374151; width:180px;" placeholder="검색" oninput="window.__monthlyCampaignSearch && window.__monthlyCampaignSearch(this.value)">
  </div>
  <div style="overflow-x:auto;">
    <table style="table-layout:fixed; width:auto; border-collapse:collapse;">
      <thead>
        <tr>
          <th rowspan="2" style="white-space:nowrap; text-align:center; vertical-align:middle; border-right:1px solid #e2e8f0; width:90px;">매체</th>
          <th rowspan="2" style="text-align:center; border-right:1px solid #e2e8f0; width:260px;">캠페인</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">광고비</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">CTR</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">예약 완료</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">예약 완료 CPA</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">매출</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle;">ROAS</th>
        </tr>
        <tr>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{M1_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0; width:150px;">{M0_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{M1_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0; width:150px;">{M0_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{M1_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0; width:150px;">{M0_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{M1_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0; width:150px;">{M0_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{M1_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0; width:150px;">{M0_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{M1_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{M0_MM}월</th>
        </tr>
      </thead>
      <tbody id="monthlyCampaignTableBody">
        <!-- 실제 행은 JS가 {MONTHLY_CAMPAIGN_ROWS} 배열(검색어로 거른 뒤 10개씩)에서
             채운다. 정적 예시 행을 직접 넣지 않는다 — 아래 "필요 데이터"에서 각 행을 이미
             완성된 <tr>...</tr> HTML 문자열 + 검색용 텍스트(매체명+캠페인명, 소문자)로
             미리 만들어 배열에 담아야 한다 (M0 광고비 내림차순, M0 광고비 ≤ ₩300,000인
             행은 배열에서 제외). 각 행의 html 형식은 아래와 같다: -->
        <!--
        <tr>
          <td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{channel}</td>
          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{campaign}</td>
          <td style="white-space:nowrap; text-align:center; padding-top:10px; padding-bottom:10px; line-height:1.3;">{m1_광고비}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0; padding-top:10px; padding-bottom:10px; line-height:1.3;">
            <div style="line-height:1.3;">{m0_광고비}</div>
            <div style="font-size:10.5px; text-align:center; color:{광고비_변화_색상}; line-height:1.3; margin-top:3px;">({광고비_화살표} {광고비_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center; padding-top:10px; padding-bottom:10px; line-height:1.3;">{m1_CTR}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0; padding-top:10px; padding-bottom:10px; line-height:1.3;">
            <div style="line-height:1.3;">{m0_CTR}</div>
            <div style="font-size:10.5px; text-align:center; color:{CTR_변화_색상}; line-height:1.3; margin-top:3px;">({CTR_화살표} {CTR_변화})</div>
          </td>
          <td style="white-space:nowrap; text-align:center; padding-top:10px; padding-bottom:10px; line-height:1.3;">{m1_예약_완료}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0; padding-top:10px; padding-bottom:10px; line-height:1.3;">
            <div style="line-height:1.3;">{m0_예약_완료}</div>
            <div style="font-size:10.5px; text-align:center; color:{예약_완료_변화_색상}; line-height:1.3; margin-top:3px;">({예약_완료_화살표} {예약_완료_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center; padding-top:10px; padding-bottom:10px; line-height:1.3;">{m1_예약_CPA}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0; padding-top:10px; padding-bottom:10px; line-height:1.3;">
            <div style="line-height:1.3;">{m0_예약_CPA}</div>
            <div style="font-size:10.5px; text-align:center; color:{예약_CPA_변화_색상}; line-height:1.3; margin-top:3px;">({예약_CPA_화살표} {예약_CPA_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center; padding-top:10px; padding-bottom:10px; line-height:1.3;">{m1_매출}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0; padding-top:10px; padding-bottom:10px; line-height:1.3;">
            <div style="line-height:1.3;">{m0_매출}</div>
            <div style="font-size:10.5px; text-align:center; color:{매출_변화_색상}; line-height:1.3; margin-top:3px;">({매출_화살표} {매출_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center; padding-top:10px; padding-bottom:10px; line-height:1.3;">{m1_ROAS}</td>
          <td style="white-space:nowrap; text-align:center; padding-top:10px; padding-bottom:10px; line-height:1.3;">
            <div style="line-height:1.3;">{m0_ROAS}</div>
            <div style="font-size:10.5px; text-align:center; color:{ROAS_변화_색상}; line-height:1.3; margin-top:3px;">({ROAS_화살표} {ROAS_변화})</div>
          </td>
        </tr>
        -->
      </tbody>
    </table>
  </div>
  <!-- 페이지네이션: 10개씩, 페이지 크기 변경 드롭다운 없음. 버튼은 JS가 동적으로 그린다. -->
  <div id="monthlyCampaignPager" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:16px;"></div>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">
    * {M0_YY}년 {M0_MM}월에 표시된 %는 전월 대비 변화율을 의미합니다.<br>
    * {M0_YY}년 {M0_MM}월 광고비가 ₩300,000 이하인 캠페인은 표에서 제외됩니다.<br>
    * 지표를 비교할 수 없는 경우(전월 데이터 없음 등) (-)로 표시됩니다.<br>
    * 데이터 수집 체계에 따라, 일부 캠페인이 데이터가 누락될 수 있습니다.
  </p>
</div>
```

## Script

```javascript
// Breezm Monthly Section 5: 캠페인 성과 비교 표 — 검색 + 페이지네이션
// 정적 HTML 한 번에 생성되는 보고서라 "검색창 입력/페이지 버튼 클릭 → 서버에 다시 물어본다"
// 방식은 동작하지 않는다. 전체 행을 미리 <tr>...</tr> HTML 문자열 + 검색용 텍스트로 만들어
// 심어두고, 검색·페이지 전환 모두 이 스크립트가 클라이언트에서 직접 처리한다.
(function(){
  const rows = {MONTHLY_CAMPAIGN_ROWS};
  // rows: [{ search: "매체명 캠페인명" (소문자), html: "<tr>...</tr>" }, ...]
  // M0 광고비 내림차순 정렬, M0 광고비 ≤ ₩300,000 제외가 이미 적용된 상태여야 한다.

  const pageSize = 10;
  const tbody = document.getElementById('monthlyCampaignTableBody');
  const pager = document.getElementById('monthlyCampaignPager');
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
    return `<button ${disabled} style="border:1px solid #e2e8f0; border-radius:6px; width:28px; height:28px; font-size:12px; cursor:${opts.disabled?'default':'pointer'}; ${active}" onclick="window.__monthlyCampaignGoto && window.__monthlyCampaignGoto(${page})">${label}</button>`;
  }

  function render() {
    const list = filteredRows();
    const totalPages = Math.max(1, Math.ceil(list.length / pageSize));
    currentPage = Math.min(Math.max(1, currentPage), totalPages);
    const start = (currentPage - 1) * pageSize;
    const pageRows = list.slice(start, start + pageSize);

    tbody.innerHTML = pageRows.length
      ? pageRows.map(r => r.html).join('')
      : `<tr><td colspan="14" style="white-space:nowrap; text-align:center; color:#94a3b8; padding:20px;">검색 결과가 없습니다.</td></tr>`;

    let html = pagerButton('‹', currentPage - 1, { disabled: currentPage === 1 });
    for (let i = 1; i <= totalPages; i++) {
      html += pagerButton(String(i), i, { active: i === currentPage });
    }
    html += pagerButton('›', currentPage + 1, { disabled: currentPage === totalPages });
    pager.innerHTML = html;
  }

  window.__monthlyCampaignGoto = function(page){ currentPage = page; render(); };
  window.__monthlyCampaignSearch = function(value){
    currentTerm = (value || '').trim().toLowerCase();
    currentPage = 1;
    render();
  };

  render();
})();
```

## 렌더링 규칙
- **매체 열과 지표 열에는 `white-space:nowrap`을 적용한다** — "예약 완료"처럼 짧은 한글
  헤더도 열이 좁아지면 한 글자씩 세로로 줄바꿈되는 문제가 발생할 수 있다. **캠페인 열은
  예외다** — 캠페인명이 길어서 `nowrap`을 그대로 쓰면 열이 지나치게 넓어지므로, 이 열은
  넉넉한 고정폭(`width:260px`) + `white-space:normal; overflow-wrap:break-word;`를 쓴다.
  ⚠️ `word-break:break-word`는 쓰지 않는다 — 하이픈/언더스코어 같은 자연스러운 경계를
  무시하고 아무 글자에서나 강제로 끊어서 이름이 세로로 길게 쪼개지는 문제가 생길 수 있다.
  `<table>`에는 **`table-layout:fixed`를 반드시 준다** — `auto`(기본값)에서는 `width`가
  힌트에 불과해서 `nowrap`인 지표 열들이 공간을 다 차지하고 캠페인 열만 계속 짜부라지는
  문제가 생길 수 있다(이 문제를 막기 위해 지표 열(월 표기 헤더) 12개 전부에도 `width:150px`를
  명시했다). ⚠️ **`<table>`에 `width:auto`도 반드시 같이 명시한다** — SKILL.md 공통
  스타일시트의 `table { width: 100%; ... }`가 전역으로 적용되는데, 개별 `<table>`에서
  `width`를 따로 지정하지 않으면 이 100%가 그대로 상속된다. `table-layout:fixed`와
  `width:100%`를 함께 쓰면 지정한 각 열의 픽셀 값이 절대값이 아니라 "100%를 나눠 갖는
  비율"로 취급되어, 열 폭을 아무리 늘려도 카드 폭에 맞춰 다시 쪼그라들어 표가 겹쳐 보이는
  문제가 생길 수 있다. 표가 카드 폭을 넘어가면 감싸는 `overflow-x:auto` 컨테이너가 가로 스크롤을
  대신 처리한다. 캠페인 이름은 **최대 두 줄 정도로 자연스럽게 들어가는 것을 기대**하지만
  정확히 2줄로 맞추는 것 자체가 목표는 아니다 — **이름이 잘려서 표시되는 것만 절대 금지**
  한다(이 규칙이 항상 최우선이다). 이름이 아주 길어서 2줄을 넘어가면 억지로 줄이지 말고
  3줄 이상으로 자연스럽게 넘치도록 둔다.
- 카드 제목·각주의 `{M1_YY}/{M1_MM}` = 전월, `{M0_YY}/{M0_MM}` = 당월(target_date가 속한
  달)이다. 표 헤더의 `{M1_MM}`/`{M0_MM}`도 동일한 월을 가리킨다.
- **헤더 구조**: 지표명(광고비/CTR/예약 완료/예약 완료 CPA/매출/ROAS)을 위쪽 행에 `colspan="2"`로
  한 번만 합쳐 표시하고, 월(M-1/M0)을 아래쪽 행에 표시한다 — 지표명을 M-1/M0 두 칸에 각각
  반복하지 않는다. **헤더 텍스트는 전부 기본 검정 색상**(`#1e293b`)이다 — 월 표기 줄도
  회색으로 옅게 처리하지 않는다.
- **모든 헤더 `<th>`에 `vertical-align:middle`과 상하 대칭 패딩(`padding-top:8px;
  padding-bottom:8px;`)을 명시적으로 적용한다** — 지표명 헤더가 살짝 아래로 치우쳐 보일 수 있다. 위쪽 행에 `padding-bottom:2px`만 주는 식으로 상하 패딩을 비대칭으로 두면, 셀 높이에 남는 여유가 없을 때 `vertical-align:middle`만으로는 비대칭 패딩을 상쇄하지 못한다. 지표명 행과 그 아래
  날짜/월 표기 행 모두 상하 패딩을 동일하게 준다(시각적으로 더 가깝게 붙이려고 일부러
  비대칭을 주지 않는다 — 정확한 상하 중앙 정렬이 항상 더 우선한다).
- **매체/캠페인 열은 좌측 정렬**하고, **그 외 모든 지표 값(광고비/CTR/예약 완료/예약 완료 CPA/매출/
  ROAS의 M-1·M0 값과 변화량)은 전부 중앙 정렬**한다.
- **정렬 순서**: 매체별로 묶지 않고, **M0 광고비 내림차순**으로 전체 캠페인을 한 줄로 정렬한다.
- **필터**: M0 광고비가 ₩300,000 이하인 캠페인은 렌더링하지 않는다 (조용히 제외 — 각주로만
  안내한다).
- **검색과 페이지네이션은 실제로 작동해야 한다.** 서버 없이 한 번에 생성되는 정적 HTML이므로,
  "첫 10개만 적어넣고 검색창·나머지 페이지는 장식으로 둔다" 방식은 **금지**한다(실제로 발생했던
  버그). 필터·정렬을 마친 전체 행을 각각 완성된 `<tr>...</tr>` HTML 문자열 + 검색용
  텍스트(매체명+캠페인명, 소문자)로 만들어 `{MONTHLY_CAMPAIGN_ROWS}` 배열에 전부 담고, 위
  Script가 검색어로 거른 뒤 10개씩 잘라 보여주게 한다. 검색은 매체/캠페인 이름
  **부분일치**(대소문자 무관)로 동작하며, 검색어가 바뀌면 1페이지로 되돌아간다. 페이지당
  10개, 하단에 페이지 번호/이동 버튼만 표시한다. 페이지 크기를 바꾸는 드롭다운은 만들지
  않는다.
- **값 한 줄 + 변화량 한 줄이 같은 셀에 들어가는 M0 셀(광고비/CTR/예약 완료/예약 완료 CPA/
  매출/ROAS 전부)은 겹침을 막기 위해 다음을 함께 적용한다** — 숫자가 크거나(예:
  `₩71,874,324`) 줄 간격이 좁으면 값 텍스트와 셀 경계선(border)이 겹쳐 보이는 문제가 발생할 수 있다:
  1. `<td>`에 `padding-top:10px; padding-bottom:10px; line-height:1.3;`을 준다(위아래
     비대칭 패딩을 쓰지 않는다 — 헤더 셀과 동일한 원칙).
  2. 값과 변화량을 **각각 별도의 `<div>`**로 감싸고 둘 다 `line-height:1.3`을 명시한다 — 값을
     감싸는 `<div>` 없이 텍스트 노드 바로 뒤에 변화량 `<div>`만 두면, 줄 높이가 폰트 크기에
     딱 맞게 눌려서 다음 행의 border-bottom과 겹칠 수 있다.
  3. 변화량 `<div>`에 `margin-top:3px`를 추가로 준다 — 값과 변화량 사이에 최소 여백을
     보장해서 두 줄이 시각적으로 붙어 보이지 않게 한다.
  4. M-1 값만 있는(변화량 없는) 단일 줄 셀에도 **동일한 `padding-top:10px; padding-bottom:10px;
     line-height:1.3;`**을 준다 — M0 셀과 세로 높이가 달라지면 같은 행에서 위아래가 어긋나
     보인다.
  이 네 가지는 특정 지표 하나가 아니라 이 섹션의 M0/M1 값 셀 전부(광고비/CTR/예약 완료/
  예약 완료 CPA/매출/ROAS)에 동일하게 적용하는 공통 규칙이다.
- **M0 셀 값 자체는 색을 입히지 않는다**(기본 텍스트 색상 `#374151`). 값 아래에 M-1 대비
  변화량을 작은 글씨로, **화살표(▲/▼)와 함께 괄호로 감싸** 중앙 정렬로 표시한다 (예:
  `(▲ +3.1%)`, `(▼ -0.1%p)`):
  - 광고비/예약 완료/매출은 상대 변화율(%), CTR/ROAS는 포인트 변화(%p)로 표기하고 부호를 항상
    붙인다. CTR/ROAS 변화는 소수점 첫째 자리까지 반올림한다. 예약 완료 CPA는 상대 변화율(%)로
    표기한다.
  - 색상: 광고비 증가·CTR 증가·예약 완료 증가·매출 증가·ROAS 증가는 긍정 신호로 보고 **빨간색**
    (`#dc2626`)으로, **예약 완료 CPA는 감소가 긍정**이므로 반대로 적용한다 — 그 외는 반대 방향을
    **파란색**(`#2563eb`)으로, 변화가 없으면(0) **검정**(`#1e293b`)으로 표시한다. **"변화가
    없다"는 화면에 표시되는(반올림된) 값을 기준으로 판단한다** — 원본 수치가 미세하게
    양수/음수라도 반올림한 표시값이 `0.0%`/`0.0%p`라면 무조건 검정으로 표시한다(빨간색·
    파란색으로 표시되는 "0.0%"는 모순으로 읽히므로 만들지 않는다).
  - **화살표는 원본 수치의 증가(▲)/감소(▼)만 가리키며 색상과는 독립적으로 판단한다** — 예약
    완료 CPA가 증가했다면 나쁜 신호(파란색)라도 화살표는 `▲`를 쓴다. 표시값이 정확히
    `0.0%`/`0.0%p`이면 화살표를 붙이지 않는다.
  - **M-1 값이 `-`이거나 0이어서 비교가 불가능하면, 변화량 자리에 `(-)`를 그대로 표시한다**
    (화살표 없이, 색상 없이 회색 계열 `#94a3b8`) — 빈 줄로 두거나 아예 생략하지 않는다.
    지표별로 독립적으로 판단한다(예: 같은 캠페인이라도 광고비는 M-1이 있고 매출은 없을 수
    있다).
- 각주는 위 HTML에 적힌 고정 문구 네 줄을 그대로 쓴다 — 매칭 실패한 캠페인명이나 매출액을
  개별 나열하지 않는다.
- 비율/ROAS/CTR은 % 소수점 1자리, 금액(광고비/예약 완료 CPA/매출)은 천 단위 콤마 원화, 예약 완료는
  정수, 값이 없으면 `-`.
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 캠페인명을 정규화/부분일치로 "맞춰서" 조인하지 않는다 — 정확 일치만 쓰고, 나머지는 위 조인
  규칙을 따른다. M-1과 M0의 조인은 서로 독립적으로 판단한다.