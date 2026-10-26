# MTD Section 4: 매체별 일별 성과 추이 (월초~기준일)

**report_type:** `mtd-detailed` (항상 포함). 월초~기준일 **일별** 매체별 추이 라인 차트 — 지표
선택(데이터에 있는 지표 전체), 매체 켜기/끄기 범례, 프로모션 브래킷이 있다.

**규칙은 `shared/references/media-trend.md`가 단일 소스다.** 이 스킬의 입력:

## MCP 도구 호출: `get_ad_performance` × 2 (같은 배치)

```json
{ "brand_name": "<brand>", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "time_grain": "day", "group_by": ["media"] }
{ "brand_name": "<brand>", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "time_grain": "total", "group_by": ["media"] }
```

- 둘 다 **`metrics`·`filters` 생략**. 첫 번째가 차트, 두 번째가 범례의 기간 전체 값이다.
- `list_promotions` ×1 (월초~target_date)도 같은 배치에서 부른다.

## 빌더 `s4` 입력

```json
"s4": { "json": ["<day 응답 원문>"], "total_json": ["<total 응답 원문>"], "promotions": [<list_promotions 응답 그대로>] }
```

- 응답이 캡처 스텁으로 왔으면 `json_files`/`total_json_files`에 경로를 넣는다.
- 데이터가 비어있으면 `s4` 자체를 넣지 않는다 → "데이터 준비 중".
