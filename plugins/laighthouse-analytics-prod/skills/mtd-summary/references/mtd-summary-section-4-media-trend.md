# MTD Executive Section 4: 매체별 성과 추이 (최근 6개월)

**report_type:** `mtd-summary` (항상 포함). 5개월 전 → 당월 매체별 추이 라인 차트 — 지표
선택(데이터에 있는 지표 전체)과 매체 켜기/끄기 범례가 있다. 모든 월은 각 월 1일~기준일 동기간이다.

**규칙은 `shared/references/media-trend.md`가 단일 소스다.** 이 스킬의 입력:

| 항목 | 값 |
|---|---|
| 차트 기간 응답 | section-3의 공유 응답(6개월, `time_grain:"month"`, `group_by:["media"]`, `day_offset`) — **새로 부르지 않는다** |
| total 응답 | 넘기지 않는다(`day_offset` 범위를 total 한 번으로 만들 수 없다) — 범례는 이번 달 값 |

```json
"s4": { "json": ["<section-3 응답 원문>"] }
```

- 응답이 캡처 스텁으로 왔으면 `json_files`에 경로를 넣는다.
- 0으로 채운 달 각주는 빌더가 자동으로 단다(`zero_fill`로 강제 가능).
- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중".
