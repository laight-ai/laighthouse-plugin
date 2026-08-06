# Breezm MTD Section 6: 광고 매체별 현황 (Channel Budget)

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 매체별 목표 대비
소진/달성 현황.

## MCP 도구 호출: `get_target_progress_v2` × 3 (섹션 1과 동일 호출 재사용, 별도 재호출 없음)

```json
{ "brand_name": "breezm", "month": "YYYY-MM", "media": "google", "as_of_date": "target_date" }
{ "brand_name": "breezm", "month": "YYYY-MM", "media": "meta", "as_of_date": "target_date" }
{ "brand_name": "breezm", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }
```

섹션 1과 달리 **합산하지 않고 매체별로 한 행씩** 쓴다.

## ⚠️ 광고 매출(실적)은 항상 Airbridge에서만 가져온다

**절대 규칙**: `광고 매출`은 목표 유무와 무관하게 **항상**
`get_ad_performance_monthly_table`(`start_month`=당월, `end_month`=당월,
`day_offset`=target_date.day, `media="airbridge"`, `group_by: "media"`) 1회 호출로 가져온다.
이 호출은 날짜별 행을 합산할 필요 없이 **채널당 이미 합산된 한 줄**을 그대로 반환한다(속도상
`get_ad_performance_daily_table`로 날짜별 행을 받아 직접 합산하는 것보다 훨씬 빠르다). 응답에서
해당 채널 행(매체 ↔ 채널 대응: google ↔ `Google Ads`, meta ↔ `Meta Ads`, naver ↔ `Naver Ads`)의
`airbridge_revenue`를 그대로 쓴다. `get_target_progress_v2`의 `revenue` 행 `actual`은 **절대
쓰지 않는다** — 실제로 naver는 이 값이 0으로 반환되지만 같은 기간 Airbridge에는 naver 채널
매출이 정상적으로 존재하는 문제가 생길 수 있다. 이 호출은 섹션 1이 이미 호출했다면(매번 실행하는
호출이므로 항상 호출했을 것이다) **그대로 재사용**한다 — 재호출하지 않는다.

```json
{ "brand_name": "breezm", "start_month": "당월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "airbridge", "group_by": "media", "day_offset": "target_date.day" }
```

## 매체별 계산 규칙 (cost/revenue 독립 판단)

특정 매체가 `"No {media} budget/target available for {month}."` 메시지를 반환하면 그 매체의
`월 예산`/`예산 소진율`은 N/A, `소진액`은 `get_ad_performance_monthly_table`(`start_month`=
`end_month`=당월, `day_offset`=target_date.day, `media`=해당 매체, `group_by: "total"`) 1회
호출로 대체한다 — 이것도 날짜별 합산 없이 한 줄로 바로 받는다. 섹션 1이 같은 매체에 대해
이미 이 호출을 했다면(섹션 1도 동일한 no-budget 매체에 대해 같은 fallback을 쓰므로 보통
그렇다) 재사용하고, 아니라면 새로 호출한다.

```json
{ "brand_name": "breezm", "start_month": "당월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "google", "group_by": "total", "day_offset": "target_date.day" }
{ "brand_name": "breezm", "start_month": "당월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "meta", "group_by": "total", "day_offset": "target_date.day" }
{ "brand_name": "breezm", "start_month": "당월 YYYY-MM", "end_month": "당월 YYYY-MM", "media": "naver", "group_by": "total", "day_offset": "target_date.day" }
```

표를 반환하는 매체는 `cost` 행을 그대로 쓴다: `월 예산` = target, `소진액` = actual,
`예산 소진율` = progress_ratio × 100. (`target`이 0이면 no-budget과 동일하게 N/A + 대체 처리)

`revenue`/`roas` 행은 **실적(actual)은 위 Airbridge 규칙으로 대체하고, target만 그대로 쓴다**:
`target`이 0보다 크면 `목표 매출` = revenue 행 target, `목표 ROAS` = roas 행 target × 100.
`target`이 0이면(현재 브리즘 세 매체 전부 이 상태) `목표 매출`/`목표 ROAS` 모두 N/A로 표시한다.

`매출 달성률` = 광고 매출(Airbridge) ÷ 목표 매출 × 100 (`목표 매출`이 N/A면 N/A),
`ROAS` = 광고 매출(Airbridge) ÷ 소진액 × 100 (소진액 0이면 N/A).

⚠️ `campaign-type` 금지.

## HTML

```html
<!-- BREEZM MTD SECTION 6: 광고 매체별 현황 (CHANNEL BUDGET) -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">광고 매체별 현황 ({M}월 1일~{M}월 {D}일)</div>
  <table>
    <thead><tr>
      <th style="text-align:center; border-right:1px solid #e2e8f0;">매체</th>
      <th style="text-align:center;">월 예산</th><th style="text-align:center;">소진액</th><th style="text-align:center; border-right:1px solid #e2e8f0;">예산 소진율</th>
      <th style="text-align:center;">목표 매출</th><th style="text-align:center;">광고 매출</th><th style="text-align:center; border-right:1px solid #e2e8f0;">매출 달성률</th>
      <th style="text-align:center;">목표 ROAS</th><th style="text-align:center;">ROAS</th>
    </tr></thead>
    <tbody>
      <!-- 채널별 행: Google Ads / Meta Ads / Naver Ads -->
      <tr>
        <td style="border-right:1px solid #e2e8f0;">{channel}</td>
        <td>{월_예산}</td><td>{소진액}</td><td style="border-right:1px solid #e2e8f0;">{예산_소진율}</td>
        <td>{목표_매출}</td><td>{광고_매출}</td><td style="border-right:1px solid #e2e8f0;">{매출_달성률}</td>
        <td>{목표_ROAS}</td><td>{ROAS}</td>
      </tr>
    </tbody>
  </table>
  <p style="font-size:11px; color:#94a3b8; margin-top:8px;">
    * 월 예산이나 매출 목표가 등록되지 않은 경우, 관련 값이 N/A로 표시됩니다.
  </p>
</div>
```

## Script
없음 (정적 표)

## 렌더링 규칙
- 카드 제목의 `{M}`/`{D}`는 데이터 기간에 맞춰 채운다 — 둘 다 `target_date` 기준이며, 시작은
  항상 당월 1일이므로 `{M}월 1일~{M}월 {D}일` 형식에서 두 `{M}`은 같은 값(당월)이고 `{D}`는
  `target_date`의 일(day)이다 (예: 기준일이 7월 15일이면 "7월 1일~7월 15일").
- 표의 첫 열은 "매체"로 표기하고, 행 값은 `Google Ads`/`Meta Ads`/`Naver Ads`를 그대로 쓴다.
- **모든 헤더 `<th>`에 `text-align:center`를 명시한다** — 공통 스타일시트의 `th` 기본값이
  좌측 정렬(`text-align:left`)이라, 명시하지 않으면 지표 이름이 좌측에 붙어 보인다.
- 비율/ROAS는 % 소수점 1자리, 금액은 천 단위 콤마 원화, N/A는 문자 그대로 `N/A`.
- no-budget 메시지는 오류가 아니다 — 행을 생략하지 말고 N/A 규칙대로 세 매체 전부 렌더링한다.
- 실제 `channel` 값이 상수와 다르면 조용히 0을 만들지 말고 표 아래에 불일치를 명시한다.