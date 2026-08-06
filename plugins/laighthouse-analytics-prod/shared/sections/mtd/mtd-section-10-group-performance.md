# MTD Section 10: 광고 그룹별 성과

**report_type:** `mtd` (항상 포함)

## MCP 도구 호출: `get_naver_group_performance`

```json
{ "brand_name": "...", "start_date": "월초", "end_date": "target_date" }
```
- naver 전용 MCP 도구 (`laighthouse-prism/src/mcp_server/tools_naver.py`). group_name 단위 groupby/
  합산/cpc·roas 계산과 정렬(`-roas,-ad_cost,-revenue,group`)을 **서버에서 이미 끝낸 상태**로 반환한다.
- 응답 `items[]`가 곧 `group_performance` 배열이다 (`group`/`impressions`/`clicks`/`cpc`/`ad_cost`/
  `revenue`/`roas` 필드 그대로 사용).
- mtd-section-11(광고 그룹별 심층 분석)이 동일 호출 결과를 재사용한다 (중복 호출 방지)

## 필요 데이터 (MCP)
- `group_performance`: 광고그룹 배열
  ```json
  [
    { "group": "002_브랜드_공용_통합", "impressions": 3528, "clicks": 108, "cpc": 346.41, "ad_cost": 37412, "revenue": 666438 },
    { "group": "0412_브랜드_단백질_단백질_영캐어", "impressions": 588, "clicks": 25, "cpc": 378.16, "ad_cost": 9454, "revenue": 258053 }
  ]
  ```
