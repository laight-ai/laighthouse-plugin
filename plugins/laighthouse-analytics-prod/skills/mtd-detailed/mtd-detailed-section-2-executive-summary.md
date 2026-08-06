# Breezm MTD Section 2: Executive Summary

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 실무자가 오늘
무엇을 점검·조치해야 하는지 판단할 수 있도록, 목표 대비 진행 상황과 페이싱(소진 속도) 중심으로
쓴다. `executive-mtd`의 Executive Summary(섹션 2)와는 목적과 HTML 골격이 다르다 — 이쪽은
실무 관점의 페이싱 점검이며 카드 하나 안에 평범한 불릿 리스트(`<ul><li>`)로 렌더링하고,
`executive-mtd`는 임원 관점의 의사결정 포인트를 불릿마다 별도 카드(점 색상 구분)로 렌더링한다.

---

## 텍스트 생성: 아래 사항을 모두 준수하여, AI가 직접 작성 (`df_dify` MCP 호출 안 함)

⚠️ **`df_dify` MCP 서버는 호출하지 않는다** (브리즘은 이 서버를 쓰지 않는다 — naver 기반 브랜드
전용 도구다).

```
작성 순서:
1. 수치 데이터 수집 — 아래 항목 중 "신규 호출" 표시가 없는 것은 전부 다른 섹션 응답을 그대로
   재사용한다 (별도 재호출 없음):
   - mtd-detailed-section-1(목표 달성 현황)의 get_target_progress_v2 응답(google/meta/naver
     3회) — 목표 ROAS/실제 ROAS. **브리즘은 현재 세 매체 모두 예산(cost) 목표는 등록돼 있지만
     매출(revenue) 목표는 등록되어 있지 않아(target: 0) 목표 ROAS가 N/A인 것이 기본 상태다.**
     목표가 없으면 "목표 대비 상회/근접/하회" 평가를 하지 않고, 실제 ROAS 수치만으로 서술한다.
     (실제 ROAS의 매출은 섹션 1 규칙대로 항상 Airbridge 기준이다 — `get_target_progress_v2`의
     revenue actual은 쓰지 않는다.)
   - mtd-detailed-section-4(일일 매출 현황)의 일별 전체 매출/광고 매출 응답과
     `list_promotions` 응답.
   - mtd-detailed-section-6(광고 매체별 현황)의 매체별 소진액/광고 매출/ROAS 응답.
   - **신규 호출**: `get_ad_performance_monthly_table`을 `media="google"`/`"meta"`/`"naver"`
     (`group_by: "total"`) 3회 + `media="airbridge"`(`group_by: "media"`) 1회, 총 4회
     호출하되 **`day_offset: target_date.day`**를 함께 넣어 `start_month`=전월,
     `end_month`=당월로 지정한다 — 이러면 한 번의 호출로 **당월 MTD 누적치**와 **전월 동기
     (같은 날짜까지) 누적치**를 동시에 받는다. 일별 데이터는 필요 없다 — 두 기간 각각의
     누적 합계만 있으면 충분하다.

   ```json
   { "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "google", "group_by": "total", "day_offset": "target_date.day" }
   { "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "meta", "group_by": "total", "day_offset": "target_date.day" }
   { "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "naver", "group_by": "total", "day_offset": "target_date.day" }
   { "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "airbridge", "group_by": "media", "day_offset": "target_date.day" }
   ```
   ⚠️ `campaign-type`을 넣지 않는다.

2. dify 호출 없이, 위 수치를 근거로 AI가 executive_summary 텍스트를 직접 작성한다. 아래
   <분석 항목> 4가지를 **반드시 이 순서대로, 항목당 정확히 한 문장씩** 포함한다 — naver
   샘플과 달리 이 브랜드는 카테고리·상품 데이터가 없으므로 해당 항목을 매체(채널)·매출 구조
   관점으로 대체했다.

<분석 항목>:
1. **ROAS vs 목표**: target_progress 응답을 바탕으로 이번 달 실제 ROAS가 목표 대비 상회/
   근접/하회 중 무엇인지 구체적인 수치와 함께 한 문장으로 평가한다. 목표 ROAS가 N/A이면
   (현재 브리즘의 기본 상태) 브리즘은 운영 특성상 매출 목표를 정하지 않는다. 따라서 목표와 비교하여 ROAS를 평가하는 것은 불가능하다. 따라서, **위 day_offset 응답으로 계산한 전월 동기
   ROAS와 비교**한다 — 이번 달 동기간 ROAS가 전월 동기 대비 상회/근접/하회인지를 구체적인
   수치와 함께 한 문장으로 쓴다 (예: "이번 달 동기간 ROAS는 122.4%로, 전월 동기(98.1%) 대비
   개선되었습니다.").
2. **페이싱(소진 속도)**: **MTD 누적 광고비**(일별 데이터 불필요, 누적 합계만 사용)를 기준으로
   판단한다. **브리즘은 현재 세 매체 모두 예산(cost) 목표가 등록되어 있으므로**(섹션 1/6 데이터
   재사용), 우선 "예산 소진률(누적 소진액 ÷ 목표 예산) vs 월 진행률(경과일 ÷ 해당 월 총일수)"을
   비교해 소진 속도가 빠른지/느린지/정상인지 한 문장으로 쓴다. 특정 매체(또는 전체)가 no-budget
   상태로 바뀌어 목표 예산을 구할 수 없는 경우에만 예외적으로 **위 day_offset 응답의 당월 동기
   누적 광고비와 전월 동기 누적 광고비**를 비교해 소진 속도가 전월 대비 빠른지/느린지/비슷한지로
   대체 판단한다. 추측성 원인 설명은 쓰지 않는다 — 속도 평가까지만 쓴다.
3. **매체별 특이사항**: mtd-detailed-section-6 데이터에서 매체(Google/Meta/Naver Ads)별
   소진액·매출·ROAS 중 가장 눈에 띄는 사항 하나를 한 문장으로 쓴다.
4. **전체/광고 매출 특이사항**: mtd-detailed-section-4 데이터에서 전체 매출 또는 광고 매출 추이
   중 눈에 띄는 사항 하나를 한 문장으로 쓴다. 같은 섹션의 `list_promotions` 응답에 이번 달
   MTD 기간과 겹치거나 그 직전에 끝난 프로모션이 있으면 **프로모션명과 기간을 함께 언급**하며
   매출 추이와 연계해 서술한다 (효과가 뚜렷하지 않으면 그 사실 그대로 쓴다). 겹치거나 직전에
   끝난 프로모션이 없으면 프로모션 언급 없이 매출 추이 특이사항만 쓴다.

3. 새로운 수치를 지어내지 않는다 — 근거 없는 원인 추정은 쓰지 않는다.
```

---

## 응답 데이터 구조

```json
{
  "executive_summary": "이번 달 동기간 ROAS는 122.4%로, 전월 동기(98.1%) 대비 개선되었습니다.\nMTD 누적 광고비는 전월 동기 대비 늘어난 수준으로, 소진 속도가 다소 빨라지고 있습니다.\nNaver Ads가 광고비 대비 매출이 가장 큰 채널로, ROAS 5,036.7%를 기록 중입니다.\n7월 1일부터 10일까지 진행된 여름 세일 기간 동안 전체 매출이 눈에 띄게 늘어, 프로모션 효과가 있었던 것으로 보입니다."
}
```

- `executive_summary` 값이 문자열이면 그대로 `<p>`로 렌더링
- 줄바꿈(`\n`) 기준으로 분리하여 각 줄을 `<li>`로 렌더링

---

## HTML

```html
<!-- BREEZM MTD SECTION 2: EXECUTIVE SUMMARY -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">Executive Summary</div>
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
- `⚠`로 시작하는 항목은 `color:#d97706`(주황) 처리 — 예: 목표 미등록으로 평가가 어려운 경우,
  소진 속도가 비정상적으로 빠른 경우 등 실무자가 주의해야 할 항목에 붙인다
- 강조 수치는 `<strong>` 태그 사용
- 4개 항목은 항상 이 순서(① ROAS vs 목표 → ② 페이싱 → ③ 매체별 특이사항 → ④ 전체/광고 매출
  특이사항)로 렌더링한다 — 순서를 섞지 않는다