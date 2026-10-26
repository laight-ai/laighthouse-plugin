# Executive Daily Section 4: 매체별 성과 추이 (최근 7일)

**report_type:** `daily-summary` (항상 포함). 기준일 포함 **최근 7일** 매체별 추이 라인 차트 —
지표 선택(데이터에 있는 지표 전체)과 매체 켜기/끄기 범례가 있다.

**규칙은 `shared/references/media-trend.md`가 단일 소스다.** 이 스킬의 입력:

| 항목 | 값 |
|---|---|
| 차트 기간 응답 | section-3의 공유 응답(기준일 6일 전~target_date, `time_grain:"day"`, `group_by:["media"]`) — **새로 부르지 않는다** |
| total 응답 | `get_ad_performance` ×1 — 같은 7일, `time_grain:"total"`, `group_by:["media"]`, `metrics` 생략 (section-3 호출과 같은 배치) |
| 프로모션 | section-2 공유 `list_promotions` 응답 그대로 |

```json
"s4": { "json": ["<section-3 응답 원문>"], "total_json": ["<total 응답 원문>"], "promotions": [...] }
```

- 응답이 캡처 스텁으로 왔으면 `json_files`/`total_json_files`에 경로를 넣는다.
- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중".
