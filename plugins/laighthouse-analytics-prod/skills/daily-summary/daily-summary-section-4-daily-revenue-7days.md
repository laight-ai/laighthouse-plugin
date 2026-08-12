# Breezm Executive Daily Section 4: 일일 매출 현황 (최근 7일)

**report_type:** `daily-summary` — **브리즘(airbridge 기반) 전용** (항상 포함). 기준일 포함
**최근 7일** 일별 광고 매출 vs 전체 매출 라인 차트 — section-3보다 간결하게 임원이 매출
추이만 한눈에 보는 섹션이다. 매출은 Airbridge 매출.

> ℹ️ 라인 차트 HTML/Script/2줄 라벨(`[M/D, (요일)]`)/₩ 축·tooltip/프로모션 브래킷(라인 차트라
> 밴드 폭 보정 없음)은 전부 템플릿+빌더가 한다 — 모델은 아래 규칙으로 **7일치 배열 2개**만
> 빌더 입력 JSON의 `s4`에 넣는다.

## MCP 호출 없음 — section-3/2의 공유 응답을 재사용

- `get_ad_performance_daily_table`: section-3의 공유 응답(`media` 생략, `group_by:"media"`,
  기준일 6일 전 ~ target_date) 중 **`media`가 `airbridge`인 행만** 쓴다.
- `list_promotions`: section-2의 공유 응답(7일 룩백)을 재사용 — 범위 밖 항목은 빌더 clamp가
  자동 제외.

## 빌더 `s4` 필드 (각 배열은 7개, 기준일-6일 → 기준일 순)

| 필드 | 값 |
|---|---|
| `ad_revenue` | 날짜별: 광고 채널(`Google Ads`/`Meta Ads`/`Naver Ads`) 행의 `airbridge_revenue` 합 |
| `total_revenue` | 날짜별: **모든** `channel` 행의 `airbridge_revenue` 합 |
| `promotions` | section-2 공유 응답 `items[]`의 `{title, date_begin, date_end}` 그대로 (없으면 `[]`) — 빌더가 이 섹션용 `M월 D일~D일` 라벨로 생성 |
| `labels` | 생략 (빌더가 `[["M/D","(요일)"], ...]` 2줄 라벨 자동 생성) |

- 7일 전부 넣는다 — 매출 0원인 날도 0 그대로 (추정/보간 금지).
- 실제 `channel` 값이 상수와 다르면 조용히 0을 만들지 말고 `s2`에 불일치 안내 불릿을 추가한다.
- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중" 카드.
