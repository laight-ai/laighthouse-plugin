# Breezm Creative Section 2: Executive Summary

**report_type:** `creative-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). **메타
(Meta Ads)만 대상**이다. 실무자가 소재 운영 관점에서 무엇을 점검·조치해야 하는지 판단할 수
있도록, 소재 단위 특이사항(지표 간 역상관 등)과 최근 7일 추이 중심으로 쓴다. `mtd`/`daily`/
`monthly`의 section-2와 같은 **실무자용 HTML 골격**(카드 하나 + 평범한 `<ul><li>`, `⚠`
항목만 주황색 — `executive-*` 계열의 점-색상 카드가 아님)을 쓴다. **이 섹션은 프로모션을
전혀 언급하지 않는다** — 소재 단위 분석이라 캠페인/매체 차원의 프로모션과 결이 달라서
`list_promotions`를 호출하지 않는다(다른 report_type의 section-2들과 다른 점).

---

## 텍스트 생성: 아래 사항을 모두 준수하여, AI가 직접 작성 (`df_dify` MCP 호출 안 함)

⚠️ **`df_dify` MCP 서버는 호출하지 않는다.** 이 섹션은 **새로운 MCP 호출이 전혀 없다** —
아래 다른 섹션들의 응답만 재사용해서 AI가 직접 작성한다.

```
작성 순서:
1. 수치 데이터 수집 — 신규 호출 없음. 전부 다른 creative 섹션 응답을 그대로 재사용한다:
   - creative-detailed-section-5-daily-creative-performance.md의 **소재 단위 7일 누적 성과**
     (노출/클릭/CTR/광고비/매출/예약 완료/CPA/ROAS) 전체 목록. 항목 1("소재 특이사항")의
     주 데이터 소스다.
   - creative-detailed-section-3-daily-CTR.md와 creative-detailed-section-4-daily-ROAS.md의
     **광고비 상위 5개 소재의 일별 CTR/ROAS 시리즈**(7일치). 항목 2("성과 추이 분석")의
     주 데이터 소스다. ⚠️ **이 두 섹션은 "광고비 상위 5개 소재"만 다룬다** — 따라서 항목
     2("성과 추이 분석")에서 다룰 수 있는 소재는 **이 5개로 제한된다**. section-5에 있는
     다른 소재들은 일별 시계열 데이터가 없어 추이 분석 대상이 될 수 없다.
   - (executive-mtd 계열과 달리 `list_promotions`는 호출하지 않는다 — 이 섹션은 프로모션을
     언급하지 않는다.)
2. dify 호출 없이, 위 수치를 근거로 AI가 executive_summary 텍스트를 직접 작성한다. 아래
   <분석 항목> 2가지를 **반드시 이 순서대로** 포함한다. 각 항목은 선정된 소재 수만큼(항목당
   2~3개) 문장을 쓴다 — 전체 문장 수를 고정하지 않는다.

<분석 항목>:
1. **소재 특이사항**: creative-detailed-section-5-daily-creative-performance의 소재 단위 성과에서 눈에 띄는 사항을 기술한다. 특히 두개 이상의 지표가 역의 상관관계가 보이는 지에 주목한다. (예: CTR은 다른 소재와 비교하여 상대적으로 우수한데 ROAS는 상대적으로 낮은 경우)
2. **성과 추이 분석**: creative-detailed-section-3-daily-CTR, creative-detailed-section-4-daily-ROAS에서 지난 7일의 성과가 유의미하게 변한 소재가 있는지 분석한다. 이를 바탕으로 소재의 교체나 랜딩페이지에서의 고객 경험에 광고 메시지가 부합하는지에 대한 점검 등의 액션 아이템을 기술한다. 
3. 새로운 수치를 지어내지 않는다 — 근거 없는 원인 추정은 쓰지 않는다.

<작성 원칙 — 반드시 지킬 것>:
1. 특이사항마다 **원인에 대한 가설과 해결 방향을 간결하게** 덧붙인다 (예: "CTR은 우수하지만 ROAS는 낮음 - 소재 자체는 매력적이지만 랜딩페이지와는 맞지 않을 수 있어 점검을 권장합니다."). 
2. **truism 금지** — "ROAS가 우수한 소재에 광고비를 늘리면 매출이 늘 것이다" 같은 근거 없는 일반론은 쓰지 않는다. 모든 문장은 구체적 수치(캠페인의 실제 ROAS/예약 완료/매출)를 근거로 든다.
3. 소재는 **2~3개 정도만** 골라 심층 분석한다 (전체를 다 훑지 않는다) —
   광고비 상위이거나 지표 이상 신호가 뚜렷한 것 위주로 고른다. 특이사항이 뚜렷한 캠페인이
   없으면 억지로 채우지 않고 있는 만큼만 쓴다.
4. 새로운 수치를 지어내지 않는다 — 근거 없는 원인 추정은 "확인이 필요하다" 수준으로만 쓴다.
```

---

## 응답 데이터 구조

```json
{
  "executive_summary": "AD_251114_04는 CTR이 4.9%로 상위권이지만 ROAS는 62.1%로 5개 소재 중 가장 낮습니다 — 클릭은 잘 유도하지만 구매 전환으로 이어지지 않는 소재로 보이며, 랜딩페이지나 제안 메시지 점검을 권장합니다.\n2607_all_comfort_feather는 최근 7일간 ROAS가 꾸준히 상승하는 추세(350%→412.8%)를 보입니다 — 이 소재의 예산을 늘려볼 만한 신호로 보입니다.\nAD_251114_04는 같은 기간 ROAS가 80%에서 62.1%로 꾸준히 하락하는 추세를 보입니다 — 소재 피로도가 쌓였을 가능성이 있어 교체나 갱신을 검토해볼 만합니다."
}
```

- `executive_summary` 값이 문자열이면 그대로 `<p>`로 렌더링
- 줄바꿈(`\n`) 기준으로 분리하여 각 줄을 `<li>`로 렌더링 (한 줄 = 한 불릿 = 한 특이사항)

---

## HTML

```html
<!-- BREEZM CREATIVE SECTION 2: EXECUTIVE SUMMARY -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title" style="text-align:left;">Executive Summary</div>
  <ul style="padding-left:20px; line-height:1.9; font-size:13px; color:#374151;">
    <!-- executive_summary를 줄바꿈 기준으로 분리하여 <li>로 렌더링 -->
    {EXECUTIVE_SUMMARY_ITEMS}
  </ul>
</div>
```

## Script
없음 (정적 텍스트)

## 렌더링 규칙
- `executive_summary` 문자열을 `\n` 기준으로 split → 각 줄을 `<li>` 태그로 변환
- 빈 줄은 건너뜀
- `⚠`로 시작하는 항목은 `color:#d97706`(주황) 처리 — 예: ROAS/CTR 역상관이 뚜렷한 소재,
  하락 추세가 뚜렷한 소재 등 실무자가 주의해야 할 항목에 붙인다
- 강조 수치는 `<strong>` 태그 사용
- 항목은 항상 이 순서(① 소재 특이사항 → ② 성과 추이 분석)로 렌더링한다 — 순서를 섞지
  않는다. 전체 문장 수를 고정하지 않는다(항목당 2~3개 소재 기준).
- 프로모션 관련 언급은 절대 넣지 않는다(다른 report_type의 section-2들과 달리 이 섹션의
  범위 밖이다).