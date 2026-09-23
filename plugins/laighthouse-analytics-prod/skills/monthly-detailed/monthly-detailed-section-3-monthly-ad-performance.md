# Monthly Section 3: 월별 광고 성과 (Monthly Ad Performance)

**report_type:** `monthly-detailed` (항상 포함). 최근 6개월(당월 포함), 연-월 단위 광고 성과 혼합
차트.
- **매출 있음 모드**: 광고비·매출 막대 + ROAS 선.
- **매출 없음 모드**: 클릭 막대 + CTR 선 (광고비·노출·CPC는 툴팁, 안내 각주 자동).

> ℹ️ 차트 HTML/Script/범례(`metric_keys` 값)/비율 계산/각주(당월 부분월 표기, zero-fill 안내)/
> 라벨은 전부 빌더(공용 킷)가 한다 — 모델은 아래 규칙으로 **역할별 6개월치 원자 값 배열**만
> 빌더 입력 JSON의 `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (section-4·section-5 매체 레벨 공유)

```json
{ "brand_name": "<brand>", "start_date": "5개월 전 YYYY-MM-01", "end_date": "target_date", "time_grain": "month", "group_by": ["media"], "day_offset": <target_date.day (정수)> }
```

- **`filters`·`metrics`를 생략한다** — 이 1회 호출로 월별·매체별(`media_list`의 각 값) 행에
  전체 지표가 들어오고, `has_organic`이면 `media`가 `null`인 행(Organic — 광고비 없이 매출만
  귀속)도 함께 받는다. 각 행에 `month`("YYYY-MM") 키가 있다.
- **`day_offset: target_date.day`를 반드시 넣는다** — 범위 내 **모든 월**에 균일하게 적용되어
  매달 "기준일과 같은 일자까지"라는 동일 기준으로 비교된다.
- **이 응답은 section-4와 section-5가 그대로 재사용한다** — section-4는 M-1·M0 두 달 행을,
  section-5 계층 표는 이 응답 원문을 매체 레벨로 쓴다(원문을 `s5.json`에 넣는다). 둘 다 별도
  매체 단위 호출이 없다.

## 빌더 `s3` 필드 (각 배열은 6개, 5개월 전 → 당월 순)

광고 성과 차트이므로 **`media`가 `null`이 아닌 행만** 월별로 합산한다(Organic 제외).

| 필드 | 값 |
|---|---|
| `cost` | 월별 cost 키 합 (두 모드 공통) |
| `revenue` | 월별 revenue 키 합 — **매출 있음 모드만** |
| `impression` / `click` | 월별 impression / click 키 합 — **매출 없음 모드만** |
| `labels` | 생략 (빌더가 `{YY}년 {M}월` 자동 생성, 당월은 `(진행 중)` 접미사까지) |

- ROAS/CTR/CPC는 넣지 않는다 — 빌더가 원자 값 합으로 계산한다(서버 비율 지표를 더하지 않는다).
- **6개월 전부 넣는다** — 행이 없는 월(데이터 적재가 늦게 시작된 경우 포함)도 0으로 채운다
  (추정/보간 금지). 0이 채워진 월이 있으면 zero-fill 각주는 빌더가 자동으로 붙인다.
- 응답의 `metrics` 목록과 실제 `media` 값이 디스커버리 결과(`metric_names`/`media_list`)와
  다르면 조용히 0을 만들지 말고 Executive Summary(`s2`)에 `⚠` 줄로 불일치를 명시한다.
- 데이터가 비어있으면 `s3` 자체를 넣지 않는다 → 빌더가 "데이터 준비 중" 카드로 렌더링.
