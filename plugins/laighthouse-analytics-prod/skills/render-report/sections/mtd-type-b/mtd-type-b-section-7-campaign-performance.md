# Breezm MTD Section 7: 캠페인 성과 (Campaign Performance)

**report_type:** `mtd` — **브리즘(airbridge 기반, type-b) 전용** (항상 포함). 매체-캠페인 단위, MTD
(월초~target_date).

## MCP 도구 호출: `get_ad_performance_daily_table` × 4 (`group_by: "campaign"`)

```json
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "google", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "meta", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "naver", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "airbridge", "group_by": "campaign" }
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
- airbridge 쪽에만 있는(매칭 실패) 캠페인 → 표에 포함하지 않는다 (개별 캠페인명·매출을 각주에
  나열하지 않는다 — 아래 고정 안내 문구로 갈음한다).

**파생 지표**:
- `CPA` = 광고비 ÷ 예약 완료 (예약 완료 0이면 N/A)
- `ROAS` = 매출 ÷ 광고비 × 100 (광고비 0이면 N/A)

## HTML

```html
<!-- BREEZM MTD SECTION 7: 캠페인 성과 (CAMPAIGN PERFORMANCE) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">캠페인 성과 ({M}월 1일~{M}월 {D}일)</div>
  <table>
    <thead><tr>
      <th>매체</th><th>캠페인</th><th>노출</th><th>클릭</th><th>CTR</th>
      <th>광고비</th><th>매출</th><th>예약 완료</th><th>CPA</th><th>ROAS</th>
    </tr></thead>
    <tbody>
      <!-- 매체별로 묶어 캠페인 행 나열 (광고비 내림차순) -->
      <tr>
        <td>{channel}</td><td>{campaign}</td><td>{노출}</td><td>{클릭}</td><td>{CTR}</td>
        <td>{광고비}</td><td>{매출}</td><td>{예약_완료}</td><td>{CPA}</td><td>{ROAS}</td>
      </tr>
    </tbody>
  </table>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">
    * 데이터 수집 체계에 따라, 일부 캠페인이 표시되지 않을 수 있습니다.
  </p>
</div>
```

## Script
없음 (정적 표)

## 렌더링 규칙
- 카드 제목의 `{M}`/`{D}`는 데이터 기간에 맞춰 채운다 — 둘 다 `target_date` 기준이며, 시작은
  항상 당월 1일이므로 `{M}월 1일~{M}월 {D}일` 형식에서 두 `{M}`은 같은 값(당월)이고 `{D}`는
  `target_date`의 일(day)이다 (예: 기준일이 7월 15일이면 "7월 1일~7월 15일").
- 표의 첫 열은 "매체"로 표기하고, 두 번째 열은 "캠페인"으로 표기한다.
- 각주는 위 HTML에 적힌 고정 문구를 그대로 쓴다 — 매칭 실패한 캠페인명이나 매출액을 개별
  나열하지 않는다.
- 비율/ROAS/CTR은 % 소수점 1자리, 금액(광고비/매출/CPA)은 천 단위 콤마 원화, N/A는 문자 그대로.
- 데이터가 비어있으면 "데이터 준비 중" 카드로 대체하고 임의로 채우지 않는다.
- 캠페인명을 정규화/부분일치로 "맞춰서" 조인하지 않는다 — 정확 일치만 쓰고, 나머지는 위 조인
  규칙을 따른다.