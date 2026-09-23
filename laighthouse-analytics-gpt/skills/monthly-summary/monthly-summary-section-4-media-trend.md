# Executive Monthly Section 4: 매체별 매출 추이 (최근 6개월)

**report_type:** `monthly-summary` (항상 포함). 최근 6개월(당월 포함) 월별 값을 **매체별 누적
막대**로 보여준다 — 임원이 "어느 매체가 얼마를 만들었는지"를 한눈에 보는 섹션이다.

- **매출 있음 모드**: 매체별 revenue 키 값. `has_organic`이면 Organic 계열(회색)이 맨 위에
  쌓이고 "막대 전체 = 광고 매체 + Organic" 각주가 붙는다.
- **매출 없음 모드**: 매체별 click 키 값 (제목도 "매체별 {클릭 키} 추이"로 바뀐다). Organic 없음.

> ℹ️ 차트 HTML/Script/라벨/축·툴팁(합계 포함)/색 배정(디스커버리 순서로 고정, 8개 초과 매체는
> "그 외 매체"로 묶음)/각주(당월 MTD 문구, Organic 정의, zero-fill)는 전부 템플릿+빌더(공용 킷
> `media_trend_spec`)가 한다 — 모델은 아래 규칙으로 **매체별 6개월 배열**만 빌더 입력 JSON의
> `s4`에 넣는다.

## MCP 호출 없음 — section-3의 공유 응답을 재사용

`monthly-summary-section-3-monthly-ad-performance.md`가 1회 호출한 `get_ad_performance`
(`filters`·`metrics` 생략, `time_grain:"month"`, `group_by:["media"]`, 5개월 전~당월,
`day_offset`=target_date.day) 응답의 월별·매체별 행을 그대로 쓴다.

## 빌더 `s4` 필드 (각 배열 6개, 5개월 전 → 당월 순)

```json
"s4": { "series": [
  {"name": "<media_list 값 1>", "values": [..6개..]},
  {"name": "<media_list 값 2>", "values": [..6개..]},
  {"name": "Organic", "values": [..6개..]}
] }
```

| 필드 | 값 |
|---|---|
| `series[].name` | `media_list`의 값 **그대로**, `media_list` 순서. Organic은 `has_organic`이고 매출 있음 모드일 때만 마지막에 `"Organic"` (`media`가 `null`인 행) |
| `series[].values` | 월별 그 매체 행의 revenue 키 값(매출 없음 모드: click 키 값). 그 월 행이 없으면 0 |
| `labels` | 생략 (빌더가 section-3과 같은 규칙으로 자동 생성) |

- 매체를 합치거나 빼지 않는다 — 8개 초과 묶음은 빌더가 한다.
- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중".
