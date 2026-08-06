# MTD Section 11: 키워드별 성과

**report_type:** `mtd` (항상 포함)

## MCP 도구 호출: `get_naver_keyword_performance`

```json
{ "brand_name": "...", "start_date": "월초", "end_date": "target_date" }
```
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`). 도구 내부가 페이지네이션을
  자동으로 다 돌며 raw row를 가져오고, `term`(키워드)별 groupby/합산/cpc·ctr·cpm·roas 계산과
  정렬(`-roas,-ad_cost,-revenue,keyword`)까지 **서버에서 이미 끝낸 상태**로 반환한다
  (`term == "-"`인 행은 서버에서 이미 제외됨).
- 응답 `items[]`가 곧 `keyword_performance` 배열이다 (`keyword`/`impressions`/`clicks`/`ad_cost`/
  `cpc`/`ctr`/`cpm`/`purchases`/`revenue`/`roas` 필드 그대로 사용).
- 키워드 수가 매우 많을 수 있으나(수백~수천 건) 이미 합산된 최종 행 목록이므로 다시 집계하지 않는다.

## 필요 데이터 (MCP)
- `keyword_performance`: 키워드 배열
  ```json
  [
    { "keyword": "알파카리그린티라떼", "impressions": 9076, "clicks": 659, "ad_cost": 353722,
      "cpc": 536.76, "ctr": 7.26, "cpm": 38973.34, "purchases": 183, "revenue": 8057615, "roas": 2278 },
    { "keyword": "경부단백질", "impressions": 556, "clicks": 0, "ad_cost": 0,
      "cpc": 0, "ctr": 0, "cpm": 0, "purchases": 0, "revenue": 0, "roas": 0 }
  ]
  ```
