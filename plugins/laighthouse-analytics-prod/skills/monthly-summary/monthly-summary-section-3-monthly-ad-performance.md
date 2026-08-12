# Breezm Executive Monthly Section 3: 월별 광고 성과 (Monthly Ad Performance)

**report_type:** `monthly-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
최근 6개월(당월 포함), 연-월 단위. 매출은 Airbridge 매출, 광고 채널은
`Google Ads`/`Meta Ads`/`Naver Ads` 행.

> ℹ️ 차트 HTML/Script/각주(당월 MTD 문구, zero-fill 고정 문구)/라벨("(진행 중)" 포함)은 전부
> 템플릿+빌더가 처리한다 — 모델은 아래 규칙으로 **6개월치 배열 3개**만 빌더 입력 JSON의
> `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance_monthly_table` × 1 (section-4/5 공유)

```json
{ "brand_name": "breezm", "start_month": "5개월 전 YYYY-MM", "end_month": "당월 YYYY-MM", "group_by": "media", "day_offset": "target_date.day" }
```

- **`media` 파라미터를 생략한다** — 이 1회 호출로 전 매체를 받는다:
  - `media`가 `google`/`meta`/`naver`인 행 — 매체당 월별로 이미 합산된 한 줄씩.
  - `media`가 `airbridge`인 행 — 월별·`channel`별 여러 줄(Google Ads/Meta Ads/Naver Ads/
    Organic/그 외).
  - 그 외(`ga4` 등)는 무시.
- **이 응답은 section-4와 section-5가 그대로 재사용한다** — 세 섹션이 각자 호출하지 않는다.
- **`day_offset: target_date.day`를 반드시 넣는다.** 기간 span 6개월 (도구 제한 24개월 이내).
- ⚠️ `campaign-type` 금지 — airbridge 행이 조용히 누락된다. `group_by`는 문자열 `"media"`.

## 빌더 `s3` 필드 (각 배열은 6개, 5개월 전 → 당월 순)

| 필드 | 값 |
|---|---|
| `ad_cost` | 월별: google/meta/naver 세 행의 `cost` 합 |
| `revenue` | 월별: airbridge 행 중 광고 채널 3종의 `airbridge_revenue` 합 |
| `roas` | 월별: 매출 ÷ 광고비 × 100 (광고비 0인 달은 `null`) |
| `labels` | 생략 (빌더가 `{YY}년 {M}월` + 당월 `(진행 중)` 자동 생성) |

- **6개월 전부 넣는다** — 행이 아예 없는 월도 0으로 채운다 (데이터 적재가 늦게 시작된 경우
  포함, 추정/보간 금지). 광고비만 있고 매출이 없는 월은 매출/ROAS만 0/null. 0이 채워진 월이
  있으면 zero-fill 고정 각주는 빌더가 자동으로 붙인다.
- 첫 airbridge 응답에서 실제 `channel` 값을 확인하고, 상수와 다르면 조용히 0을 만들지 말고
  Executive Summary(`s2`)에 중립 불릿으로 불일치를 명시한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
