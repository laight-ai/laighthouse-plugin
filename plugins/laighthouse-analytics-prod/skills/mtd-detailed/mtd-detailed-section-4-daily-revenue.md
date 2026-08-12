# Breezm MTD Section 4: 일일 매출 현황 (Daily Revenue)

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 월초~target_date
일별 광고 매출 vs 전체 매출. 매출은 Airbridge 매출.

> ℹ️ 차트 HTML/Script/두 줄 라벨(날짜+요일)/프로모션 브래킷 오버레이(인덱스 계산·클램프 포함)는
> 전부 빌더가 한다 — 모델은 **일별 배열 2개와 프로모션 원본 목록**만 빌더 입력 JSON의 `s4`에
> 넣는다.

## MCP 도구 호출: `get_ad_performance_daily_table` × 1

```json
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "airbridge", "group_by": "media" }
```

- MTD 범위이므로 도구 제한(31일 이내)을 항상 만족한다. ⚠️ `campaign-type` 금지.

## MCP 도구 호출: `list_promotions` (같은 날짜 범위, 1회)

```json
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date" }
```

- 이 응답은 section-2(Executive Summary)/section-5(캠페인 분석)가 그대로 재사용한다.

## 빌더 `s4` 필드 (각 배열은 월초 → target_date 순, 하루도 빠짐없이)

| 필드 | 값 |
|---|---|
| `ad_revenue` | 일별: 광고 채널(`Google Ads`/`Meta Ads`/`Naver Ads`) 행의 `airbridge_revenue` 합 |
| `total_revenue` | 일별: 모든 `channel` 행의 `airbridge_revenue` 합 (오거닉 포함) |
| `promotions` | `list_promotions` 응답 `items[]`의 `{title, date_begin, date_end}`를 **가공 없이 그대로** 담은 배열 (없으면 `[]`) — 인덱스 계산·클램프·범위 밖 제외·range_label 생성은 빌더가 한다 |
| `labels` | 생략 (빌더가 `[M/D, (요일)]` 두 줄 라벨 자동 생성) |

- 월초부터 기준일까지 전부 넣는다 — 매출 0원인 날도 0 그대로 (추정/보간 금지). 격일 축약 금지.
- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중" 카드.
- 실제 `channel` 값이 상수와 다르면 조용히 0을 만들지 말고 Executive Summary(`s2`)에 `⚠` 줄로
  불일치를 명시한다.
