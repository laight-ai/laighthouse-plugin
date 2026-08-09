# Breezm Daily Section 5: 광고그룹 및 광고 성과 (D-1 vs D-0)

**report_type:** `daily-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 매체-캠페인-
광고그룹-광고 단위로 **전날(D-1)과 기준일(D-0) 딱 이틀만** 비교한다 — section-4(캠페인 성과)
보다 한 단계 더 깊이(광고그룹/광고) 들어간 버전이며, 지표·색상·정렬 규칙은 section-4와 동일하다.

## MCP 도구 호출: `get_ad_performance_daily_table` × 4 (D-1~D0 이틀만, 매체별 각각 호출)

```json
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "google", "group_by": "ad" }
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "meta", "group_by": "ad" }
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "naver", "group_by": "ad" }
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "airbridge", "group_by": "campaign" }
```

- `start_date`는 항상 `target_date`의 하루 전날이다.
- **google/meta/naver를 각각 별도로 부른다 — `media`를 생략하지 않는다.** 예전에는 세 매체
  모두 필요한 `group_by`가 `"ad"`(가장 세부 단위)로 같다는 이유로 `media`를 생략한 1회
  호출로 통합했었지만, `group_by:"ad"`처럼 광고 단위 행이 나오는 호출은 매체 하나만으로도
  응답이 매우 커질 수 있고(같은 세션 실측: `media:"meta"` 단독, `group_by:"ad"`, 7일
  범위에서 132,913자), `media`를 생략해 불필요한 매체(예: `ga4`)까지 같이 받으면 응답이
  더 커진다 — 실제 프로덕션 실행에서 이 유형의 응답이 모델 컨텍스트를 넘어설 정도로 커진
  사례가 확인되어 매체별 개별 호출로 되돌렸다. 각 호출의 응답 행에는 `ad_name`(광고)뿐 아니라
  상위 차원인 `campaign_name`(캠페인)과 `asset_group`(광고그룹)도 함께 들어있으므로, 매체별
  호출 각각이 캠페인/광고그룹/광고 3단계를 전부 준다 (광고그룹만 따로 `group_by: "ad-set"`로
  재호출할 필요 없음).
- **airbridge는 `media: "airbridge"`, `group_by: "campaign"`으로 별도 호출한다** — airbridge는
  `group_by`가 `"ad"`가 아니라 `"campaign"`이어야 캠페인 단위로 정확히 집계되므로, 위
  google/meta/naver 호출과 합칠 수 없다(예전부터 유지되던 부분이며 이번 되돌림과 무관하다).
  즉 이 섹션은 **4회 호출**(google/meta/naver 각각 1회 + airbridge 1회)이다. 네 호출은 서로
  데이터 의존성이 없으므로 한 메시지 안에서 병렬로 발사한다(위 "병렬 호출 지침" 참고).
- **매체에 따라 `asset_group`/`ad_name`이 비어 있을 수 있다** (예: naver는 캠페인 단위까지만
  제공하고 광고그룹/광고 차원이 없는 경우가 있다) — 이 경우 해당 칸을 `-`로 표시한다(오류
  아님).
- **airbridge는 `group_by: "campaign"`으로만 호출한다** — Airbridge는 캠페인보다 아래
  (광고그룹/광고) 단위로는 매출/예약을 귀속하지 않으므로, 광고그룹/광고 행의 매출·예약 완료·
  CPA·ROAS는 **그 광고가 속한 캠페인의 Airbridge 매출을 그대로 재사용**한다 (같은 캠페인
  아래 있는 모든 광고그룹/광고 행이 동일한 매출/예약 완료/CPA/ROAS 값을 공유하게 된다 — 이는
  데이터 왜곡이 아니라 Airbridge의 귀속 단위 한계다).
- ⚠️ `campaign-type` 금지 — 넣으면 airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 문자열 그대로 보낸다 (`"ad"`/`"campaign"`).

## 필요 데이터 (매체/캠페인/광고그룹/광고별, D-1/D-0 각각 별도로)

각 날짜(D-1, D-0) 각각에 대해:

**매체 지표** (google/meta/naver 각 호출 응답의 해당 날짜 행, `campaign_name`+`asset_group`+
`ad_name` 단위):
- `광고비` = `cost` / `노출` = `impression` / `클릭` = `click`
- `CTR` = 클릭 ÷ 노출 × 100 (노출 0이면 N/A)

**airbridge 지표** (airbridge 호출(`media: "airbridge"`, `group_by: "campaign"`) 응답의 해당
날짜 행, `campaign_name` 단위 — section-4와 동일):
- `매출` = `airbridge_revenue` / `예약 완료` = `reservation`

**조인**: `campaign_name` **정확 일치**로 매체 행(광고그룹/광고 단위)과 airbridge 행(캠페인
단위)을 잇는다 — **같은 캠페인의 모든 광고그룹/광고 행이 그 캠페인의 airbridge 매출/예약 완료를
그대로 공유**한다. D-1과 D-0은 각각 독립적으로 조인한다.
- 매체 쪽에만 있는 캠페인(airbridge에 없음) → 매출/예약 완료 칸은 `-`
- airbridge 쪽에만 있는(매칭 실패) 캠페인의 광고그룹/광고 → 표에 포함하지 않는다.

**파생 지표** (날짜별로 각각 계산):
- `예약 완료 CPA` = 광고비 ÷ 예약 완료 (예약 완료 0이면 N/A)
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비 0이면 N/A)

**표시 지표 순서(고정)**: 광고비 → CTR → 예약 완료 → 예약 완료 CPA → 매출 → ROAS, 총 6개 지표
(section-4와 동일).

**변화량** (D-0 값 아래에 표시, D-1 대비 — section-4와 동일):
- `광고비 변화율` = (D-0 광고비 − D-1 광고비) ÷ D-1 광고비 × 100, **%**로 표기, 괄호로 감싼다
  (D-1 광고비 0/N/A면 표시 안 함)
- `CTR 변화` = D-0 CTR − D-1 CTR, **%p**로 표기, 괄호로 감싼다 (D-1 CTR N/A면 표시 안 함)
- `예약 완료 변화율` = (D-0 예약 완료 − D-1 예약 완료) ÷ D-1 예약 완료 × 100, **%**로 표기, 괄호로 감싼다
  (D-1 예약 완료 0/N/A면 표시 안 함)
- `예약 완료 CPA 변화율` = (D-0 CPA − D-1 CPA) ÷ D-1 CPA × 100, **%**로 표기, 괄호로 감싼다 (D-1
  CPA 0/N/A면 표시 안 함)
- `매출 변화율` = (D-0 매출 − D-1 매출) ÷ D-1 매출 × 100, **%**로 표기, 괄호로 감싼다 (D-1
  매출 0/N/A면 표시 안 함)
- `ROAS 변화` = D-0 ROAS − D-1 ROAS, **%p**로 표기, 괄호로 감싼다 (D-1 ROAS N/A면 표시 안 함)

**화살표**: 위 6개 변화량 각각의 **부호(원본 수치가 증가/감소했는지)에 따라 `▲`(증가) 또는
`▼`(감소)를 값 앞에 붙인다** — 예: `(▲ +5.4%)`, `(▼ -0.4%p)`. 변화가 정확히 0이면 화살표를
붙이지 않는다. **화살표는 색상(긍정/부정 신호)과 무관하게 오로지 수치의 증가·감소만
가리킨다** — 예약 완료 CPA가 증가했다면 그 자체가 나쁜 신호(파란색)라도 화살표는 증가를 뜻하는
`▲`를 쓴다(감소를 뜻하는 `▼`를 쓰지 않는다). 즉 화살표와 색상은 독립적으로 판단한다.

**필터**: D-0 `광고비`가 **₩10,000 이하인 행은 표에서 제외**한다 (렌더링하지 않는다).

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다.

## HTML

```html
<!-- BREEZM DAILY SECTION 5: 광고그룹 및 광고 성과 비교 및 전일 대비 증감율 (D-1 VS D-0) -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title">광고그룹 및 광고 성과 비교 ({D1_MM}월 {D1_DD}일 vs {D0_MM}월 {D0_DD}일) 및 전일 대비 증감율</div>
    <input id="dailyAdSearch" style="border:1px solid #e2e8f0; border-radius:8px; padding:6px 12px; font-size:12px; color:#374151; width:180px;" placeholder="검색" oninput="window.__dailyAdSearch && window.__dailyAdSearch(this.value)">
  </div>
  <div style="overflow-x:auto;">
    <table style="table-layout:fixed; width:auto; border-collapse:collapse;">
      <thead>
        <tr>
          <th rowspan="2" style="white-space:nowrap; text-align:center; vertical-align:middle; border-right:1px solid #e2e8f0; width:90px;">매체</th>
          <th rowspan="2" style="text-align:center; border-right:1px solid #e2e8f0; width:260px;">캠페인</th>
          <th rowspan="2" style="text-align:center; border-right:1px solid #e2e8f0; width:200px;">광고그룹</th>
          <th rowspan="2" style="text-align:center; border-right:1px solid #e2e8f0; width:200px;">광고</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">광고비</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">CTR</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">예약 완료</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">예약 완료 CPA</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">매출</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle;">ROAS</th>
        </tr>
        <tr>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{D1_M}/{D1_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px; border-right:1px solid #e2e8f0;">{D0_M}/{D0_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{D1_M}/{D1_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px; border-right:1px solid #e2e8f0;">{D0_M}/{D0_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{D1_M}/{D1_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px; border-right:1px solid #e2e8f0;">{D0_M}/{D0_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{D1_M}/{D1_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px; border-right:1px solid #e2e8f0;">{D0_M}/{D0_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{D1_M}/{D1_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px; border-right:1px solid #e2e8f0;">{D0_M}/{D0_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{D1_M}/{D1_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; width:150px;">{D0_M}/{D0_D}</th>
        </tr>
      </thead>
      <tbody id="dailyAdTableBody">
        <!-- 실제 행은 JS가 {DAILY_AD_ROWS} 배열(검색어로 거른 뒤 10개씩)에서 채운다. 정적
             예시 행을 직접 넣지 않는다 — 아래 "필요 데이터"에서 각 행을 이미 완성된
             <tr>...</tr> HTML 문자열 + 검색용 텍스트(매체명+캠페인명+광고그룹명+광고명,
             소문자)로 미리 만들어 배열에 담아야 한다 (D-0 광고비 내림차순, D-0 광고비 ≤
             ₩10,000인 행은 배열에서 제외). **매체/캠페인/광고그룹/광고 4개 열의 너비
             ({매체_열_너비} 등)는 고정값이 아니라, 그 열에 들어갈 실제 값들 중 가장 긴
             이름을 기준으로 렌더링 시점에 계산한다** — 아래 "렌더링 규칙"의 계산법 참고.
             각 행의 html 형식은 아래와 같다: -->
        <!--
        <tr>
          <td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{channel}</td>
          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{campaign}</td>
          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{asset_group}</td>
          <td style="text-align:left; white-space:normal; overflow-wrap:break-word; line-height:1.4; border-right:1px solid #e2e8f0;">{ad_name}</td>
          <td style="white-space:nowrap; text-align:center;">{d1_광고비}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {d0_광고비}
            <div style="font-size:10.5px; text-align:center; color:{광고비_변화_색상};">({광고비_화살표} {광고비_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{d1_CTR}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {d0_CTR}
            <div style="font-size:10.5px; text-align:center; color:{CTR_변화_색상};">({CTR_화살표} {CTR_변화})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{d1_예약_완료}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {d0_예약_완료}
            <div style="font-size:10.5px; text-align:center; color:{예약_완료_변화_색상};">({예약_완료_화살표} {예약_완료_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{d1_예약_CPA}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {d0_예약_CPA}
            <div style="font-size:10.5px; text-align:center; color:{예약_CPA_변화_색상};">({예약_CPA_화살표} {예약_CPA_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{d1_매출}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {d0_매출}
            <div style="font-size:10.5px; text-align:center; color:{매출_변화_색상};">({매출_화살표} {매출_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{d1_ROAS}</td>
          <td style="white-space:nowrap; text-align:center;">
            {d0_ROAS}
            <div style="font-size:10.5px; text-align:center; color:{ROAS_변화_색상};">({ROAS_화살표} {ROAS_변화})</div>
          </td>
        </tr>
        -->
      </tbody>
    </table>
  </div>
  <!-- 페이지네이션: 10개씩, 페이지 크기 변경 드롭다운 없음. 버튼은 JS가 동적으로 그린다. -->
  <div id="dailyAdPager" style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:16px;"></div>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">
    * {D0_MM}월 {D0_DD}일에 표시된 %는 전날 대비 변화율을 의미합니다.<br>
    * {D0_MM}월 {D0_DD}일 광고비가 ₩10,000 이하인 광고그룹/광고는 표에서 제외됩니다.<br>
    * 데이터 수집 체계에 따라, 일부 항목이 표시되지 않을 수 있습니다.
  </p>
</div>
```

## Script

```javascript
// Breezm Daily Section 5: 광고그룹 및 광고 성과 표 — 검색 + 페이지네이션
// 정적 HTML 한 번에 생성되는 보고서라 "검색창 입력/페이지 버튼 클릭 → 서버에 다시 물어본다"
// 방식은 동작하지 않는다. 전체 행을 미리 <tr>...</tr> HTML 문자열 + 검색용 텍스트로 만들어
// 심어두고, 검색·페이지 전환 모두 이 스크립트가 클라이언트에서 직접 처리한다.
(function(){
  const rows = {DAILY_AD_ROWS};
  // rows: [{ search: "매체명 캠페인명 광고그룹명 광고명" (소문자), html: "<tr>...</tr>" }, ...]
  // D-0 광고비 내림차순 정렬, D-0 광고비 ≤ ₩10,000 제외가 이미 적용된 상태여야 한다.
  // asset_group/ad_name이 "-"인 행은 search 문자열에 "-"를 그대로 포함해도 무방하다(검색
  // 대상에서 실질적 영향 없음).

  const pageSize = 10;
  const tbody = document.getElementById('dailyAdTableBody');
  const pager = document.getElementById('dailyAdPager');
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
    return `<button ${disabled} style="border:1px solid #e2e8f0; border-radius:6px; width:28px; height:28px; font-size:12px; cursor:${opts.disabled?'default':'pointer'}; ${active}" onclick="window.__dailyAdGoto && window.__dailyAdGoto(${page})">${label}</button>`;
  }

  function render() {
    const list = filteredRows();
    const totalPages = Math.max(1, Math.ceil(list.length / pageSize));
    currentPage = Math.min(Math.max(1, currentPage), totalPages);
    const start = (currentPage - 1) * pageSize;
    const pageRows = list.slice(start, start + pageSize);

    tbody.innerHTML = pageRows.length
      ? pageRows.map(r => r.html).join('')
      : `<tr><td colspan="16" style="white-space:nowrap; text-align:center; color:#94a3b8; padding:20px;">검색 결과가 없습니다.</td></tr>`;

    let html = pagerButton('‹', currentPage - 1, { disabled: currentPage === 1 });
    for (let i = 1; i <= totalPages; i++) {
      html += pagerButton(String(i), i, { active: i === currentPage });
    }
    html += pagerButton('›', currentPage + 1, { disabled: currentPage === totalPages });
    pager.innerHTML = html;
  }

  window.__dailyAdGoto = function(page){ currentPage = page; render(); };
  window.__dailyAdSearch = function(value){
    currentTerm = (value || '').trim().toLowerCase();
    currentPage = 1;
    render();
  };

  render();
})();
```

## 렌더링 규칙
- **모든 `<th>`/`<td>`에 `white-space:nowrap`을 반드시 적용한다** — "예약 완료"처럼 짧은 한글 헤더도 열이 좁아지면 한 글자씩 세로로 줄바꿈되는 문제가 발생할 수 있다. 표가 카드 폭을 넘어가면 감싸는 `overflow-x:auto` 컨테이너가 가로 스크롤을 대신 처리하므로, 텍스트를 줄바꿈해서 억지로 좁히지 않는다.
- **모든 헤더 `<th>`에 `vertical-align:middle`과 상하 대칭 패딩(`padding-top:8px;
  padding-bottom:8px;`)을 명시적으로 적용한다** — 지표명 헤더가 살짝 아래로 치우쳐 보일 수 있다. 위쪽 행에 `padding-bottom:2px`만 주는 식으로 상하 패딩을 비대칭으로 두면, 셀 높이에 남는 여유가 없을 때 `vertical-align:middle`만으로는 비대칭 패딩을 상쇄하지 못한다. 지표명 행과 그 아래
  날짜/월 표기 행 모두 상하 패딩을 동일하게 준다(시각적으로 더 가깝게 붙이려고 일부러
  비대칭을 주지 않는다 — 정확한 상하 중앙 정렬이 항상 더 우선한다).
- 카드 제목·각주의 `{D1_MM}/{D1_DD}` = target_date의 하루 전날, `{D0_MM}/{D0_DD}` = target_date
  그 자체다. 표 헤더의 `{D1_M}/{D1_D}`, `{D0_M}/{D0_D}`는 `M/D`(0 없이) 형식으로 줄인다
  (예: `7/14`, `7/15`).
- **매체/캠페인/광고그룹/광고는 별도의 4개 열로 나눈다** — "매체 / 캠페인"처럼 한 셀에
  합쳐 쓰지 않는다 — 매체와 캠페인을 각각 검색·비교하기 쉽도록 분리한다. 4개 열 모두 사이에 구분선을 넣고 **좌측 정렬**한다.
- **`<table>`에 `table-layout:fixed`를 반드시 준다.** `table-layout:auto`(기본값)에서는
  각 셀의 `width`가 "힌트"에 불과해서, 열이 12개(6개 지표×2)나 되는 이 표에서 `nowrap`인
  지표 열들이 공간을 다 차지하고 식별 열(캠페인/광고그룹/광고)만 계속 짜부라지는 문제가 생길 수 있다(이름이 "u/p/p/e/r"처럼 글자 단위로 쪼개져 여러 줄로 표시됨). `table-layout:
  fixed`를 쓰면 지정한 폭이 그대로 강제된다 — 대신 **지표 열(D-1/D-0 날짜 헤더) 12개
  전부에도 명시적으로 `width:150px`를 준다**(안 주면 `fixed` 모드에서 남는 폭이 이상하게
  분배될 수 있다).
- ⚠️ **`<table>`에 `width:auto`도 반드시 같이 명시한다** — 이게 진짜 근본 원인이었다.
  SKILL.md 공통 스타일시트의 `table { width: 100%; ... }`가 전역으로 적용되는데, 개별
  `<table>`에서 `width`를 따로 지정하지 않으면 이 100%가 그대로 상속된다. **`table-layout:
  fixed`와 `width:100%`를 함께 쓰면, 지정한 각 열의 픽셀 값이 절대값이 아니라 "100%를
  나눠 갖는 비율"로 취급된다** — 그래서 지표 열 폭을 90px→115px→150px로 계속 올려도
  카드 폭(100%)에 맞춰 다시 비율로 쪼그라들어서 실제로는 하나도 안 넓어지고, 표가 계속
  겹쳐 보이는 문제가 반복될 수 있다. `width:auto`를 명시하면 테이블이 선언한 열 폭들의 **합만큼
  실제로 넓어지고**, 카드보다 넓어진 부분은 `overflow-x:auto` 컨테이너가 가로 스크롤로
  처리한다 — 이게 원래 의도한 동작이다.
- **매체 열은 값이 짧으므로 `white-space:nowrap`을 유지**하지만, **캠페인/광고그룹/광고
  3개 열은 이름이 길 수 있으므로 `white-space:normal; overflow-wrap:break-word;`로
  줄바꿈을 허용한다.** ⚠️ **`word-break:break-word`는 쓰지 않는다** — 이 속성은 하이픈·
  언더스코어 같은 자연스러운 경계를 무시하고 아무 글자에서나 강제로 끊어서(예:
  "u/p/p/e/r"), 이름이 하나의 세로로 긴 글자 나열처럼 보이는 문제가 생길 수 있다.
  `overflow-wrap:break-word`는 하이픈/언더스코어/공백 뒤에서 먼저 끊고, 그래도 안 들어가는
  긴 토큰만 최후의 수단으로 강제 개행한다. 절대 `text-overflow:ellipsis`나
  `overflow:hidden`으로 잘라내지 않는다(스크린샷처럼 "upper(al..."로 잘려서 표시되는 문제가 생길 수 있다). 규칙은 다음 3가지다:
  1. 이름은 **최대 두 줄 정도**로 자연스럽게 들어가는 것을 기대하지만, 정확히 2줄로 맞추는
     것 자체가 목표는 아니다.
  2. **이름은 절대 잘려서 표시되면 안 된다** — 이 규칙이 항상 최우선이다.
  3. 이름이 아주 길어서 2줄을 넘어가면, 억지로 줄이거나 자르지 말고 3줄 이상으로 자연스럽게
     넘치도록 둔다 — "잘리지 않는 것"이 "줄 수를 맞추는 것"보다 우선한다.
- **열 너비**: `{캠페인_열_너비}` 같은 이름 길이 기반 정밀 계산은 쓰지 않는다 — 안정적이지 않을 수 있다. 대신 **넉넉한 고정값**을 그대로 쓴다 — 매체 `90px`, 캠페인
  `260px`, 광고그룹 `200px`, 광고 `200px`. 이 값들로도 유난히 긴 이름이 3줄 이상으로
  넘치는 것은 정상이며 문제가 아니다(위 규칙 2·3 참고).
- **헤더 구조**: 지표명(광고비/CTR/예약 완료 CPA/ROAS)을 위쪽 행에 `colspan="2"`로 한 번만 합쳐
  표시하고, 날짜(D-1/D-0)를 아래쪽 행에 표시한다 — 지표명을 D-1/D-0 두 칸에 각각 반복하지
  않는다. **헤더 텍스트는 전부 기본 검정 색상**(`#1e293b`)이다 — 날짜 줄도 회색으로 옅게
  처리하지 않는다. 식별 열(매체/캠페인/광고그룹/광고) 헤더도 포함해 모든 헤더 셀은 중앙
  정렬한다.
- **그 외 모든 지표 값(광고비/CTR/예약 완료 CPA/ROAS의 D-1·D-0 값과 변화량)은 전부 중앙 정렬**
  한다.
- `asset_group`(광고그룹)/`ad_name`(광고)이 빈 값이면 `-`로 표시한다.
- **정렬 순서**: D-0 광고비 내림차순으로 전체 행을 한 줄로 정렬한다 (매체·캠페인별로 묶지 않음).
- **필터**: D-0 광고비가 ₩10,000 이하인 행은 렌더링하지 않는다 (조용히 제외 — 별도 표시 없음,
  각주로만 안내).
- **검색과 페이지네이션은 실제로 작동해야 한다.** 서버 없이 한 번에 생성되는 정적 HTML이므로,
  "첫 10개만 적어넣고 검색창·나머지 페이지는 장식으로 둔다" 방식은 **금지**한다(실제로 발생했던
  버그). 필터·정렬을 마친 전체 행을 각각 완성된 `<tr>...</tr>` HTML 문자열 + 검색용
  텍스트(매체명+캠페인명+광고그룹명+광고명, 소문자)로 만들어 `{DAILY_AD_ROWS}` 배열에 전부
  담고, 위 Script가 검색어로 거른 뒤 10개씩 잘라 보여주게 한다. 검색은 매체/캠페인/광고그룹/
  광고 이름 **부분일치**(대소문자 무관)로 동작하며, 검색어가 바뀌면 1페이지로 되돌아간다.
  페이지당 10개, 하단에 페이지 번호/이동 버튼만 표시한다. 페이지 크기를 바꾸는 드롭다운은
  만들지 않는다.
- **D-0 셀 값 자체는 색을 입히지 않는다**(기본 텍스트 색상). 값 아래에 D-1 대비 변화량을
  작게, **괄호로 감싸** 표시한다 (`(+3.1%)`, `(-0.1%p)`):
  - 광고비/예약 완료 CPA/매출(금액 지표)과 예약 완료(카운트 지표)는 상대 변화율(%), CTR/ROAS는
    포인트 변화(%p)로 표기하고 부호를 항상 붙인다. **CTR·ROAS 변화는 소수점 첫째 자리까지
    반올림**한다(예: `+0.27%p` → `+0.3%p`, section-4와 동일).
  - 변화량 텍스트는 중앙 정렬한다.
  - 색상: 광고비 증가·CTR 증가·예약 완료 증가·매출 증가·ROAS 증가는 빨간색(`#dc2626`),
    **예약 완료 CPA는 감소가 긍정**이므로 반대로 적용한다 — 그 외는 반대 방향을
    파란색(`#2563eb`), 무변화는 검정(`#1e293b`). **"무변화"는 화면에 표시되는(반올림된)
    값을 기준으로 판단한다** — 원본 수치가 미세하게 양수/음수라도, 반올림한 표시값이
    `0.0%`/`0.0%p`라면 무조건 검정으로 표시한다(빨간색이나 파란색으로 표시되는 "0.0%"는
    보는 사람에게 모순으로 읽히므로 만들지 않는다). 화살표도 마찬가지로, 표시값이
    `0.0%`/`0.0%p`이면 붙이지 않는다.
  - **화살표**: 표시값이 0이 아니면 원본 수치의 증가·감소에 따라 값 앞에 `▲`(증가) 또는
    `▼`(감소)를 붙인다(예: `(▲ +5.4%)`, `(▼ -0.4%p)`). 화살표는 색상과 무관하게 오로지
    증가·감소만 가리킨다 — 예약 완료 CPA가 증가했다면(나쁜 신호, 파란색이라도) 화살표는 증가를
    뜻하는 `▲`를 쓴다.
  - D-1 값이 없어(N/A) 변화량을 계산할 수 없으면 변화량 자체를 표시하지 않는다.
- 각주는 위 HTML에 적힌 고정 문구 세 줄을 그대로 쓴다.
- 비율/ROAS/CTR은 % 소수점 1자리, 금액(광고비/예약 완료 CPA/매출)은 천 단위 콤마 원화, 예약 완료는
  정수, N/A는 문자 그대로.
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 캠페인명을 정규화/부분일치로 "맞춰서" 조인하지 않는다 — 정확 일치만 쓴다. D-1과 D-0의
  조인은 서로 독립적으로 판단한다.