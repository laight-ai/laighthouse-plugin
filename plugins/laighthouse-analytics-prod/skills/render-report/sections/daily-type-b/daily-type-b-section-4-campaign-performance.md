# Breezm Daily Section 4: 캠페인 성과 (D-1 vs D-0)

**report_type:** `daily` — **브리즘(airbridge 기반, type-b) 전용** (항상 포함). 매체-캠페인
단위로 **전날(D-1)과 기준일(D-0) 딱 이틀만** 비교한다 — `mtd` 섹션 7(캠페인 성과)처럼 월초부터
누적 합산하지 않는다.

## MCP 도구 호출: `get_ad_performance_daily_table` × 4 (`group_by: "campaign"`, D-1~D0 이틀만)

```json
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "google", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "meta", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "naver", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "media": "airbridge", "group_by": "campaign" }
```

- `start_date`는 항상 `target_date`의 하루 전날이다 (기간 span 2일 → 31일 제한을 항상 만족).
- **이 도구는 원래도 날짜별로 행을 나눠서 반환한다** — mtd 섹션 7에서 "캠페인별로 일별 행을
  합산한다"고 한 것 자체가 날짜별 행이 따로 온다는 뜻이다. 여기서는 그 날짜별 행을 **합산하지
  않고 D-1 행과 D-0 행을 끝까지 따로 유지**한다.
- ⚠️ `campaign-type` 금지 — 넣으면 airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 문자열 `"campaign"` 그대로 보낸다.

## 필요 데이터 (캠페인별, D-1/D-0 각각 별도로)

각 날짜(D-1, D-0) 각각에 대해, 캠페인별로:

**매체 지표** (google/meta/naver 응답의 해당 날짜 행):
- `광고비` = `cost` / `노출` = `impression` / `클릭` = `click`
- `CTR` = 클릭 ÷ 노출 × 100 (노출 0이면 N/A)

**airbridge 지표** (airbridge 응답의 해당 날짜 행):
- `매출` = `airbridge_revenue` / `예약 완료` = `reservation`

**조인**: 캠페인 이름 **정확 일치(exact match)**로 매체 행과 airbridge 행을 잇는다 — **D-1과
D-0을 각각 독립적으로 조인**한다 (어떤 캠페인이 D-0에는 airbridge 매출이 잡히지만 D-1에는
아직 없는 경우처럼, 날짜마다 조인 성공 여부가 다를 수 있다).
- 매체 쪽에만 있는 캠페인 → 그 날짜의 예약 완료/매출 칸은 `-`
- airbridge 쪽에만 있는(매칭 실패) 캠페인 → 표에 포함하지 않는다 (개별 캠페인명·매출을 각주에
  나열하지 않는다 — 고정 안내 문구로 갈음한다).

**파생 지표** (날짜별로 각각 계산):
- `예약 CPA` = 광고비 ÷ 예약 완료 (예약 완료 0이면 N/A)
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비 0이면 N/A)

**변화량** (D-0 값 아래에 표시, D-1 대비):
- `광고비 변화율` = (D-0 광고비 − D-1 광고비) ÷ D-1 광고비 × 100, **%**로 표기 (D-1 광고비 0/N/A면 표시 안 함)
- `CTR 변화` = D-0 CTR − D-1 CTR, **%p**로 표기, **소수점 첫째 자리까지 반올림**한다
  (예: +0.27%p → +0.3%p) (D-1 CTR N/A면 표시 안 함)
- `예약 CPA 변화율` = (D-0 CPA − D-1 CPA) ÷ D-1 CPA × 100, **%**로 표기 (D-1 CPA 0/N/A면 표시 안 함)
- `ROAS 변화` = D-0 ROAS − D-1 ROAS, **%p**로 표기, **소수점 첫째 자리까지 반올림**한다
  (D-1 ROAS N/A면 표시 안 함)

**필터**: D-0 `광고비`가 **₩10,000 이하인 행은 표에서 제외**한다 (렌더링하지 않는다).

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다.

## HTML

```html
<!-- BREEZM DAILY SECTION 4: 캠페인 성과 (D-1 VS D-0) -->
<div class="card" style="margin-bottom:16px;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
    <div class="section-title">캠페인 성과 ({D1_MM}월 {D1_DD}일 vs {D0_MM}월 {D0_DD}일)</div>
    <input style="border:1px solid #e2e8f0; border-radius:8px; padding:6px 12px; font-size:12px; color:#94a3b8; width:180px;" placeholder="검색">
  </div>
  <div style="overflow-x:auto;">
    <table>
      <thead>
        <tr>
          <th rowspan="2">매체</th>
          <th rowspan="2">캠페인</th>
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
        <!-- D-0 광고비 내림차순으로 캠페인 행 나열, D-0 광고비 ≤ ₩10,000인 행은 제외, 페이지당 10개 -->
        <tr>
          <td style="text-align:left; border-right:1px solid #e2e8f0;">{channel}</td>
          <td style="text-align:left; border-right:1px solid #e2e8f0;">{campaign}</td>
          <td style="text-align:right;">{d1_광고비}</td>
          <td style="text-align:right; border-right:1px solid #e2e8f0;">
            {d0_광고비}
            <div style="font-size:10.5px; text-align:center; color:{광고비_변화_색상};">{광고비_변화율}</div>
          </td>
          <td style="text-align:right;">{d1_CTR}</td>
          <td style="text-align:right; border-right:1px solid #e2e8f0;">
            {d0_CTR}
            <div style="font-size:10.5px; text-align:center; color:{CTR_변화_색상};">{CTR_변화}</div>
          </td>
          <td style="text-align:right;">{d1_예약_CPA}</td>
          <td style="text-align:right; border-right:1px solid #e2e8f0;">
            {d0_예약_CPA}
            <div style="font-size:10.5px; text-align:center; color:{예약_CPA_변화_색상};">{예약_CPA_변화율}</div>
          </td>
          <td style="text-align:right;">{d1_ROAS}</td>
          <td style="text-align:right;">
            {d0_ROAS}
            <div style="font-size:10.5px; text-align:center; color:{ROAS_변화_색상};">{ROAS_변화}</div>
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
    * {D0_MM}월 {D0_DD}일 광고비가 ₩10,000 이하인 캠페인은 표에서 제외됩니다.<br>
    * 데이터 수집 체계에 따라, 일부 캠페인이 표시되지 않을 수 있습니다.
  </p>
</div>
```

## Script
없음 (정적 표 — 페이지네이션은 서버/렌더링 단계에서 페이지별로 잘라 보여준다. 클라이언트 JS
정렬·필터링 로직은 필요 없다.)

## 렌더링 규칙
- 카드 제목·각주의 `{D1_MM}/{D1_DD}` = target_date의 하루 전날, `{D0_MM}/{D0_DD}` = target_date
  그 자체다. 표 헤더의 `{D1_M}/{D1_D}`, `{D0_M}/{D0_D}`는 같은 날짜를 `M/D`(0 없이) 형식으로
  줄여서 쓴다 (예: `7/14`, `7/15`).
- 모든 열 헤더(날짜 줄·지표명 줄, 매체·캠페인 포함)는 **중앙 정렬**한다.
- **정렬 순서**: 매체별로 묶지 않고, **D-0 광고비 내림차순**으로 전체 캠페인을 한 줄로 정렬한다.
- **필터**: D-0 광고비가 ₩10,000 이하인 캠페인은 렌더링하지 않는다 (조용히 제외 — 각주로만
  안내한다).
- **페이지네이션**: 페이지당 10개, 하단에 페이지 번호/이동 버튼만 표시한다. **페이지 크기를
  바꾸는 드롭다운("10개" 등)은 만들지 않는다.**
- **D-0 셀 값 자체는 색을 입히지 않는다** (기본 텍스트 색상 `#374151`). 대신 그 값 아래에
  D-1 대비 변화량을 작은 글씨로, **좌우에 괄호를 씌워서** 표시한다 (예: `(+3.1%)`,
  `(-0.1%p)`):
  - 광고비/예약 CPA(금액 지표)는 **상대 변화율(%)**로, CTR/ROAS(비율 지표)는 **포인트
    변화(%p)**로 표기한다. **CTR·ROAS 변화는 소수점 첫째 자리까지 반올림**한다(예:
    `+0.27%p` → `+0.3%p`). 부호(`+`/`-`)를 항상 붙이고, 전체를 괄호로 감싼다.
  - 변화량 텍스트는 **중앙 정렬**한다.
  - 색상: 광고비 증가·CTR 증가·ROAS 증가·**예약 CPA 감소**는 긍정 신호로 보고 **빨간색**
    (`#dc2626`)으로, 그 반대는 **파란색**(`#2563eb`)으로, 변화가 없으면(0) **검정**
    (`#1e293b`)으로 표시한다.
  - D-1 값이 없어(N/A) 변화량을 계산할 수 없으면 변화량 자체를 표시하지 않는다 (빈 줄로 두지
    않고 아예 렌더링하지 않는다).
- 각주는 위 HTML에 적힌 고정 문구 세 줄을 그대로 쓴다 — 매칭 실패한 캠페인명이나 매출액을
  개별 나열하지 않는다.
- 비율/ROAS/CTR은 % 소수점 1자리, 금액(광고비/예약 CPA)은 천 단위 콤마 원화, N/A는 문자
  그대로.
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 캠페인명을 정규화/부분일치로 "맞춰서" 조인하지 않는다 — 정확 일치만 쓰고, 나머지는 위 조인
  규칙을 따른다. D-1과 D-0의 조인은 서로 독립적으로 판단한다.