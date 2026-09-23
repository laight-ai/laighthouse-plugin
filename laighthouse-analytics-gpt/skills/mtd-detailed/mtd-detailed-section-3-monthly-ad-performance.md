# MTD Section 3: 월별 광고 성과 (Monthly Ad Performance)

**report_type:** `mtd-detailed` (항상 포함). 최근 6개월(당월 포함), 연-월 단위 혼합 차트.
- **매출 있음 모드**: 광고비·매출 막대 + ROAS 선.
- **매출 없음 모드**: 클릭 막대 + CTR 선 (광고비·노출·CPC는 툴팁, 안내 각주 자동).

> ℹ️ 차트 HTML/Script/월 라벨/비율 계산/범례(`metric_keys` 값)/각주(당월 기준일·0 채움 월)는
> 전부 템플릿+빌더(공용 킷)가 처리한다 — 모델은 아래 규칙으로 **역할별 6개월치 원자 값 배열**만
> 빌더 입력 JSON의 `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (`filters` 생략 — section-2/7 공유)

```json
{ "brand_name": "<brand>", "start_date": "5개월 전 YYYY-MM-01", "end_date": "target_date", "time_grain": "month", "group_by": ["media"], "day_offset": <target_date.day (정수)> }
```

- **`metrics`·`filters` 생략** — 1회 호출로 월별·매체별(`media_list` 전 매체 + Organic `null` 행)
  행을 전체 지표와 함께 받는다. 각 행에 `month`("YYYY-MM") 키와 역할 키 지표가 들어있다.
- **`day_offset: target_date.day` 필수** — 없으면 당월이 실제 오늘 날짜까지 누적되어 섹션 1/6과
  어긋나고, 전월이 동기간으로 잘리지 않는다.
- **이 응답을 section-2(전월 동기 비교)와 section-7(계층 표 매체 레벨)이 그대로 재사용한다** —
  section-7에는 응답 원문 문자열을 `s7.json`에 넣는다.

## 빌더 `s3` 필드 (각 배열은 6개, 5개월 전 → 당월 순)

| 필드 | 값 |
|---|---|
| `cost` | 월별: 매체 행(`media` non-null)의 cost 키 합 (두 모드 공통) |
| `revenue` | 월별: 매체 행의 revenue 키 합 — **매출 있음 모드만** |
| `impression` / `click` | 월별: 매체 행의 impression / click 키 합 — **매출 없음 모드만** |
| `labels` | 생략 (빌더가 `{YY}년 {M}월` + 당월 `(진행 중)` 자동 생성) |
| `zero_fill_note` | 생략 (막대가 전부 0인 월이 있으면 빌더가 월 목록을 담은 각주를 자동 생성) |

- ROAS/CTR/CPC는 넣지 않는다 — 빌더가 원자 값 합으로 계산한다(서버 비율 지표를 더하지 않는다).
- **최근 6개월 고정** — 행이 없는 월도 제외하지 않고 0으로 채워 항상 6개 전부 넣는다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → "데이터 준비 중" 카드 (추정/보간 금지).
- 응답의 `metrics` 목록과 `media` 값이 디스커버리와 다르면 조용히 0을 만들지 말고 Executive
  Summary(`s2`)에 `⚠` 줄로 불일치를 명시한다.
