# Breezm Executive MTD Section 5: 매체 성과 비교 (전월 vs 당월)

**report_type:** `mtd-summary` — **브리즘(airbridge 기반) 전용** (항상 포함). 전월
(M-1)과 당월(M0)을 매체별로 비교한다. **전월은 전체 월이 아니라 당월과 같은 일자까지 자른
동일 기간(1일~target_date.day일) 비교다** — `day_offset`으로 구현하고, 표 하단에 "전월은
동일 기간(1일~{day}일) 기준" 문구를 반드시 표기한다. 비교 단위는 캠페인이 아니라 매체 —
Naver Ads / Google Ads / Meta Ads / Organic / Others 5개 항목으로 성과를 구분해서 보여준다
(`executive-monthly`의 section-5와 동일한 방식).

## MCP 도구 호출: `get_ad_performance_monthly_table` × 4 (2개월 span, day_offset)

```json
{ "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "google", "group_by": "total", "day_offset": "target_date.day" }
{ "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "meta", "group_by": "total", "day_offset": "target_date.day" }
{ "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "naver", "group_by": "total", "day_offset": "target_date.day" }
{ "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "airbridge", "group_by": "media", "day_offset": "target_date.day" }
```

- `day_offset`이 두 달 모두를 같은 일자(same-day MTD cut)까지 자른다 — 공정한 MoM 비교용.
- google/meta/naver는 `group_by: "total"`(매체별 월간 `cost` 합)만 필요하다.
- airbridge는 `group_by: "media"`(채널별 월간 `airbridge_revenue`/`reservation`)로 받는다.
- ⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다 — airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 문자열 그대로 보낸다 (`"total"`/`"media"`).

## 필요 데이터 (매체별, M-1/M0 각각 별도로)

각 월(M-1, M0) 각각에 대해, airbridge 응답의 `channel` 값을 아래 5개 항목으로 분류한다:

- **Naver Ads**: airbridge `channel`이 정확히 `"Naver Ads"`인 행.
- **Google Ads**: airbridge `channel`이 정확히 `"Google Ads"`인 행.
- **Meta Ads**: airbridge `channel`이 정확히 `"Meta Ads"`인 행.
- **Organic**: airbridge `channel`이 `"Organic"`(자연 유입으로 표시되는 값)인 행.
- **Others**: 위 네 가지에 해당하지 않는 나머지 모든 `channel` 값의 행을 전부 합산한다 (예:
  CRM, 제휴 마케팅, Direct, Referral 등). **실제 channel 값들을 첫 응답에서 확인하고, 위 네
  상수와 다른 값이 있으면 자동으로 Others에 포함시킨다** — 조용히 버리지 않는다.

각 항목의 지표:
- `광고비`: Naver Ads/Google Ads/Meta Ads는 각각 대응하는 매체 응답(naver/google/meta)의
  해당 월(day_offset 적용) `cost`를 그대로 쓴다. **Organic과 Others는 광고비 개념이 없으므로
  항상 `-`로 표시한다.**
- `매출` = 해당 항목으로 분류된 airbridge 행(들)의 `airbridge_revenue` 합.
- `예약 완료` = 해당 항목으로 분류된 airbridge 행(들)의 `reservation` 합.
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비가 `-`인 항목은 ROAS도 `-`로 표시 — 0으로 만들지 않는다).

**변화량** (M0 값 아래에 표시, M-1 대비, 괄호로 감싼다):
- `광고비 변화율`, `매출 변화율`, `예약 완료 변화율` = (M0 − M-1) ÷ M-1 × 100, **%**로 표기
  (M-1 값이 `-`이거나 0이면 표시 안 함).
- `ROAS 변화` = M0 ROAS − M-1 ROAS, **%p**로 표기, 소수점 첫째 자리까지 반올림 (M-1 ROAS가
  `-`이면 표시 안 함).
- **이 섹션은 네 지표 전부 "증가 = 긍정(빨강)"이다.**

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다.

## HTML

```html
<!-- BREEZM EXECUTIVE MTD SECTION 5: 매체 성과 비교 (전월 VS 당월) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">매체 성과 비교 ({YY}년 {MM}월 vs {YY}년 {MM}월) 및 전월 동기간 대비 증감율</div>
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
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle;">{M1_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">{M0_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle;">{M1_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">{M0_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle;">{M1_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">{M0_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle;">{M1_MM}월</th>
          <th style="white-space:nowrap; text-align:center; font-size:11px; font-weight:500; padding-top:8px; padding-bottom:8px; vertical-align:middle;">{M0_MM}월</th>
        </tr>
      </thead>
      <tbody>
        <!-- 매출(M0) 내림차순, Naver Ads/Google Ads/Meta Ads/Organic/Others 5행 고정 -->
        <tr>
          <td style="white-space:nowrap; text-align:left; border-right:1px solid #e2e8f0;">{매체명}</td>
          <td style="white-space:nowrap; text-align:center;">{m1_광고비}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {m0_광고비}
            <div style="font-size:10.5px; text-align:center; color:{광고비_변화_색상};">({광고비_화살표} {광고비_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{m1_매출}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {m0_매출}
            <div style="font-size:10.5px; text-align:center; color:{매출_변화_색상};">({매출_화살표} {매출_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{m1_예약_완료}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {m0_예약_완료}
            <div style="font-size:10.5px; text-align:center; color:{예약_완료_변화_색상};">({예약_완료_화살표} {예약_완료_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{m1_ROAS}</td>
          <td style="white-space:nowrap; text-align:center;">
            {m0_ROAS}
            <div style="font-size:10.5px; text-align:center; color:{ROAS_변화_색상};">({ROAS_화살표} {ROAS_변화})</div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">
    * 전월 데이터는 당월 MTD와 동일 기간(1일~{target_date.day}일) 기준입니다.<br>
    * Others는 CRM, 제휴 마케팅 등 기타 채널을 의미합니다.
  </p>
</div>
```

## Script
없음 (정적 표 — 5개 항목이 고정이라 페이지네이션/검색창을 두지 않는다)

## 렌더링 규칙
- **모든 `<th>`/`<td>`에 `white-space:nowrap`을 반드시 적용한다** — "예약 완료"처럼 짧은 한글 헤더도 열이 좁아지면 한 글자씩 세로로 줄바꿈될 수 있다.
- **모든 헤더 `<th>`에 `vertical-align:middle`과 상하 대칭 패딩(`padding-top:8px;
  padding-bottom:8px;`)을 명시적으로 적용한다** — 지표명 헤더가 살짝 아래로 치우쳐 보일 수 있다. 지표명 행과 그 아래
  날짜/월 표기 행 모두 상하 패딩을 동일하게 준다(시각적으로 더 가깝게 붙이려고 일부러
  비대칭을 주지 않는다 — 정확한 상하 중앙 정렬이 항상 더 우선한다).
- 카드 제목·표 헤더의 `{YY}년 {MM}월 vs {YY}년 {MM}월`(및 `{M1_MM}`/`{M0_MM}`)은 앞이
  전월(M-1), 뒤가 당월(M0)이며 둘 다 `target_date` 기준으로 채운다 (예: 기준일이 2026년
  7월 15일이면 "26년 6월 vs 26년 7월").
- **헤더 구조**: 지표명(광고비/매출/예약 완료/ROAS)을 위쪽 행에 `colspan="2"`로 한 번만 합쳐
  표시하고, 월(M-1/M0)을 아래쪽 행에 표시한다 — 지표명을 M-1/M0 두 칸에 각각 반복하지 않는다.
  **헤더 텍스트는 전부 기본 검정 색상**(`#1e293b`)이다 — 월 표기 줄도 회색으로 옅게 처리하지
  않는다.
- **"매체" 열(항목명)은 좌측 정렬**하고, **그 외 모든 지표 값(광고비/매출/예약 완료/ROAS의
  M-1·M0 값과 변화량)은 전부 중앙 정렬**한다.
- **행 구성은 Naver Ads / Google Ads / Meta Ads / Organic / Others 5개로 고정**한다 — 데이터가
  없어도 항목 자체를 생략하지 않고 `-`로 채운다.
- **정렬 순서**: M0(당월) 매출 내림차순으로 5개 행을 정렬한다.
- **M0 셀 값 자체는 색을 입히지 않는다**(기본 텍스트 색상). 값 아래에 M-1 대비 변화량을 작게,
  **화살표(▲/▼)와 함께 괄호로 감싸** 중앙 정렬로 표시한다 (예: `(▲ +3.1%)`, `(▼ -0.1%p)`):
  - 광고비/매출/예약 완료는 상대 변화율(%), ROAS는 포인트 변화(%p)로 표기하고 부호를 항상 붙인다.
    ROAS 변화는 소수점 첫째 자리까지 반올림한다.
  - **네 지표 전부 "증가=빨강(`#dc2626`)/감소=파랑(`#2563eb`)/무변화=검정(`#1e293b`)"이다**
    (기존의 "음수는 파란색, 양수는 빨간색" 규칙과 방향은 같다 — 표기 형식만 괄호+색상으로
    바뀌었다). **"무변화"는 화면에 표시되는(반올림된) 값을 기준으로 판단한다** — 원본
    수치가 미세하게 양수/음수라도 반올림한 표시값이 `0.0%`/`0.0%p`라면 무조건 검정으로
    표시한다(빨간색·파란색으로 표시되는 "0.0%"는 모순으로 읽히므로 만들지 않는다).
  - **화살표는 원본 수치의 증가(▲)/감소(▼)만 가리키며 색상과는 독립적으로 판단한다.**
    표시값이 정확히 `0.0%`/`0.0%p`이면 화살표를 붙이지 않는다.
  - M-1 값이 `-`이거나 0이어서 변화량을 계산할 수 없으면 변화량 자체를 표시하지 않는다.
- 각주는 위 HTML에 적힌 고정 문구 두 줄을 그대로 쓴다 (`target_date.day`는 실제 기준일로
  채운다).
- 비율/ROAS는 % 소수점 1자리, 금액(광고비/매출)은 천 단위 콤마 원화, 예약 완료는 정수, 값이
  없으면 `-`(N/A 아님 — 이 섹션에서는 "제공되지 않는 지표"를 `-`로 통일한다).
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- airbridge 응답의 실제 `channel` 값을 첫 응답에서 확인하고, 위 4개 상수(Naver Ads/Google
  Ads/Meta Ads/Organic) 중 어디에도 안 맞으면 Others로 분류한다 — 조용히 버리지 않는다.