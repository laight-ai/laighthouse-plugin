# Breezm Executive Daily Section 5: 매체별 성과 (D-1 vs D-0)

**report_type:** `daily-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
`daily`의 section-4(캠페인 성과, D-1 vs D-0)와 비교 방식(D-1 vs D-0, 변화량 표기, 색상 규칙)은
동일하지만, **비교 단위가 캠페인이 아니라 매체**다 — Naver Ads / Google Ads / Meta Ads /
Organic / Others 5개 항목으로 성과를 구분해서 보여준다(임원이 캠페인 단위 디테일 없이 매체
구조만 훑어보도록 만든 섹션).

## `get_ad_performance_daily_table` — 별도 호출 없음, section-3의 공유 응답을 재사용

- 이 섹션은 `get_ad_performance_daily_table`을 직접 호출하지 않는다 —
  `daily-summary-section-3-daily-performance-7days.md`가 3단계에서 1회 호출한 응답(`media`
  생략, `group_by: "media"`, 기준일 6일 전 ~ target_date)을 그대로 재사용하고, 그중 **마지막
  이틀(target_date의 하루 전날 = D-1, target_date = D-0)에 해당하는 행만** 가져다 쓴다 — 이
  섹션이 필요로 하는 D-1~D0 범위는 section-3의 7일 범위 안에 완전히 포함되므로 별도 호출 없이
  그대로 재사용해도 결과는 동일하다.
- `media`가 `google`/`meta`/`naver`인 행(매체당 날짜별로 이미 합산된 한 줄)에서 D-1/D-0 각
  날짜의 `cost`를 가져온다 — 예전에 각각 `group_by: "total"`로 따로 받던 값과 동일하다.
- `media`가 `airbridge`인 행에서 D-1/D-0 각 날짜의 `channel`별 `airbridge_revenue`/
  `reservation`을 가져온다 — 예전에 `airbridge`+`group_by: "media"`로 따로 받던 값과 동일하다.
- D-1 행과 D-0 행은 합산하지 않고 끝까지 따로 유지한다 (section-4와 동일한 방식).

## 필요 데이터 (매체별, D-1/D-0 각각 별도로)

각 날짜(D-1, D-0) 각각에 대해, airbridge 응답의 `channel` 값을 아래 5개 항목으로 분류한다:

- **Naver Ads**: airbridge `channel`이 정확히 `"Naver Ads"`인 행.
- **Google Ads**: airbridge `channel`이 정확히 `"Google Ads"`인 행.
- **Meta Ads**: airbridge `channel`이 정확히 `"Meta Ads"`인 행.
- **Organic**: airbridge `channel`이 `"Organic"`(자연 유입으로 표시되는 값)인 행.
- **Others**: 위 네 가지에 해당하지 않는 나머지 모든 `channel` 값의 행을 전부 합산한다 (예:
  Direct, Referral, 기타 미분류 채널 등). **실제 channel 값들을 첫 응답에서 확인하고, 위
  네 상수와 다른 값이 있으면 자동으로 Others에 포함시킨다** — 조용히 버리지 않는다.

각 항목의 지표:
- `광고비`: Naver Ads/Google Ads/Meta Ads는 각각 공유 응답에서 `media`가 naver/google/meta인
  행의 해당 날짜 `cost`를 그대로 쓴다. **Organic과 Others는 광고비 개념이 없으므로 항상 `-`로
  표시한다** (google/meta/naver 세 매체의 광고비는 이미 각자의 행에 전부 배정되므로, Others에
  남는 광고비는 없다).
- `매출` = 해당 항목으로 분류된 airbridge 행(들)의 `airbridge_revenue` 합.
- `예약 완료` = 해당 항목으로 분류된 airbridge 행(들)의 `reservation` 합.
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비가 `-`인 항목은 ROAS도 `-`로 표시 — 0으로 만들지 않는다).

**변화량** (D-0 값 아래에 표시, D-1 대비 — section-4와 동일한 형식, 괄호로 감싼다):
- `광고비 변화율`, `매출 변화율`, `예약 완료 변화율` = (D-0 − D-1) ÷ D-1 × 100, **%**로 표기
  (D-1 값이 `-`이거나 0이면 표시 안 함).
- `ROAS 변화` = D-0 ROAS − D-1 ROAS, **%p**로 표기, 소수점 첫째 자리까지 반올림 (D-1 ROAS가
  `-`이면 표시 안 함).
- **이 섹션은 네 지표 전부 "증가 = 긍정(빨강)"이다** — section-4의 예약 완료 CPA처럼 "감소가
  긍정"인 지표가 없다 (예약 완료 CPA/CTR 지표 자체가 이 섹션에는 없음).

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다.

## HTML

```html
<!-- BREEZM EXECUTIVE DAILY SECTION 5: 매체별 성과 (D-1 VS D-0) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">매체별 성과 비교 ({D1_MM}월 {D1_DD}일 vs {D0_MM}월 {D0_DD}일) 및 전일 대비 증감율</div>
  <div style="overflow-x:auto;">
    <table>
      <thead>
        <tr>
          <th rowspan="2" style="white-space:nowrap; text-align:center; vertical-align:middle; border-right:1px solid #e2e8f0;">매체</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">광고비</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">매출</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">예약 완료</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle;">ROAS</th>
        </tr>
        <tr>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle;">{D1_M}/{D1_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">{D0_M}/{D0_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle;">{D1_M}/{D1_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">{D0_M}/{D0_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle;">{D1_M}/{D1_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">{D0_M}/{D0_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle;">{D1_M}/{D1_D}</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle;">{D0_M}/{D0_D}</th>
        </tr>
      </thead>
      <tbody>
        <!-- 매출(D-0) 내림차순, Naver Ads/Google Ads/Meta Ads/Organic/Others 5행 고정 -->
        <tr>
          <td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{매체명}</td>
          <td style="white-space:nowrap; text-align:center;">{d1_광고비}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {d0_광고비}
            <div style="font-size:10.5px; text-align:center; color:{광고비_변화_색상};">({광고비_화살표} {광고비_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{d1_매출}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {d0_매출}
            <div style="font-size:10.5px; text-align:center; color:{매출_변화_색상};">({매출_화살표} {매출_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{d1_예약_완료}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {d0_예약_완료}
            <div style="font-size:10.5px; text-align:center; color:{예약_완료_변화_색상};">({예약_완료_화살표} {예약_완료_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{d1_ROAS}</td>
          <td style="white-space:nowrap; text-align:center;">
            {d0_ROAS}
            <div style="font-size:10.5px; text-align:center; color:{ROAS_변화_색상};">({ROAS_화살표} {ROAS_변화})</div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">
    * {D0_MM}월 {D0_DD}일에 표시된 %는 전날 대비 변화율을 의미합니다.<br>
    * Others는 CRM, 제휴 마케팅 등 기타 채널을 의미합니다.<br>
    * 데이터 수집 체계에 따라, 일부 캠페인이 데이터가 누락될 수 있습니다.
  </p>
</div>
```

## Script
없음 (정적 표 — 5개 항목이 고정이라 페이지네이션/검색창을 두지 않는다)

## 렌더링 규칙
- **모든 `<th>`/`<td>`에 `white-space:nowrap`을 반드시 적용한다** — "예약 완료"처럼 짧은 한글 헤더도 열이 좁아지면 한 글자씩 세로로 줄바꿈될 수 있다.
- **모든 헤더 `<th>`에 `vertical-align:middle`과 상하 대칭 패딩(`padding-top:8px;
  padding-bottom:8px;`)을 명시적으로 적용한다** — 지표명(광고비 등) 헤더가 아래로 치우쳐 보일 수 있다. 지표명 행("광고비" 등)과 그 아래 날짜 표기 행
  모두 상하 패딩을 동일하게 준다(지표명 행과 날짜 행을 시각적으로 더 가깝게 붙이려고
  일부러 비대칭을 주지 않는다 — 정확한 상하 중앙 정렬이 항상 더 우선한다).
- 카드 제목·각주의 `{D1_MM}/{D1_DD}` = target_date의 하루 전날, `{D0_MM}/{D0_DD}` = target_date
  그 자체다. 표 헤더의 `{D1_M}/{D1_D}`, `{D0_M}/{D0_D}`는 `M/D`(0 없이) 형식으로 줄인다.
- **헤더 구조**: 지표명(광고비/매출/예약 완료/ROAS)을 위쪽 행에 `colspan="2"`로 한 번만 합쳐
  표시하고, 날짜(D-1/D-0)를 아래쪽 행에 표시한다 — 지표명을 D-1/D-0 두 칸에 각각 반복하지
  않는다. **헤더 텍스트는 전부 기본 검정 색상**(`#1e293b`)이다 — 날짜 줄도 회색으로 옅게
  처리하지 않는다.
- **"매체" 열(항목명)은 좌측 정렬**하고, **그 외 모든 지표 값(광고비/매출/예약 완료/ROAS의
  D-1·D-0 값과 변화량)은 전부 중앙 정렬**한다 — 예약 완료만 중앙 정렬하는 게 아니라 표에 들어가는
  모든 수치 열이 중앙 정렬이어야 한다.
- **행 구성은 Naver Ads / Google Ads / Meta Ads / Organic / Others 5개로 고정**한다 — 데이터가
  없어도 항목 자체를 생략하지 않고 `-`로 채운다.
- **정렬 순서**: D-0 매출 내림차순으로 5개 행을 정렬한다.
- **D-0 셀 값 자체는 색을 입히지 않는다**(기본 텍스트 색상). 값 아래에 D-1 대비 변화량을 작게,
  **화살표(▲/▼)와 함께 괄호로 감싸** 중앙 정렬로 표시한다 (예: `(▲ +3.1%)`, `(▼ -0.1%p)`):
  - 광고비/매출/예약 완료는 상대 변화율(%), ROAS는 포인트 변화(%p)로 표기하고 부호를 항상 붙인다.
    ROAS 변화는 소수점 첫째 자리까지 반올림한다.
  - **이 섹션은 네 지표 전부 "증가=빨강(`#dc2626`)/감소=파랑(`#2563eb`)/무변화=검정
    (`#1e293b`)"이다** — section-4의 예약 완료 CPA 같은 "감소가 긍정" 지표는 없다. **"무변화"는
    화면에 표시되는(반올림된) 값을 기준으로 판단한다** — 원본 수치가 미세하게 양수/음수라도
    반올림한 표시값이 `0.0%`/`0.0%p`라면 무조건 검정으로 표시한다(빨간색·파란색으로
    표시되는 "0.0%"는 모순으로 읽히므로 만들지 않는다).
  - **화살표는 원본 수치의 증가(▲)/감소(▼)만 가리키며 색상과는 독립적으로 판단한다.**
    표시값이 정확히 `0.0%`/`0.0%p`이면 화살표를 붙이지 않는다.
  - D-1 값이 `-`이거나 0이어서 변화량을 계산할 수 없으면 변화량 자체를 표시하지 않는다.
- 각주는 위 HTML에 적힌 고정 문구 세 줄을 그대로 쓴다.
- 비율/ROAS는 % 소수점 1자리, 금액(광고비/매출)은 천 단위 콤마 원화, 예약 완료는 정수, 값이
  없으면 `-`(N/A 아님 — 이 섹션에서는 "제공되지 않는 지표"를 `-`로 통일한다).
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- airbridge 응답의 실제 `channel` 값을 첫 응답에서 확인하고, 위 5개 상수(Naver Ads/Google
  Ads/Meta Ads/Organic) 중 어디에도 안 맞으면 Others로 분류한다 — 조용히 버리지 않는다.