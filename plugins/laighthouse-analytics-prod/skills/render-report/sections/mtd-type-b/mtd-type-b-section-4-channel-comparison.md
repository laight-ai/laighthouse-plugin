# MTD-type-b Section 4: Channel별 성과 비교 (전월 vs 당월)

**report_type:** `mtd` — **분기 B(type-b) 전용** (항상 포함). 전월(M-1)과 당월(M0)을
채널별로 비교한다. **전월은 전체 월이 아니라 당월과 같은 일자까지 자른 동일 기간(1일~target_date.day일)
비교다** — `day_offset`으로 구현하고, 표 하단에 "전월은 동일 기간(1일~{day}일) 기준" 문구를
반드시 표기한다.

## MCP 도구 호출: `get_ad_performance_monthly_table` × 4 (2개월 span, day_offset)

```json
{ "brand_name": "브리즘", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "google", "group_by": "total", "day_offset": "target_date.day" }
{ "brand_name": "브리즘", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "meta", "group_by": "total", "day_offset": "target_date.day" }
{ "brand_name": "브리즘", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "naver", "group_by": "total", "day_offset": "target_date.day" }
{ "brand_name": "브리즘", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "airbridge", "group_by": "media", "day_offset": "target_date.day" }
```

- `day_offset`이 두 달 모두를 같은 일자(same-day MTD cut)까지 자른다 — 공정한 MoM 비교용.
- ⚠️ `campaign-type` 금지.

## 필요 데이터 (채널별 집계)

채널 ↔ 매체 대응: `Google Ads` ↔ `google`, `Meta Ads` ↔ `meta`, `Naver Ads` ↔ `naver`.

각 채널·각 월(M-1, M0)에 대해:
- `광고 매출` = airbridge 응답에서 해당 채널 행의 `airbridge_revenue`
- `광고비` = 대응 매체 응답의 `cost`
- `ROAS` = 광고 매출 ÷ 광고비 × 100 (광고비 0이면 N/A)

MoM 지표:
- `ROAS MoM` = M0 ROAS − M-1 ROAS, **%p(퍼센트포인트 차이)**로 표기 (예: `+12.3%p`)
- `광고 매출 MoM` = (M0 매출 − M-1 매출) ÷ M-1 매출 × 100, **%(상대 변화율)**로 표기
  (M-1 매출 0이면 N/A)

## HTML

```html
<!-- MTD-TYPE-B SECTION 4: Channel별 성과 비교 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">Channel별 성과 비교 (전월 vs 당월)</div>
  <table>
    <thead><tr>
      <th>Channel</th><th>전월 광고 매출</th><th>당월 광고 매출</th><th>광고 매출 MoM</th>
      <th>전월 ROAS</th><th>당월 ROAS</th><th>ROAS MoM</th>
    </tr></thead>
    <tbody>
      <!-- 채널별 행: Google Ads / Meta Ads / Naver Ads -->
      <tr>
        <td>{channel}</td><td>{prev_revenue}</td><td>{curr_revenue}</td>
        <td style="color:{changeColor};">{revenue_mom_pct}</td>
        <td>{prev_roas}</td><td>{curr_roas}</td>
        <td style="color:{changeColor};">{roas_mom_pp}</td>
      </tr>
    </tbody>
  </table>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">
    * 전월은 동일 기간(1일~{target_date.day}일) 기준입니다.
  </p>
</div>
```

## Script
없음 (정적 표)

## 렌더링 규칙
- MoM 값은 부호 포함 표기, 양수 초록/음수 빨강 (공통 유틸 `changeColor` 규칙).
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 실제 `channel` 값이 상수와 다르면 조용히 0을 만들지 말고 표 아래에 불일치를 명시한다.
