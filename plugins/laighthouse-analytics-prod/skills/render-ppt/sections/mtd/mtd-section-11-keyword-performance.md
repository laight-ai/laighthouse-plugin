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

## PPT 섹션

```json
{
  "type": "table",
  "heading": "키워드별 성과",
  "headers": ["키워드", "노출", "클릭", "광고비", "CPC", "클릭율", "CPM", "구매건수", "매출", "ROAS"],
  "rows": [
    ["{keyword}", "{impressions_fmt}", "{clicks_fmt}", "{ad_cost_fmt}", "{cpc_fmt}", "{ctr}%", "{cpm_fmt}", "{purchases}", "{revenue_fmt}", "{roas}%"]
  ]
}
```

`rows`에는 `keyword_performance` 배열의 모든 항목을 위 필드 매핑대로 한 행씩 그대로 넣는다
(검색창/페이지네이션은 정적 문서에 의미가 없으므로 제거 — 전체 행을 한 표에 다 낸다).

### 렌더링 규칙
- 금액/노출/클릭 필드는 `toLocaleString()` 스타일 천 단위 콤마 포맷 문자열로 만들어 넣는다.
- 반환 키워드 수가 매우 많을 수 있음(PDF 기준 130페이지 규모) — `get_naver_keyword_performance`는
  절단 파라미터가 없고 합산·정렬된 전체 키워드를 반환하므로, 전부 받아 한 표에 전체 행으로 낸다
  (report-backend `build_keywords_table`도 상위 N 컷 없이 전체를 낸다).
- 노출/클릭/구매가 모두 0인 키워드도 그대로 표시 (성과 없음 상태 확인 목적)
> ⚡ **상위 15행 저장 규칙**: 이 섹션의 MCP 응답 `items`는 임시 JSON에 **응답 순서 그대로 앞
> 15개만** 저장하고 최상위에 `"items_total": <원본 items 길이>`를 기록한다 (SKILL.md `mtd 전용:
> 병렬 서브에이전트 실행 방식` 2번 참고). PPT 표는 상위 12행만 그리며, `map_section.py`가
> `items_total`을 `rows_total`로 전달해 "외 n행 생략" 캡션이 전체 데이터 기준으로 표시된다.
