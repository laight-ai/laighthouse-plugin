# MTD Section 9: 캠페인별 성과

**report_type:** `mtd` (항상 포함)

## MCP 도구 호출: `get_naver_campaign_performance`

```json
{ "brand_name": "...", "start_date": "월초", "end_date": "target_date" }
```
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`). 캠페인×채널 단위 groupby/합산/
  roas·ctr·cpc·avg_price 계산과 정렬(`-roas,-ad_cost,-revenue,campaign,channel`)을 **서버에서 이미
  끝낸 상태**로 반환한다 — LLM이 raw row를 그룹핑하거나 비율을 계산할 필요가 없다.
- 응답 `items[]`가 곧 `campaign_performance` 배열이다 (`campaign`/`channel`/`revenue`/`ad_cost`/
  `roas`/`impressions`/`clicks`/`ctr`/`cpc`/`purchases`/`avg_price` 필드 그대로 사용, 그대로 렌더링).

## 필요 데이터 (MCP)
- `campaign_performance`: 캠페인 배열
  ```json
  [
    { "campaign": "05_GT케이(SPBR)_MO", "channel": "NVSHOP", "revenue": 1320543, "ad_cost": 129801,
      "roas": 1017, "impressions": 12778, "clicks": 53, "ctr": 0.41, "cpc": 2449.08,
      "purchases": 17, "avg_price": 77679 }
  ]
  ```
- `roas`, `ctr`는 % 단위 숫자, `cpc`/`avg_price`는 원 단위
