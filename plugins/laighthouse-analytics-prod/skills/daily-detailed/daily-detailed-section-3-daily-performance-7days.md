# Breezm Daily Section 3: 최근 7일 성과 (Daily Performance, 7-Day)

**report_type:** `daily-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 기준일 포함
최근 7일 일자별 광고 성과. 매출은 Airbridge 매출, 광고 채널은 `Google Ads`/`Meta Ads`/
`Naver Ads` 행.

> ℹ️ 차트 HTML/Script/프로모션 브래킷 오버레이(인덱스 계산·클램프 포함)는 전부 빌더가 한다 —
> 모델은 아래 규칙으로 **7일치 배열 3개와 프로모션 원본 목록**만 빌더 입력 JSON의 `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance_daily_table` × 1

```json
{ "brand_name": "breezm", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "media" }
```

- **`media` 파라미터를 생략한다** — 이 1회 호출로 전 매체를 받는다:
  - `media`가 `google`/`meta`/`naver`인 행 — 매체당 날짜별로 이미 합산된 한 줄.
  - `media`가 `airbridge`인 행 — 날짜별·`channel`별 여러 줄.
  - 그 외(`ga4` 등)는 무시.
- 이 응답은 section-4/5와 **공유되지 않는다** (기간·group_by가 다름 — 각자 호출).
- ⚠️ `campaign-type` 금지, `group_by`는 문자열 `"media"` 그대로.

## MCP 도구 호출: `list_promotions` (같은 날짜 범위, 1회)

```json
{ "brand_name": "breezm", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date" }
```

## 빌더 `s3` 필드 (각 배열은 7개, 기준일-6일 → 기준일 순)

| 필드 | 값 |
|---|---|
| `ad_cost` | 날짜별: google/meta/naver 세 행의 `cost` 합 |
| `revenue` | 날짜별: airbridge 행 중 광고 채널 3종의 `airbridge_revenue` 합 |
| `roas` | 날짜별: 매출 ÷ 광고비 × 100 (광고비 0인 날은 `null`) |
| `promotions` | `list_promotions` 응답 `items[]`의 `{title, date_begin, date_end}`를 **가공 없이 그대로** 담은 배열 (없으면 `[]`) — 인덱스 계산·범위 밖 제외·라벨 생성은 빌더가 한다 |
| `labels` | 생략 (빌더가 `M/D(요일)` 자동 생성) |

- 7일 전부 넣는다 — 매출 0원인 날도 0 그대로 (추정/보간 금지).
- 첫 airbridge 응답에서 실제 `channel` 값을 확인하고, 상수와 다르면 조용히 0을 만들지 말고
  Executive Summary(`s2`)에 `⚠` 줄로 불일치를 명시한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
