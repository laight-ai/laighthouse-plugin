# MTD Section 7: 매체별 예산 소진 현황

**report_type:** `mtd` (항상 포함)

## MCP 도구 호출: `get_naver_channel_budget_progress`

```json
{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date" }
```
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`). 채널 라벨 매핑
  (`nvad:BRS`→네이버 브랜드검색 등), `budget_goal`/`daily_budget`/`spent`/`daily_spent_avg`/
  `spent_rate` 계산, `total` 합계 행까지 **서버에서 이미 끝낸 상태**로 반환한다.
- 응답 `items[]`가 곧 `media_budget_progress.rows`, `total`이 곧 `media_budget_progress.total`이다
  (필드명은 `media`↔`channel`만 다르므로 그대로 매핑해 렌더링).

## 필요 데이터 (MCP)
- `media_budget_progress.channel_group`: 채널 그룹 레이블 (예: 'SA / DA')
- `media_budget_progress.rows`: 매체별 배열
  ```json
  [
    { "channel": "네이버 브랜드검색", "spent_rate": 55.9, "budget_goal": 19099909, "spent": 9237537, "daily_budget": 10669754, "daily_spent_avg": 8421155 },
    { "channel": "네이버 파워링크", "spent_rate": 50.4, "budget_goal": 4909091, "spent": 2375367, "daily_budget": 2473472, "daily_spent_avg": 2435419 }
  ]
  ```
- `media_budget_progress.total`: 합계 행 (동일 필드 구조, `media` 없음)
