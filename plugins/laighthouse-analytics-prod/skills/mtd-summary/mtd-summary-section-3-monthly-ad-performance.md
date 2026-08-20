# Breezm Executive MTD Section 3: 월별 광고 성과 (Monthly Ad Performance)

**report_type:** `mtd-summary` — **브리즘(airbridge 기반) 전용** (항상 포함). 최근 6개월
(당월 포함) 혼합 차트. 매출은 Airbridge 귀속 매출(`매출_AB`).

> ℹ️ 차트 HTML/Script/월 라벨/각주 문구는 전부 빌더가 한다 — 모델은 아래 규칙으로 **6개월치
> 배열 3개**만 빌더 입력 JSON의 `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (`media` 생략 — section-4/5 공유)

```json
{ "brand_name": "breezm", "start_date": "5개월 전 YYYY-MM-01", "end_date": "target_date", "time_grain": "month", "group_by": ["media"], "day_offset": "target_date.day" }
```

- **`media` 파라미터를 생략한다** — 이 1회 호출로 월별·매체별(`Google`/`Meta`/`Naver`) 행을
  전부 받는다. 각 행에 `month`("YYYY-MM") 키와 `광고비`/`매출_AB`/`예약완료_AB` 등 지표가
  함께 들어있다(별도 매출 응답 없음).
- **이 응답은 section-4와 section-5가 그대로 재사용한다** — 세 섹션이 각자 호출하지 않는다
  (section-5가 필요한 전월~당월 2개월은 이 6개월 범위에 완전히 포함되고 `day_offset`도 동일).
- **`day_offset: target_date.day`를 반드시 넣는다** — 없으면 당월이 실제 오늘 날짜까지 누적돼
  section-1의 target_date 기준 수치와 어긋난다.

## 빌더 `s3` 필드 (각 배열은 6개, 5개월 전 → 당월 순)

| 필드 | 값 |
|---|---|
| `ad_cost` | 월별: 세 매체 행의 `광고비` 합 |
| `revenue` | 월별: 세 매체 행의 `매출_AB` 합 |
| `roas` | 월별: 매출 ÷ 광고비 × 100 (광고비 0인 달은 `null`) — 매체별 행을 합산했으므로 행의 `ROAS_AB`를 더하지 말고 원자 지표 합으로 계산한다 |
| `labels` | 생략 (빌더가 `YY년 M월` + 당월 `(진행 중)` 자동 생성) |
| `zero_fill` | 생략 (배열에 0이 있으면 빌더가 고정 각주를 자동 표시 — 강제하려면 true/false 명시) |

- **6개월 전부 넣는다** — 행이 없는 월도 0으로 채워 labels에서 제외하지 않는다 (광고비만 있고
  매출이 없는 월은 매출/ROAS만 0/null, 광고비는 실제 값). 추정/보간 금지.
- MTD 기준 각주("이번달 데이터는 1일부터 기준일까지")와 zero-fill 고정 각주는 빌더가 넣는다.
- 첫 응답에서 `metrics` 목록과 실제 `media` 값을 확인하고, 기대 값과 다르면 조용히 0을
  만들지 말고 Executive Summary(`s2`)에 불일치 불릿을 추가한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
