# Executive Daily Section 3: 최근 7일 성과 (Daily Performance, 7-Day)

**report_type:** `daily-summary` (항상 포함). 기준일 포함 최근 7일 일자별 광고 성과 혼합 차트.
- **매출 있음 모드**: 광고비·매출 막대 + ROAS 선.
- **매출 없음 모드**: 클릭 막대 + CTR 선 (광고비·노출·CPC는 툴팁, 안내 각주 자동).

> ℹ️ 차트 HTML/Script/비율 계산/프로모션 브래킷 오버레이는 전부 템플릿+빌더가 한다 — 모델은
> 아래 규칙으로 **역할별 7일치 원자 값 배열**만 빌더 입력 JSON의 `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (section-4/5 공유)

```json
{ "brand_name": "<brand>", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "time_grain": "day", "group_by": ["media"] }
```

- **`filters`를 생략한다** — 이 1회 호출로 날짜별·매체별(`media_list`의 각 값) 행에 더해,
  `media`가 `null`인 행(Organic — 광고비 없이 매출만 귀속, `has_organic`일 때)도 함께 받는다.
  각 행에 cost/revenue/conversion 키 등 지표가 함께 들어있다(별도 매출 응답 없음).
- **이 응답은 section-4/5가 그대로 재사용한다** — section-4는 날짜별·매체별 값(Organic 행 포함)을,
  section-5는 마지막 이틀(D-1, D-0) 행만 쓴다. 세 섹션이 각자 호출하지 않는다.
- 이 섹션(`s3`)의 배열은 **`media`가 `null`이 아닌 행만** 합산한다 — Organic 행은 광고 성과
  차트이므로 여기서는 제외한다(Organic 매출은 section-4의 별도 계열).

## `list_promotions` — 별도 호출 없음, section-2의 공유 응답(7일 룩백)을 재사용

## 빌더 `s3` 필드 (각 배열은 7개, 기준일-6일 → 기준일 순)

| 필드 | 값 |
|---|---|
| `cost` | 날짜별: 매체 행(`media` non-null)의 cost 키 합 (두 모드 공통) |
| `revenue` | 날짜별: 매체 행의 revenue 키 합 — **매출 있음 모드만** |
| `impression` / `click` | 날짜별: 매체 행의 impression / click 키 합 — **매출 없음 모드만** |
| `promotions` | section-2 공유 `list_promotions` 응답 `items[]`의 `{title, date_begin, date_end}`를 **가공 없이 그대로** 담은 배열 (없으면 `[]`) — 인덱스 계산·클램프·범위 밖 제외·`M/D~D` 라벨 생성은 빌더가 한다 |
| `labels` | 생략 (빌더가 `M/D(요일)` 자동 생성) |

- ROAS/CTR/CPC는 넣지 않는다 — 빌더가 원자 값 합으로 계산한다(서버 비율 지표를 더하지 않는다).
- 7일 전부 넣는다 — 0인 날도 0 그대로 (추정/보간 금지).
- 응답의 `metrics` 목록과 실제 `media` 값이 디스커버리 결과(`metric_names`/`media_list`)와
  다르면 조용히 0을 만들지 말고 Executive Summary(`s2`)에 불일치 안내 불릿을 추가한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
