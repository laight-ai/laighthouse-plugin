# Breezm Daily Section 5: 광고그룹 및 광고 성과 (D-1 vs D-0)

**report_type:** `daily` — **브리즘(airbridge 기반, type-b) 전용** (항상 포함). 매체-캠페인-
광고그룹-광고 단위로 **전날(D-1)과 기준일(D-0) 딱 이틀만** 비교한다 — section-4(캠페인 성과)
보다 한 단계 더 깊이(광고그룹/광고) 들어간 버전이며, 지표·색상·정렬 규칙은 section-4와 동일하다.

## MCP 도구 호출: `get_ad_performance_daily_table` × 4 (media별 `group_by` 다름, D-1~D0 이틀만)

```json
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "google", "group_by": "ad" }
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "meta", "group_by": "ad" }
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "naver", "group_by": "ad" }
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "airbridge", "group_by": "campaign" }
```

- `start_date`는 항상 `target_date`의 하루 전날이다.
- google/meta/naver는 **`group_by: "ad"`**(가장 세부 단위)로 호출한다 — 응답 행에는 `ad_name`
  (광고)뿐 아니라 상위 차원인 `campaign_name`(캠페인)과 `asset_group`(광고그룹)도 함께
  들어있으므로, 이 한 번의 호출로 캠페인/광고그룹/광고 3단계를 전부 얻는다 (광고그룹만 따로
  `group_by: "ad-set"`로 재호출할 필요 없음).
- **매체에 따라 `asset_group`/`ad_name`이 비어 있을 수 있다** (예: naver는 캠페인 단위까지만
  제공하고 광고그룹/광고 차원이 없는 경우가 있다) — 이 경우 해당 칸을 `-`로 표시한다(오류
  아님).
- **airbridge는 `group_by: "campaign"`으로만 호출한다** — Airbridge는 캠페인보다 아래
  (광고그룹/광고) 단위로는 매출/예약을 귀속하지 않으므로, 광고그룹/광고 행의 매출·예약
  완료·CPA·ROAS는 **그 광고가 속한 캠페인의 Airbridge 매출을 그대로 재사용**한다 (같은
  캠페인 아래 있는 모든 광고그룹/광고 행이 동일한 매출/예약 완료/CPA/ROAS 값을 공유하게
  된다 — 이는 데이터 왜곡이 아니라 Airbridge의 귀속 단위 한계다).
- ⚠️ `campaign-type` 금지 — 넣으면 airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 문자열 그대로 보낸다 (`"ad"`/`"campaign"`).

## 필요 데이터 (매체/캠페인/광고그룹/광고별, D-1/D-0 각각 별도로)

각 날짜(D-1, D-0) 각각에 대해:

**매체 지표** (google/meta/naver 응답의 해당 날짜 행, `campaign_name`+`asset_group`+`ad_name`
단위):
- `광고비` = `cost` / `노출` = `impression` / `클릭` = `click`
- `CTR` = 클릭 ÷ 노출 × 100 (노출 0이면 N/A)

**airbridge 지표** (airbridge 응답의 해당 날짜 행, `campaign_name` 단위 — section-4와 동일):
- `매출` = `airbridge_revenue` / `예약 완료` = `reservation`

**조인**: `campaign_name` **정확 일치**로 매체 행(광고그룹/광고 단위)과 airbridge 행(캠페인
단위)을 잇는다 — **같은 캠페인의 모든 광고그룹/광고 행이 그 캠페인의 airbridge 매출/예약
완료를 그대로 공유**한다. D-1과 D-0은 각각 독립적으로 조인한다.
- 매체 쪽에만 있는 캠페인(airbridge에 없음) → 매출/예약 완료 칸은 `-`
- airbridge 쪽에만 있는(매칭 실패) 캠페인의 광고그룹/광고 → 표에 포함하지 않는다.

**파생 지표** (날짜별로 각각 계산):
- `예약 CPA` = 광고비 ÷ 예약 완료 (예약 완료 0이면 N/A)
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비 0이면 N/A)

**변화량** (D-0 값 아래에 표시, D-1 대비 — section-4와 동일):
- `광고비 변화율` = (D-0 광고비 − D-1 광고비) ÷ D-1 광고비 × 100, **%**로 표기, 괄호로 감싼다
  (D-1 광고비 0/N/A면 표시 안 함)
- `CTR 변화` = D-0 CTR − D-1 CTR, **%p**로 표기, 괄호로 감싼다 (D-1 CTR N/A면 표시 안 함)
- `예약 CPA 변화율` = (D-0 CPA − D-1 CPA) ÷ D-1 CPA × 100, **%**로 표기, 괄호로 감싼다 (D-1
  CPA 0/N/A면 표시 안 함)
- `ROAS 변화` = D-0 ROAS − D-1 ROAS, **%p**로 표기, 괄호로 감싼다 (D-1 ROAS N/A면 표시 안 함)

**필터**: D-0 `광고비`가 **₩10,000 이하인 행은 표에서 제외**한다 (렌더링하지 않는다).

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다.

## HTML

```html
<!-- BREEZM DAILY SECTION 5: 광고그룹 및 광고 성과 (D-1 VS D-0) -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title">광고그룹 및 광고 성과 ({D1_MM}월 {D1_DD}일 vs {D0_MM}월 {D0_DD}일)</div>
    <input style="border:1px solid #e2e8f0; border-radius:8px; padding:6px 12px; font-size:12px; color:#94a3b8; width:180px;" placeholder="검색">
  </div>
  <div style="overflow-x:auto;">
    <table>
      <thead>
        <tr>
          <th rowspan="2" style="border-right:1px solid #e2e8f0; width:150px;">매체 / 캠페인</th>
          <th rowspan="2" style="border-right:1px solid #e2e8f0; width:150px;">광고그룹</th>
          <th rowspan="2" style="border-right:1px solid #e2e8f0; width:150px;">광고</th>
          <th style="color:#94a3b8; font-weight:500; font-size:11px; border-bottom:none; text-align:center;">{D1_M}/{D1_D}</th>
          <th style="color:#94a3b8; font-weight:500; font-size:11px; border-bottom:none; text-align:center; border-right:1px solid #e2e8f0;">{D0_M}/{D0_D}</th>
          <th style="color:#94a3b8; font-weight:500; font-size:11px; border-bottom:none; text-align:center;">{D1_M}/{D1_D}</th>
          <th style="color:#94a3b8; font-weight:500; font-size:11px; border-bottom:none; text-align:center; border-right:1px solid #e2e8f0;">{D0_M}/{D0_D}</th>
          <th style="color:#94a3b8; font-weight:500; font-size:11px; border-bottom:none; text-align:center;">{D1_M}/{D1_D}</th>
          <th style="color:#94a3b8; font-weight:500; font-size:11px; border-bottom:none; text-align:center; border-right:1px solid #e2e8f0;">{D0_M}/{D0_D}</th>
          <th style="color:#94a3b8; font-weight:500; font-size:11px; border-bottom:none; text-align:center;">{D1_M}/{D1_D}</th>
          <th style="color:#94a3b8; font-weight:500; font-size:11px; border-bottom:none; text-align:center;">{D0_M}/{D0_D}</th>
        </tr>
        <tr>
          <th style="text-align:center;">광고비</th>
          <th style="text-align:center; border-right:1px solid #e2e8f0;">광고비</th>
          <th style="text-align:center;">CTR</th>
          <th style="text-align:center; border-right:1px solid #e2e8f0;">CTR</th>
          <th style="text-align:center;">예약 CPA</th>
          <th style="text-align:center; border-right:1px solid #e2e8f0;">예약 CPA</th>
          <th style="text-align:center;">ROAS</th>
          <th style="text-align:center;">ROAS</th>
        </tr>
      </thead>
      <tbody>
        <!-- D-0 광고비 내림차순, D-0 광고비 ≤ ₩10,000인 행은 제외, 페이지당 10개 -->
        <tr>
          <td style="text-align:left; border-right:1px solid #e2e8f0; width:150px;"><div>{channel} /</div><div>{campaign}</div></td>
          <td style="text-align:left; border-right:1px solid #e2e8f0; width:150px;">{asset_group}</td>
          <td style="text-align:left; border-right:1px solid #e2e8f0; width:150px;">{ad_name}</td>
          <td style="text-align:right;">{d1_광고비}</td>
          <td style="text-align:right; border-right:1px solid #e2e8f0;">
            {d0_광고비}
            <div style="font-size:10.5px; text-align:center; color:{광고비_변화_색상};">({광고비_변화율})</div>
          </td>
          <td style="text-align:right;">{d1_CTR}</td>
          <td style="text-align:right; border-right:1px solid #e2e8f0;">
            {d0_CTR}
            <div style="font-size:10.5px; text-align:center; color:{CTR_변화_색상};">({CTR_변화})</div>
          </td>
          <td style="text-align:right;">{d1_예약_CPA}</td>
          <td style="text-align:right; border-right:1px solid #e2e8f0;">
            {d0_예약_CPA}
            <div style="font-size:10.5px; text-align:center; color:{예약_CPA_변화_색상};">({예약_CPA_변화율})</div>
          </td>
          <td style="text-align:right;">{d1_ROAS}</td>
          <td style="text-align:right;">
            {d0_ROAS}
            <div style="font-size:10.5px; text-align:center; color:{ROAS_변화_색상};">({ROAS_변화})</div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <!-- 페이지네이션: 10개씩, 페이지 크기 변경 드롭다운 없음 -->
  <div style="display:flex; justify-content:center; align-items:center; gap:8px; margin-top:16px;">
    {PAGINATION_CONTROLS}
  </div>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">
    * {D0_MM}월 {D0_DD}일에 표시된 %는 전날 대비 변화율을 의미합니다.<br>
    * {D0_MM}월 {D0_DD}일 광고비가 ₩10,000 이하인 광고그룹/광고는 표에서 제외됩니다.<br>
    * 데이터 수집 체계에 따라, 일부 항목이 표시되지 않을 수 있습니다.
  </p>
</div>
```

## Script
없음 (정적 표 — 페이지네이션은 렌더링 단계에서 페이지별로 잘라 보여준다.)

## 렌더링 규칙
- 카드 제목·각주의 `{D1_MM}/{D1_DD}` = target_date의 하루 전날, `{D0_MM}/{D0_DD}` = target_date
  그 자체다. 표 헤더의 `{D1_M}/{D1_D}`, `{D0_M}/{D0_D}`는 `M/D`(0 없이) 형식으로 줄인다
  (예: `7/14`, `7/15`).
- **첫 3열(매체/캠페인, 광고그룹, 광고)은 폭을 동일하게(각 150px) 맞추고, 열 사이에 구분선을
  넣는다** — "매체 / 캠페인" 열은 한 셀 안에서 **매체 뒤에 `/`를 붙인 줄(위)**과 **캠페인
  (아래)**을 줄바꿈으로 분리한다 (예: "Naver Ads /" / "파워링크_단백질보충제") — 두 줄 모두
  **기본 텍스트 색상**(`#374151`)이며, 캠페인 줄을 회색 등으로 옅게 처리하지 않는다.
- 모든 열 헤더(날짜 줄·지표명 줄, 첫 3열 포함)는 **중앙 정렬**한다.
- `asset_group`(광고그룹)/`ad_name`(광고)이 빈 값이면 `-`로 표시한다.
- **정렬 순서**: D-0 광고비 내림차순으로 전체 행을 한 줄로 정렬한다 (매체·캠페인별로 묶지 않음).
- **필터**: D-0 광고비가 ₩10,000 이하인 행은 렌더링하지 않는다 (조용히 제외 — 별도 표시 없음,
  각주로만 안내).
- **페이지네이션**: 페이지당 10개, 하단에 페이지 번호/이동 버튼만 표시한다. 페이지 크기를
  바꾸는 드롭다운은 만들지 않는다.
- **D-0 셀 값 자체는 색을 입히지 않는다**(기본 텍스트 색상). 값 아래에 D-1 대비 변화량을
  작게, **괄호로 감싸** 표시한다 (`(+3.1%)`, `(-0.1%p)`):
  - 광고비/예약 CPA는 상대 변화율(%), CTR/ROAS는 포인트 변화(%p)로 표기하고 부호를 항상 붙인다.
    **CTR·ROAS 변화는 소수점 첫째 자리까지 반올림**한다(예: `+0.27%p` → `+0.3%p`, section-4와
    동일).
  - 변화량 텍스트는 중앙 정렬한다.
  - 색상: 광고비 증가·CTR 증가·ROAS 증가·**예약 CPA 감소**는 빨간색(`#dc2626`), 반대는
    파란색(`#2563eb`), 무변화는 검정(`#1e293b`).
  - D-1 값이 없어(N/A) 변화량을 계산할 수 없으면 변화량 자체를 표시하지 않는다.
- 각주는 위 HTML에 적힌 고정 문구 세 줄을 그대로 쓴다.
- 비율/ROAS/CTR은 % 소수점 1자리, 금액(광고비/예약 CPA)은 천 단위 콤마 원화, N/A는 문자
  그대로.
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 캠페인명을 정규화/부분일치로 "맞춰서" 조인하지 않는다 — 정확 일치만 쓴다. D-1과 D-0의
  조인은 서로 독립적으로 판단한다.