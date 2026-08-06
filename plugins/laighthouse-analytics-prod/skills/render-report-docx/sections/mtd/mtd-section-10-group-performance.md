# MTD Section 10: 광고 그룹별 성과 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/mtd/mtd-section-10-group-performance.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "table",
  "heading": "광고 그룹별 성과",
  "headers": ["광고그룹", "노출", "클릭", "CPC", "광고비", "매출"],
  "rows": [
    ["{group}", "{impressions_fmt}", "{clicks_fmt}", "{cpc_fmt}", "{ad_cost_fmt}", "{revenue_fmt}"]
  ]
}
```

`rows`에는 `group_performance` 배열의 모든 항목을 위 필드 매핑대로 한 행씩 그대로 넣는다
(검색창/페이지네이션은 정적 문서에 의미가 없으므로 제거 — 전체 행을 한 표에 다 낸다).

### 렌더링 규칙
- 금액/노출/클릭 필드는 `toLocaleString()` 스타일 천 단위 콤마 포맷 문자열로 만들어 넣는다.
> ⚡ **상위 15행 저장 규칙**: 이 섹션의 MCP 응답 `items`는 임시 JSON에 **응답 순서 그대로 앞
> 15개만** 저장하고 최상위에 `"items_total": <원본 items 길이>`를 기록한다 (SKILL.md `mtd 전용:
> 병렬 서브에이전트 실행 방식` 2번 참고). PPT 표는 상위 12행만 그리며, `map_section.py`가
> `items_total`을 `rows_total`로 전달해 "외 n행 생략" 캡션이 전체 데이터 기준으로 표시된다.
