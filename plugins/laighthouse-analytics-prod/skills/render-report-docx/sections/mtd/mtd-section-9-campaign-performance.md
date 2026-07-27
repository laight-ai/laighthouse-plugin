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

## DOCX 섹션

```json
{
  "type": "table",
  "heading": "캠페인별 성과",
  "headers": ["캠페인", "네이버 광고 채널명", "매출", "광고비", "ROAS", "노출", "클릭", "CTR", "CPC", "구매", "평균단가"],
  "rows": [
    ["{campaign}", "{channel}", "{revenue_fmt}", "{ad_cost_fmt}", "{roas}%", "{impressions_fmt}", "{clicks_fmt}", "{ctr}%", "{cpc_fmt}", "{purchases}", "{avg_price_fmt}"]
  ]
}
```

`rows`에는 `campaign_performance` 배열의 모든 항목을 위 필드 매핑대로 한 행씩 그대로 넣는다
(검색창/페이지네이션은 정적 문서에 의미가 없으므로 제거 — 전체 행을 한 표에 다 낸다).

### 렌더링 규칙
- 금액/노출/클릭 필드는 `toLocaleString()` 스타일 천 단위 콤마 포맷 문자열로 만들어 넣는다.
> ⚡ **상위 15행 저장 규칙**: 이 섹션의 MCP 응답 `items`는 임시 JSON에 **응답 순서 그대로 앞
> 15개만** 저장하고 최상위에 `"items_total": <원본 items 길이>`를 기록한다 (SKILL.md `mtd 전용:
> 병렬 서브에이전트 실행 방식` 2번 참고). PPT 표는 상위 12행만 그리며, `map_section.py`가
> `items_total`을 `rows_total`로 전달해 "외 n행 생략" 캡션이 전체 데이터 기준으로 표시된다.
