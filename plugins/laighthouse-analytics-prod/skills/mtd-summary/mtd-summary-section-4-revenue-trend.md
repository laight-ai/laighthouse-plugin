# Breezm Executive MTD Section 4: 매출 추이 (Revenue Trend)

**report_type:** `mtd-summary` — **브리즘(airbridge 기반) 전용** (항상 포함). 최근 6개월
(당월 포함) 라인 차트. 매출은 Airbridge 매출.

> ℹ️ 차트 HTML/Script/월 라벨/각주(MTD 기준·전체 매출 정의·zero-fill)는 전부 빌더가 한다 —
> 모델은 아래 규칙으로 **6개월치 배열 2개**만 빌더 입력 JSON의 `s4`에 넣는다.

## MCP 호출 없음 — section-3의 공유 응답을 재사용

- 이 섹션은 `get_ad_performance_monthly_table`을 직접 호출하지 않는다 — section-3이 받은
  공유 응답(`media` 생략, `group_by:"media"`, 5개월 전~당월, `day_offset`=target_date.day)
  중 **`media`가 `airbridge`인 행만** 쓴다. 예전 단독 호출(`media:"airbridge"`)과 파라미터·
  범위가 동일하므로 결과도 동일하다.

## 빌더 `s4` 필드 (각 배열은 6개, 5개월 전 → 당월 순)

| 필드 | 값 (airbridge 행만 사용) |
|---|---|
| `ad_revenue` | 월별: 광고 채널(`Google Ads`/`Meta Ads`/`Naver Ads`) 행의 `airbridge_revenue` 합 |
| `total_revenue` | 월별: **모든** `channel` 행의 `airbridge_revenue` 합 (광고 채널 외 포함) |
| `labels` | 생략 (빌더가 `YY년 M월` + 당월 `(진행 중)` 자동 생성) |
| `zero_fill` | 생략 (배열에 0이 있으면 빌더가 고정 각주를 자동 표시 — 강제하려면 true/false 명시) |

- **6개월 전부 넣는다** — airbridge에 해당 월 행이 전혀 없으면 두 값 모두 0으로 기록하고
  labels에서 제외하지 않는다. 추정/보간 금지.
- 실제 `channel` 값이 광고 채널 상수와 다르면 조용히 0을 만들지 말고 Executive Summary(`s2`)에
  불일치 불릿을 추가한다.
- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
