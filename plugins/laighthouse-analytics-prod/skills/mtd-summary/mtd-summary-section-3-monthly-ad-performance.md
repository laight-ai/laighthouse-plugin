# Executive MTD Section 3: 월별 광고 성과 (Monthly Ad Performance)

**report_type:** `mtd-summary` (항상 포함). 최근 6개월(당월 포함) 광고 성과 혼합 차트.
- **매출 있음 모드**: 광고비·매출 막대 + ROAS 선.
- **매출 없음 모드**: 클릭 막대 + CTR 선 (광고비·노출·CPC는 툴팁, 안내 각주 자동).

> ℹ️ 차트 HTML/Script/월 라벨/비율 계산/범례(`metric_keys` 값)/각주 문구는 전부 템플릿+빌더(공용
> 킷)가 한다 — 모델은 아래 규칙으로 **역할별 6개월치 원자 값 배열**만 빌더 입력 JSON의 `s3`에
> 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (`filters` 생략 — section-4/5 공유)

```json
{ "brand_name": "<brand>", "start_date": "5개월 전 YYYY-MM-01", "end_date": "target_date", "time_grain": "month", "group_by": ["media"], "day_offset": <target_date.day (정수)> }
```

- **`metrics`·`filters`를 생략한다** — 이 1회 호출로 월별·매체별(`media_list`의 각 값) 행에 더해,
  `media`가 `null`인 행(Organic — 광고비 없이 매출만 귀속, `has_organic`일 때)도 함께 받는다.
  각 행에 `month`("YYYY-MM") 키와 역할 키 지표가 함께 들어있다(별도 매출 응답 없음).
- **이 응답은 section-4와 section-5가 그대로 재사용한다** — 세 섹션이 각자 호출하지 않는다
  (section-5가 필요한 전월~당월 2개월은 이 6개월 범위에 완전히 포함되고 `day_offset`도 동일).
  이 섹션(`s3`)의 배열은 **`media`가 `null`이 아닌 행만** 합산한다 — Organic 행은 광고 성과
  차트이므로 여기서는 제외한다(Organic은 section-4의 별도 계열).
- **`day_offset: target_date.day`를 반드시 넣는다** — 없으면 당월이 실제 오늘 날짜까지 누적돼
  section-1의 target_date 기준 수치와 어긋난다.

## 빌더 `s3` 필드 (각 배열은 6개, 5개월 전 → 당월 순)

| 필드 | 값 |
|---|---|
| `cost` | 월별: 매체 행(`media` non-null)의 cost 키 합 (두 모드 공통) |
| `revenue` | 월별: 매체 행의 revenue 키 합 — **매출 있음 모드만** |
| `impression` / `click` | 월별: 매체 행의 impression / click 키 합 — **매출 없음 모드만** |
| `labels` | 생략 (빌더가 `YY년 M월` + 당월 `(진행 중)` 자동 생성) |
| `zero_fill` | 생략 (막대 배열에 0이 있으면 빌더가 고정 각주를 자동 표시 — 강제하려면 true/false 명시) |

- ROAS/CTR/CPC는 넣지 않는다 — 빌더가 원자 값 합으로 계산한다(서버 비율 지표를 더하지 않는다).
- **6개월 전부 넣는다** — 행이 없는 월도 0으로 채워 labels에서 제외하지 않는다. 추정/보간 금지.
- MTD 기준 각주("이번달 데이터는 1일부터 기준일까지")와 zero-fill 고정 각주는 빌더가 넣는다.
- 응답의 `metrics` 목록과 실제 `media` 값이 디스커버리 결과(`metric_names`/`media_list`)와
  다르면 조용히 0을 만들지 말고 Executive Summary(`s2`)에 중립 불릿으로 불일치를 명시한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
