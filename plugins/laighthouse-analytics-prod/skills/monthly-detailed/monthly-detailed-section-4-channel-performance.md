# Breezm Monthly Section 4: 매체 성과 비교 (M-1 vs M0)

**report_type:** `monthly-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함).
`executive-daily`의 section-5(매체별 성과, D-1 vs D-0)와 비교 방식(변화량 표기, 색상 규칙,
헤더 구조)은 동일하지만, **비교 시점이 하루가 아니라 한 달**이다 — 전월(M-1)과 당월(M0)을
비교한다. 비교 단위는 캠페인이 아니라 매체 — Naver Ads / Google Ads / Meta Ads / Organic /
Others 5개 항목으로 성과를 구분해서 보여준다. `executive-monthly`의 section-5와 완전히
동일한 내용이며, `monthly`에서는 섹션 순서상 4번이다.

## MCP 도구 호출 — 별도 호출 없음, section-3의 공유 응답을 재사용

이 섹션은 `get_ad_performance_monthly_table`을 직접 호출하지 않는다 —
`monthly-detailed-section-3-monthly-ad-performance.md`가 호출한 **1회 호출**
(`start_month`=5개월 전, `end_month`=당월, `group_by:"media"`, `media` 생략,
`day_offset`=target_date.day) 응답을 그대로 재사용한다. 이 섹션이 필요로 하는 전월(M-1)·
당월(M0) 두 달은 section-3의 6개월 범위 안에 완전히 포함되며, `day_offset`도 section-3와
동일한 값이 범위 내 모든 월에 균일하게 적용되므로(도구 구현상 `day_offset`은 당월뿐 아니라
과거 월에도 동일하게 적용된다) M-1·M0 각각의 값이 별도로 호출했을 때와 완전히 동일하다.

- 이전에는 이 섹션이 `start_month`=전월, `end_month`=당월 범위로 4회(`google`/`meta`/`naver`
  `group_by:"total"` + `airbridge` `group_by:"media"`) 직접 호출했지만, section-3가 이미
  `media` 생략 1회 호출로 더 넓은 6개월 범위(같은 `day_offset`)를 받아두므로 이 섹션은 그
  응답에서 M-1·M0 두 달 행만 골라 쓰면 된다 — 추가 호출이 전혀 필요 없다.
- 공유 응답에서 `media`가 정확히 `"google"`/`"meta"`/`"naver"`인 행은 매체당 월별로 이미
  합산된 한 줄(`cost`/`impression`/`click` 포함 — CTR 계산에 `impression`/`click`도 필요하다)
  이고, `media`가 `"airbridge"`인 행은 월별·`channel`별 여러 줄(`airbridge_revenue`/
  `reservation`)이다.
- ⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다 — airbridge 행이 조용히 누락된다.

## 필요 데이터 (매체별, M-1/M0 각각 별도로)

각 월(M-1, M0) 각각에 대해, airbridge 응답의 `channel` 값을 아래 5개 항목으로 분류한다
(`daily-summary-section-5`와 동일한 분류 방식):

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
- `CTR`: Naver Ads/Google Ads/Meta Ads는 대응 매체 응답의 `click` ÷ `impression` × 100
  (노출 0이면 N/A). **Organic과 Others는 광고 노출/클릭 개념이 없으므로 항상 `-`로 표시한다.**
- `매출` = 해당 항목으로 분류된 airbridge 행(들)의 `airbridge_revenue` 합.
- `예약 완료` = 해당 항목으로 분류된 airbridge 행(들)의 `reservation` 합.
- `예약 완료 CPA` = 광고비 ÷ 예약 완료 (Naver Ads/Google Ads/Meta Ads만 해당 — 광고비가 `-`인
  Organic/Others는 항상 `-`. 예약 완료 0이면 N/A).
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비가 `-`인 항목은 ROAS도 `-`로 표시 — 0으로 만들지 않는다).

**표시 지표 순서(고정)**: 광고비 → CTR → 예약 완료 → 예약 완료 CPA → 매출 → ROAS, 총 6개 지표
(`daily-detailed-section-4/5`와 동일한 순서).

**변화량** (M0 값 아래에 표시, M-1 대비 — 형식은 daily의 section-5와 동일, 괄호로 감싼다):
- `광고비 변화율`, `예약 완료 변화율`, `매출 변화율` = (M0 − M-1) ÷ M-1 × 100, **%**로 표기
  (M-1 값이 `-`이거나 0이면 표시 안 함).
- `CTR 변화` = M0 CTR − M-1 CTR, **%p**로 표기, 소수점 첫째 자리까지 반올림 (M-1 CTR이 `-`
  이거나 N/A면 표시 안 함).
- `예약 완료 CPA 변화율` = (M0 CPA − M-1 CPA) ÷ M-1 CPA × 100, **%**로 표기 (M-1 CPA가 `-`이거나
  0/N/A면 표시 안 함).
- `ROAS 변화` = M0 ROAS − M-1 ROAS, **%p**로 표기, 소수점 첫째 자리까지 반올림 (M-1 ROAS가
  `-`이면 표시 안 함).
- **이 섹션은 광고비/CTR/예약 완료/매출/ROAS 5개 지표는 "증가 = 긍정(빨강)"이고, `예약 완료 CPA`
  만 "감소 = 긍정(빨강)"이다** (daily-detailed-section-4/5와 동일한 색상 규칙).

⚠️ 어떤 호출에도 `campaign-type`을 넣지 않는다.

## HTML

```html
<!-- BREEZM MONTHLY SECTION 4: 매체 성과 비교 및 전월 대비 증감율 (M-1 VS M0) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">매체 성과 비교 ({M1_YY}년 {M1_MM}월 vs {M0_YY}년 {M0_MM}월) 및 전월 대비 증감율</div>
  <div style="overflow-x:auto;">
    <table>
      <thead>
        <tr>
          <th rowspan="2" style="white-space:nowrap; text-align:center; vertical-align:middle; border-right:1px solid #e2e8f0;">매체</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">광고비</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">CTR</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">예약 완료</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">예약 완료 CPA</th>
          <th colspan="2" style="white-space:nowrap; text-align:center; border-bottom:none; padding-top:8px; padding-bottom:8px; vertical-align:middle; border-right:1px solid #e2e8f0;">매출</th>
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
          <td style="white-space:nowrap; text-align:center;">{m1_CTR}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {m0_CTR}
            <div style="font-size:10.5px; text-align:center; color:{CTR_변화_색상};">({CTR_화살표} {CTR_변화})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{m1_예약_완료}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {m0_예약_완료}
            <div style="font-size:10.5px; text-align:center; color:{예약_완료_변화_색상};">({예약_완료_화살표} {예약_완료_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{m1_예약_CPA}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {m0_예약_CPA}
            <div style="font-size:10.5px; text-align:center; color:{예약_CPA_변화_색상};">({예약_CPA_화살표} {예약_CPA_변화율})</div>
          </td>
          <td style="white-space:nowrap; text-align:center;">{m1_매출}</td>
          <td style="white-space:nowrap; text-align:center; border-right:1px solid #e2e8f0;">
            {m0_매출}
            <div style="font-size:10.5px; text-align:center; color:{매출_변화_색상};">({매출_화살표} {매출_변화율})</div>
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
    * {M0_YY}년 {M0_MM}월에 표시된 %는 전월 대비 변화율을 의미합니다.<br>
    * Others는 CRM, 제휴 마케팅 등 기타 채널을 의미합니다.
  </p>
</div>
```

## Script
없음 (정적 표 — 5개 항목이 고정이라 페이지네이션/검색창을 두지 않는다)

## 렌더링 규칙
- **모든 `<th>`/`<td>`에 `white-space:nowrap`을 반드시 적용한다** — "예약 완료"처럼 짧은 한글 헤더도 열이 좁아지면 한 글자씩 세로로 줄바꿈될 수 있다. 표가 카드 폭을 넘어가면 감싸는 `overflow-x:auto` 컨테이너가 가로 스크롤을 대신 처리하므로, 텍스트를 줄바꿈해서 억지로 좁히지 않는다.
- **모든 헤더 `<th>`에 `vertical-align:middle`과 상하 대칭 패딩(`padding-top:8px;
  padding-bottom:8px;`)을 명시적으로 적용한다** — 지표명 헤더가 살짝 아래로 치우쳐 보일 수 있다. 지표명 행과 그 아래
  날짜/월 표기 행 모두 상하 패딩을 동일하게 준다(시각적으로 더 가깝게 붙이려고 일부러
  비대칭을 주지 않는다 — 정확한 상하 중앙 정렬이 항상 더 우선한다).
- 카드 제목·표 헤더의 `{M1_YY}/{M1_MM}` = 전월, `{M0_YY}/{M0_MM}` = 당월(target_date가 속한
  달)이다.
- **헤더 구조**: 지표명(광고비/CTR/예약 완료/예약 완료 CPA/매출/ROAS)을 위쪽 행에 `colspan="2"`로
  한 번만 합쳐 표시하고, 월(M-1/M0)을 아래쪽 행에 표시한다 — 지표명을 M-1/M0 두 칸에 각각
  반복하지 않는다. **헤더 텍스트는 전부 기본 검정 색상**(`#1e293b`)이다 — 월 표기 줄도
  회색으로 옅게 처리하지 않는다.
- **"매체" 열(항목명)은 좌측 정렬**하고, **그 외 모든 지표 값(광고비/CTR/예약 완료/예약 완료 CPA/
  매출/ROAS의 M-1·M0 값과 변화량)은 전부 중앙 정렬**한다.
- **행 구성은 Naver Ads / Google Ads / Meta Ads / Organic / Others 5개로 고정**한다 — 데이터가
  없어도 항목 자체를 생략하지 않고 `-`로 채운다.
- **정렬 순서**: M0(당월) 매출 내림차순으로 5개 행을 정렬한다.
- **M0 셀 값 자체는 색을 입히지 않는다**(기본 텍스트 색상). 값 아래에 M-1 대비 변화량을 작게,
  **화살표(▲/▼)와 함께 괄호로 감싸** 중앙 정렬로 표시한다 (예: `(▲ +3.1%)`, `(▼ -0.1%p)`):
  - 광고비/예약 완료/매출은 상대 변화율(%), CTR/ROAS는 포인트 변화(%p)로 표기하고 부호를 항상
    붙인다. CTR/ROAS 변화는 소수점 첫째 자리까지 반올림한다.
  - **광고비/CTR/예약 완료/매출/ROAS 5개 지표는 "증가=빨강(`#dc2626`)"이고, `예약 완료 CPA`만
    "감소=빨강"이다** — 그 반대는 파랑(`#2563eb`), 무변화는 검정(`#1e293b`). **"무변화"는
    화면에 표시되는(반올림된) 값을 기준으로 판단한다** — 원본 수치가 미세하게 양수/음수라도
    반올림한 표시값이 `0.0%`/`0.0%p`라면 무조건 검정으로 표시한다(빨간색·파란색으로 표시되는
    "0.0%"는 모순으로 읽히므로 만들지 않는다).
  - **화살표는 원본 수치의 증가(▲)/감소(▼)만 가리키며 색상과는 독립적으로 판단한다** —
    예약 완료 CPA가 증가했다면 나쁜 신호(파란색)라도 화살표는 `▲`를 쓴다. 표시값이 정확히
    `0.0%`/`0.0%p`이면 화살표를 붙이지 않는다.
  - M-1 값이 `-`이거나 0이어서 변화량을 계산할 수 없으면 변화량 자체를 표시하지 않는다.
- 각주는 위 HTML에 적힌 고정 문구 두 줄을 그대로 쓴다.
- 비율/ROAS/CTR은 % 소수점 1자리, 금액(광고비/예약 완료 CPA/매출)은 천 단위 콤마 원화, 예약 완료는
  정수, 값이 없으면 `-`(N/A 아님 — 이 섹션에서는 "제공되지 않는 지표"를 `-`로 통일한다).
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- airbridge 응답의 실제 `channel` 값을 첫 응답에서 확인하고, 위 4개 상수(Naver Ads/Google
  Ads/Meta Ads/Organic) 중 어디에도 안 맞으면 Others로 분류한다 — 조용히 버리지 않는다.