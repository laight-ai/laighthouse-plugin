# Executive Daily Section 4: 매체별 매출 추이 (최근 7일)

**report_type:** `daily-summary` (항상 포함). 기준일 포함 **최근 7일** 일별 값을 **매체별 누적
막대**로 보여준다 — 임원이 "어느 매체가 얼마를 만들었는지"를 한눈에 보는 섹션이다.

- **매출 있음 모드**: 매체별 revenue 키 값. `has_organic`이면 Organic 계열(회색)이 맨 위에
  쌓이고 "막대 전체 = 광고 매체 + Organic" 각주가 붙는다.
- **매출 없음 모드**: 매체별 click 키 값 (제목도 "매체별 {클릭 키} 추이"로 바뀐다). Organic 없음.

> ℹ️ 차트 HTML/Script/2줄 라벨(`[M/D, (요일)]`)/축·툴팁(합계 포함)/색 배정(디스커버리 순서로
> 고정, 8개 초과 매체는 "그 외 매체"로 묶음)/프로모션 브래킷은 전부 템플릿+빌더가 한다 — 모델은
> 아래 규칙으로 **매체별 7일 배열**만 빌더 입력 JSON의 `s4`에 넣는다.

## MCP 호출 없음 — section-3/2의 공유 응답을 재사용

- `get_ad_performance`(day grain, `group_by:["media"]`): section-3의 공유 응답.
- `list_promotions`: section-2의 공유 응답(7일 룩백)을 재사용 — 범위 밖 항목은 빌더 clamp가
  자동 제외.

## 빌더 `s4` 필드 (각 배열 7개, 기준일-6일 → 기준일 순)

```json
"s4": { "series": [
  {"name": "<media_list 값 1>", "values": [..7개..]},
  {"name": "<media_list 값 2>", "values": [..7개..]},
  {"name": "Organic", "values": [..7개..]}
], "promotions": [...] }
```

| 필드 | 값 |
|---|---|
| `series[].name` | `media_list`의 값 **그대로**, `media_list` 순서. Organic은 `has_organic`이고 매출 있음 모드일 때만 마지막에 `"Organic"` |
| `series[].values` | 날짜별 그 매체 행의 revenue 키 값(매출 없음 모드: click 키 값). 그 날짜 행이 없으면 0 |
| `promotions` | section-2 공유 `list_promotions` 응답을 가공 없이 그대로 |
| `labels` | 생략 (빌더가 자동 생성) |

- 매체를 합치거나 빼지 않는다 — 8개 초과 묶음은 빌더가 한다.
- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중".
