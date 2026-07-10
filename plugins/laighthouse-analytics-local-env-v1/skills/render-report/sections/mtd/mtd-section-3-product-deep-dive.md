# MTD Section 3: 제품 판매 성과의 심층 분석

**report_type:** `mtd` (항상 포함)

---

## MCP 도구 호출: `df_dify` 서버의 분석 tool (텍스트만; 수치 소스는 section-5/6 — `get_naver_item_sales_daily`)

`mcp__df_dify__<workflow-tool-name>`으로 분석 텍스트를 가져온다. 응답에서 `analysis_of_ad_performance` key의 값을 사용한다.

```
호출 순서:
1. section-5(카테고리별 매출액)/section-6(일일 카테고리별 매출)이 이미 호출한
   get_naver_item_sales_daily(group_by="category_3rd") 결과 재사용
2. mcp__df_dify__<workflow-tool-name> 으로 분석 요청 (1의 수치 데이터 전달)
3. 응답의 analysis_of_ad_performance 값을 렌더링
```

dify 응답 실패 시 section-5/6 수치 기반으로 AI가 직접 생성한다.

---

## 응답 데이터 구조

```json
{
  "analysis_of_ad_performance": "Overview\n매출이 가장 많이 발생하는 5개 카테고리(국내분유, 커피, 단백질보충제, 우유/요거트, 두유)를 분석 대상으로 선정하였습니다.\n\n국내분유\n프로모션 기간 광고 효율에서 CTR과의 관계가...\n\n커피\n커피 카테고리는 매출 대비 광고비 비중이..."
}
```

- `analysis_of_ad_performance`는 `\n\n`으로 구분된 블록으로 구성
- 각 블록의 첫 줄이 `Overview` 또는 카테고리명(예: `국내분유`, `커피`)이면 `<h4>` 소제목으로 렌더링
- 나머지 문장은 `<p>`로 렌더링 (section-7 트렌드 분석보다 더 긴 서술형)

---

## HTML

```html
<!-- MTD SECTION 3: 제품 판매 성과의 심층 분석 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">제품 판매 성과의 심층 분석</div>
  <div style="font-size:13px; color:#374151; line-height:1.8;">
    <!-- analysis_of_ad_performance를 \n\n 기준으로 분리, 각 블록의 첫 줄은 <h4> 소제목 -->
    {PRODUCT_ANALYSIS_BLOCKS}
  </div>
</div>
```

블록 렌더링 예시:

```html
<h4 style="font-size:14px; font-weight:700; margin:16px 0 6px;">국내분유</h4>
<p>프로모션 기간 광고 효율에서 CTR과의 관계가 뚜렷이 드러났습니다...</p>
```

## Script
없음 (정적 텍스트)

## 렌더링 규칙
- 첫 블록(`Overview`)은 `margin-top:0`
- 강조 수치는 `<strong>` 태그 사용
- section-7(제품 판매 트렌드 분석)과 동시에 포함 섹션 키워드를 지정하지 않는 것을 권장
  (mtd-section-3이 더 상세한 대체 콘텐츠이므로 중복 방지)
