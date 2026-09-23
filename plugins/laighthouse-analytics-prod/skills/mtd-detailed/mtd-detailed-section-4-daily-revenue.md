# MTD Section 4: 매체별 일별 추이 (Daily Media Trend)

**report_type:** `mtd-detailed` (항상 포함). 월초~target_date 일별 값을 **매체별 누적 막대**로
보여준다.

- **매출 있음 모드**: 매체별 revenue 키 값. `has_organic`이면 Organic 계열(회색)이 맨 위에
  쌓이고 "막대 전체 = 광고 매체 + Organic" 각주가 붙는다.
- **매출 없음 모드**: 매체별 click 키 값 (제목도 "매체별 {클릭 키} 추이"로 바뀐다). Organic 없음.

> ℹ️ 차트 HTML/Script/두 줄 라벨(날짜+요일)/축·툴팁(합계 포함)/색 배정(디스커버리 순서로 고정,
> 8개 초과 매체는 "그 외 매체"로 묶음)/프로모션 브래킷 오버레이(인덱스 계산·클램프 포함)는 전부
> 빌더가 한다 — 모델은 **매체별 일별 배열과 프로모션 원본 목록**만 빌더 입력 JSON의 `s4`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 + `list_promotions` × 1

```json
{ "brand_name": "<brand>", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "time_grain": "day", "group_by": ["media"] }
```
```json
{ "brand_name": "<brand>", "start_date": "월초 YYYY-MM-01", "end_date": "target_date" }
```

- `get_ad_performance`는 `filters`를 생략한다 — 이 섹션 전용 신규 호출이다(section-3은
  `time_grain:"month"`라 grain이 달라 공유하지 않는다).
- `list_promotions` 응답은 section-2(Executive Summary)/section-5(캠페인 분석)가 그대로
  재사용한다.

## 빌더 `s4` 필드 (일별 배열, 월초 → target_date, 하루도 빠짐없이)

```json
"s4": { "series": [
  {"name": "<media_list 값 1>", "values": [...]},
  {"name": "Organic", "values": [...]}
], "promotions": [...] }
```

| 필드 | 값 |
|---|---|
| `series[].name` | `media_list`의 값 **그대로**, `media_list` 순서. Organic은 `has_organic`이고 매출 있음 모드일 때만 마지막에 `"Organic"` (`media`가 `null`인 행) |
| `series[].values` | 날짜별 그 매체 행의 revenue 키 값(매출 없음 모드: click 키 값). 그 날짜 행이 없으면 0 |
| `promotions` | `list_promotions` 응답 원본을 가공 없이 그대로 |
| `labels` | 생략 (빌더가 자동 생성) |

- 매체를 합치거나 빼지 않는다 — 8개 초과 묶음은 빌더가 한다.
- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중".
