# Breezm Executive Monthly Section 4: 매출 추이 (Revenue Trend)

**report_type:** `monthly-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
최근 6개월(당월 포함) 라인 차트. 매출은 Airbridge 매출.

> ℹ️ 차트 HTML/Script/각주 3줄(MTD 문구, '전체 매출' 정의 고정 문구, zero-fill 고정 문구)/
> 라벨은 전부 템플릿+빌더가 처리한다 — 모델은 **6개월치 배열 2개**만 빌더 입력 JSON의 `s4`에
> 넣는다.

## MCP 도구 호출 — 별도 호출 없음, section-3의 공유 응답을 재사용

`monthly-summary-section-3-monthly-ad-performance.md`가 1회 호출한
`get_ad_performance_monthly_table`(`media` 생략, `group_by:"media"`, 5개월 전~당월,
`day_offset`=target_date.day) 응답 중 `media`가 `"airbridge"`인 행 전체를 그대로 쓴다 —
필요한 기간·매체가 완전히 동일하므로 재사용에 따른 결과 차이가 없다.

## 빌더 `s4` 필드 (각 배열은 6개, 5개월 전 → 당월 순)

| 필드 | 값 |
|---|---|
| `ad_revenue` | 월별: 광고 채널(`Google Ads`/`Meta Ads`/`Naver Ads`) 행의 `airbridge_revenue` 합 |
| `total_revenue` | 월별: **모든** `channel` 행의 `airbridge_revenue` 합 (광고 채널 외 포함) |
| `labels` | 생략 (빌더가 section-3과 동일한 규칙으로 자동 생성) |

- **6개월 전부 넣는다** — airbridge 행이 전혀 없는 월은 두 값 모두 0으로 기록한다 (추정/보간
  금지). 0이 채워진 월이 있으면 zero-fill 고정 각주는 빌더가 자동으로 붙인다.
- 실제 `channel` 값이 광고 채널 상수와 다르면 조용히 0을 만들지 말고 Executive Summary(`s2`)에
  중립 불릿으로 불일치를 명시한다.
- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
