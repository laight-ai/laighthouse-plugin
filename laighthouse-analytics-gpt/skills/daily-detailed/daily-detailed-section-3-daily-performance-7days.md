# Daily Section 3: 최근 7일 성과 (Daily Performance, 7-Day)

**report_type:** `daily-detailed` (항상 포함). 기준일 포함 최근 7일 일자별 광고 성과.
광고비·매출은 `metric_keys`의 cost·revenue 키 값이다.

> ℹ️ 차트 HTML/Script/프로모션 브래킷 오버레이(인덱스 계산·클램프 포함)는 전부 빌더가 한다 —
> 모델은 아래 규칙으로 **7일치 배열 3개와 프로모션 원본 목록**만 빌더 입력 JSON의 `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1

```json
{ "brand_name": "<brand>", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "time_grain": "day" }
```

- **`filters`도 `group_by`도 생략한다** — 이 1회 호출로 날짜당 한 행(`date` 키)의 전체 총계를
  받는다. 매출이 같은 행의 지표로 들어오므로 별도 매출 응답이 없다. (총계 행에는 Organic
  귀속 매출도 포함된다 — 그대로 쓴다.)
- 이 응답은 section-4/5와 **공유되지 않는다** (기간·group_by가 다름 — 각자 호출).

## MCP 도구 호출: `list_promotions` (같은 날짜 범위, 1회)

```json
{ "brand_name": "<brand>", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date" }
```

## 빌더 `s3` 필드 (각 배열은 7개, 기준일-6일 → 기준일 순)

| 필드 | 값 |
|---|---|
| `ad_cost` | 날짜별: 해당 `date` 행의 cost 키 값 |
| `revenue` | 날짜별: 해당 `date` 행의 revenue 키 값 |
| `roas` | 날짜별: 매출 ÷ 광고비 × 100 (광고비 0인 날은 `null`) — 서버 비율 지표의 키 이름은 테넌트별이라 추측하지 않고 역할 키의 원자 값으로 계산한다 |
| `promotions` | `list_promotions` 응답 `items[]`의 `{title, date_begin, date_end}`를 **가공 없이 그대로** 담은 배열 (없으면 `[]`) — 인덱스 계산·범위 밖 제외·라벨 생성은 빌더가 한다 |
| `labels` | 생략 (빌더가 `M/D(요일)` 자동 생성) |

- 7일 전부 넣는다 — 행이 없는 날도 0으로 채우고(매출 0원인 날 포함) 추정/보간하지 않는다.
- 응답의 `metrics` 목록이 디스커버리 `metric_names`와 다르거나 `metric_keys`의 키가 없으면
  조용히 0을 만들지 말고 Executive Summary(`s2`)에 `⚠` 줄로 불일치를 명시한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
