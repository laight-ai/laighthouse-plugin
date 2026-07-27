# MTD-type-b Section 6: Channel별 예산 소진 현황

**report_type:** `mtd` — **분기 B(type-b) 전용** (항상 포함). 채널(매체)별 목표 대비
소진/달성 현황.

## MCP 도구 호출: `get_target_progress_v2` × 3 (섹션 1과 동일 호출 재사용, 별도 재호출 없음)

```json
{ "brand_name": "브리즘", "month": "YYYY-MM", "media": "google", "as_of_date": "target_date" }
{ "brand_name": "브리즘", "month": "YYYY-MM", "media": "meta", "as_of_date": "target_date" }
{ "brand_name": "브리즘", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }
```

섹션 1과 달리 **합산하지 않고 매체별로 한 행씩** 쓴다. 특정 매체가
`"No {media} budget/target available for {month}."` 메시지를 반환하면(type-b 브랜드의 현재 기대 상태)
그 매체의 목표 관련 칸(목표 예산/소진율/달성률)은 **N/A**, 실적 칸은 섹션 1의 대체 규칙과 동일하게
`get_ad_performance_daily_table`(MTD)에서 가져온다:
- `소진액` = 해당 매체(`media="google"`/`"meta"`/`"naver"`, `group_by: "total"`)의 cost 합
- `매출` = airbridge(`group_by: "media"`) 응답에서 해당 채널 행의 `airbridge_revenue` 합
  (채널 ↔ 매체 대응: `Google Ads` ↔ google, `Meta Ads` ↔ meta, `Naver Ads` ↔ naver)
- `ROAS` = 매출 ÷ 소진액 × 100 (소진액 0이면 N/A)

표를 반환한 매체는 응답 값을 그대로 쓴다: 목표 예산 = cost 행 target, 소진액 = cost 행 actual,
소진율 = cost 행 progress_ratio × 100, 매출 = revenue 행 actual, 달성률 = revenue 행
progress_ratio × 100, ROAS = roas 행 actual × 100.

⚠️ `campaign-type` 금지.

## HTML

```html
<!-- MTD-TYPE-B SECTION 6: Channel별 예산 소진 현황 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">Channel별 예산 소진 현황 (MTD)</div>
  <table>
    <thead><tr>
      <th>Channel</th><th>목표 예산</th><th>소진액</th><th>소진율</th>
      <th>매출</th><th>달성률</th><th>ROAS</th>
    </tr></thead>
    <tbody>
      <!-- 채널별 행: Google Ads / Meta Ads / Naver Ads -->
      <tr>
        <td>{channel}</td><td>{목표_예산}</td><td>{소진액}</td><td>{소진율}</td>
        <td>{매출}</td><td>{달성률}</td><td>{ROAS}</td>
      </tr>
    </tbody>
  </table>
</div>
```

## Script
없음 (정적 표)

## 렌더링 규칙
- 비율/ROAS는 % 소수점 1자리, 금액은 천 단위 콤마 원화, N/A는 문자 그대로 `N/A`.
- no-budget 메시지는 오류가 아니다 — 행을 생략하지 말고 N/A 규칙대로 세 채널 전부 렌더링한다.
- 실제 `channel` 값이 상수와 다르면 조용히 0을 만들지 말고 표 아래에 불일치를 명시한다.
