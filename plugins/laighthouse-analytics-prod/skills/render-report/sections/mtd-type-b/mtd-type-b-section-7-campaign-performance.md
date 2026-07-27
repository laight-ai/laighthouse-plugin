# MTD-type-b Section 7: Campaign별 성과

**report_type:** `mtd` — **분기 B(type-b) 전용** (항상 포함). 채널-캠페인 단위, MTD
(월초~target_date).

## MCP 도구 호출: `get_ad_performance_daily_table` × 4 (`group_by: "campaign"`)

```json
{ "brand_name": "브리즘", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "google", "group_by": "campaign" }
{ "brand_name": "브리즘", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "meta", "group_by": "campaign" }
{ "brand_name": "브리즘", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "naver", "group_by": "campaign" }
{ "brand_name": "브리즘", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "airbridge", "group_by": "campaign" }
```

- ⚠️ `campaign-type` 금지 — 넣으면 airbridge 행이 조용히 누락된다.
- ⚠️ `group_by`는 문자열 `"campaign"` 그대로 보낸다.

## 필요 데이터 (캠페인별 집계)

**매체 지표** (google/meta/naver 응답, 캠페인별로 일별 행을 합산):
- `노출` = `impression` 합 / `클릭` = `click` 합 / `광고비` = `cost` 합
- `CTR` = 클릭 ÷ 노출 × 100 (노출 0이면 N/A)

**airbridge 지표** (airbridge 응답, 캠페인별 합산):
- `매출` = `airbridge_revenue` 합 / `예약 완료` = `reservation` 합

**조인**: 캠페인 이름 **정확 일치(exact match)**로 매체 행과 airbridge 행을 잇는다.
- 매체 쪽에만 있는 캠페인 → 매출/예약 완료 칸은 `-`
- airbridge 쪽에만 있는(매칭 실패) 캠페인 → **드롭하지 않고** 표 하단 각주에 캠페인명과 매출을
  나열한다.

**파생 지표**:
- `CPA` = 광고비 ÷ 예약 완료 (예약 완료 0이면 N/A)
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비 0이면 N/A)

## HTML

```html
<!-- MTD-TYPE-B SECTION 7: Campaign별 성과 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">Campaign별 성과 (MTD)</div>
  <table>
    <thead><tr>
      <th>Channel</th><th>Campaign</th><th>노출</th><th>클릭</th><th>CTR</th>
      <th>광고비</th><th>매출</th><th>예약 완료</th><th>CPA</th><th>ROAS</th>
    </tr></thead>
    <tbody>
      <!-- 채널별로 묶어 캠페인 행 나열 (광고비 내림차순) -->
      <tr>
        <td>{channel}</td><td>{campaign}</td><td>{노출}</td><td>{클릭}</td><td>{CTR}</td>
        <td>{광고비}</td><td>{매출}</td><td>{예약_완료}</td><td>{CPA}</td><td>{ROAS}</td>
      </tr>
    </tbody>
  </table>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">
    <!-- 매칭 실패한 airbridge 캠페인이 있을 때만 -->
    * 캠페인명 미일치로 표에 포함되지 않은 airbridge 캠페인: {unmatched_list}
  </p>
</div>
```

## Script
없음 (정적 표)

## 렌더링 규칙
- 비율/ROAS/CTR은 % 소수점 1자리, 금액(광고비/매출/CPA)은 천 단위 콤마 원화, N/A는 문자 그대로.
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 캠페인명을 정규화/부분일치로 "맞춰서" 조인하지 않는다 — 정확 일치만 쓰고, 나머지는 각주 규칙을
  따른다.
