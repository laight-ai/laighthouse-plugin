# Breezm Executive MTD Section 5: Channel별 성과 비교 (전월 vs 당월) (Channel Comparison)

**report_type:** `executive-mtd` — **브리즘(airbridge 기반, type-b) 전용** (항상 포함). 전월(M-1)과
당월(M0)을 채널별로 비교한다. **전월은 전체 월이 아니라 당월과 같은 일자까지 자른 동일 기간
(1일~target_date.day일) 비교다** — `day_offset`으로 구현하고, 표 하단에 "전월은 동일 기간
(1일~{day}일) 기준" 문구를 반드시 표기한다.

## MCP 도구 호출: `get_ad_performance_monthly_table` × 4 (2개월 span, day_offset)

```json
{ "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "google", "group_by": "total", "day_offset": "target_date.day" }
{ "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "meta", "group_by": "total", "day_offset": "target_date.day" }
{ "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "naver", "group_by": "total", "day_offset": "target_date.day" }
{ "brand_name": "breezm", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "airbridge", "group_by": "media", "day_offset": "target_date.day" }
```

- `day_offset`이 두 달 모두를 같은 일자(same-day MTD cut)까지 자른다 — 공정한 MoM 비교용.
- ⚠️ `campaign-type` 금지.

## 필요 데이터 (채널별 집계)

채널 ↔ 매체 대응: `Google Ads` ↔ `google`, `Meta Ads` ↔ `meta`, `Naver Ads` ↔ `naver`.

각 채널·각 월(M-1, M0)에 대해:
- `광고 매출` = airbridge 응답에서 해당 채널 행의 `airbridge_revenue`
- `광고비` = 대응 매체 응답의 `cost`
- `ROAS` = 광고 매출 ÷ 광고비 × 100 (광고비 0이면 N/A)

MoM 지표 (표에는 "변화율"로 표기):
- `ROAS 변화율` (`roas_change_pp`) = M0 ROAS − M-1 ROAS, **%p(퍼센트포인트 차이)**로 표기 (예: `+12.3%p`)
- `광고 매출 변화율` (`revenue_change_pct`) = (M0 매출 − M-1 매출) ÷ M-1 매출 × 100, **%(상대 변화율)**로 표기
  (M-1 매출 0이면 N/A)

## HTML

```html
<!-- BREEZM EXECUTIVE MTD SECTION 5: Channel별 성과 비교 (CHANNEL COMPARISON) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">Channel별 성과 비교 ({YY}년 {MM}월 vs {YY}년 {MM}월)</div>
  <table>
    <thead><tr>
      <th style="border-right:1px solid #e2e8f0;">Channel</th><th>전월 광고 매출</th><th>당월 광고 매출</th><th style="border-right:1px solid #e2e8f0;">광고 매출 변화율</th>
      <th>전월 ROAS</th><th>당월 ROAS</th><th>ROAS 변화율</th>
    </tr></thead>
    <tbody>
      <!-- 채널별 행: Google Ads / Meta Ads / Naver Ads -->
      <tr>
        <td style="border-right:1px solid #e2e8f0;">{channel}</td><td>{prev_revenue}</td><td>{curr_revenue}</td>
        <td style="color:{changeColor}; border-right:1px solid #e2e8f0;">{revenue_change_pct}</td>
        <td>{prev_roas}</td><td>{curr_roas}</td>
        <td style="color:{changeColor};">{roas_change_pp}</td>
      </tr>
    </tbody>
  </table>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">
    * 전월 데이터는 당월 MTD와 동일 기간(1일~{target_date.day}일) 기준입니다.
  </p>
</div>
```

## Script
없음 (정적 표)

## 렌더링 규칙
- 카드 제목의 `{YY}년 {MM}월 vs {YY}년 {MM}월`은 앞이 전월(M-1), 뒤가 당월(M0)이며 둘 다
  `target_date` 기준으로 채운다 (예: 기준일이 2026년 7월 15일이면 "26년 6월 vs 26년 7월").
- 변화율(`광고 매출 변화율`/`ROAS 변화율`) 값은 부호 포함 표기, **음수는 파란색, 양수는 빨간색**으로
  표시한다 (공통 유틸 `changeColor` 규칙 갱신: 기존 초록/빨강 대신 파란색/빨간색 사용).
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 실제 `channel` 값이 상수와 다르면 조용히 0을 만들지 말고 표 아래에 불일치를 명시한다.
- 표 아래 각주는 전월 데이터의 동일 기간 기준만 명시한다 (`target_date.day`는 실제 기준일로
  채운다).