# Daily Section 3: 최근 7일 성과 (Daily Performance, 7-Day)

**report_type:** `daily-detailed` (항상 포함). 기준일 포함 최근 7일 일자별 광고 성과 혼합 차트.
- **매출 있음 모드**: 광고비·매출 막대 + ROAS 선.
- **매출 없음 모드**: 클릭 막대 + CTR 선 (광고비·노출·CPC는 툴팁, 안내 각주 자동).

> ℹ️ 차트 HTML/Script/비율 계산/프로모션 브래킷 오버레이는 전부 빌더가 한다 — 모델은 아래
> 규칙으로 **역할별 7일치 원자 값 배열과 프로모션 원본 목록**만 빌더 입력 JSON의 `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (section-4 매체 레벨 공유)

```json
{ "brand_name": "<brand>", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "time_grain": "day", "group_by": ["media"] }
```

- **`filters`·`metrics` 생략** — 날짜별·매체별 행에 전체 지표가 들어온다. `media`가 `null`인
  행(Organic)도 온다.
- **이 응답은 section-4 계층 표의 매체 레벨로 그대로 재사용한다** — 원문을 `s4.json`에 넣는다.

## MCP 도구 호출: `list_promotions` (같은 날짜 범위, 1회)

```json
{ "brand_name": "<brand>", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date" }
```

## 빌더 `s3` 필드 (각 배열은 7개, 기준일-6일 → 기준일 순)

광고 성과 차트이므로 **`media`가 `null`이 아닌 행만** 날짜별로 합산한다(Organic 제외).

| 필드 | 값 |
|---|---|
| `cost` | 날짜별 cost 키 합 (두 모드 공통) |
| `revenue` | 날짜별 revenue 키 합 — **매출 있음 모드만** |
| `impression` / `click` | 날짜별 impression / click 키 합 — **매출 없음 모드만** |
| `promotions` | `list_promotions` 응답 `items[]`의 `{title, date_begin, date_end}`를 **가공 없이 그대로** 담은 배열 (없으면 `[]`) |
| `labels` | 생략 (빌더가 `M/D(요일)` 자동 생성) |

- ROAS/CTR/CPC는 넣지 않는다 — 빌더가 원자 값 합으로 계산한다(서버 비율 지표를 더하지 않는다).
- 7일 전부 넣는다 — 행이 없는 날도 0으로 채우고 추정/보간하지 않는다.
- 응답의 `metrics` 목록에 `metric_keys`의 키가 없으면 조용히 0을 만들지 말고 Executive
  Summary(`s2`)에 `⚠` 줄로 불일치를 명시한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
