# Breezm Executive Monthly Section 3: 월별 광고 성과 (Monthly Ad Performance)

**report_type:** `monthly-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
최근 6개월(당월 포함), 연-월 단위. 매출은 Airbridge 귀속 매출(`매출_AB`).

> ℹ️ 차트 HTML/Script/각주(당월 MTD 문구, zero-fill 고정 문구)/라벨("(진행 중)" 포함)은 전부
> 템플릿+빌더가 처리한다 — 모델은 아래 규칙으로 **6개월치 배열 3개**만 빌더 입력 JSON의
> `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (section-4/5 공유)

```json
{ "brand_name": "breezm", "start_date": "5개월 전 YYYY-MM-01", "end_date": "target_date", "time_grain": "month", "group_by": ["media"], "day_offset": "target_date.day" }
```

- **`media` 파라미터를 생략한다** — 이 1회 호출로 월별·매체별(`Google`/`Meta`/`Naver`) 행에
  더해, `media`가 `null`인 행(Organic — 광고비 없이 매출만 귀속)도 함께 받는다. 각 행에
  `month`("YYYY-MM") 키와 `광고비`/`매출_AB`/`예약완료_AB` 등 지표가 함께 들어있다(별도 매출
  응답 없음).
- **이 응답은 section-4와 section-5가 그대로 재사용한다** — 세 섹션이 각자 호출하지 않는다.
  이 섹션(`s3`)의 `ad_cost`/`revenue`는 **세 매체 행만** 합산한다 — `null`(Organic) 행은
  광고 성과 차트이므로 여기서는 제외한다(전체 매출이 필요한 곳은 section-4).
- **`day_offset: target_date.day`를 반드시 넣는다** — 범위 내 모든 월에 균일하게 적용된다.

## 빌더 `s3` 필드 (각 배열은 6개, 5개월 전 → 당월 순)

| 필드 | 값 |
|---|---|
| `ad_cost` | 월별: 세 매체 행의 `광고비` 합 |
| `revenue` | 월별: 세 매체 행의 `매출_AB` 합 |
| `roas` | 월별: 매출 ÷ 광고비 × 100 (광고비 0인 달은 `null`) — 매체별 행을 합산했으므로 행의 `ROAS_AB`를 더하지 말고 원자 지표 합으로 계산한다 |
| `labels` | 생략 (빌더가 `{YY}년 {M}월` + 당월 `(진행 중)` 자동 생성) |

- **6개월 전부 넣는다** — 행이 아예 없는 월도 0으로 채운다 (데이터 적재가 늦게 시작된 경우
  포함, 추정/보간 금지). 광고비만 있고 매출이 없는 월은 매출/ROAS만 0/null. 0이 채워진 월이
  있으면 zero-fill 고정 각주는 빌더가 자동으로 붙인다.
- 첫 응답에서 `metrics` 목록과 실제 `media` 값을 확인하고, 기대 값과 다르면 조용히 0을
  만들지 말고 Executive Summary(`s2`)에 중립 불릿으로 불일치를 명시한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
