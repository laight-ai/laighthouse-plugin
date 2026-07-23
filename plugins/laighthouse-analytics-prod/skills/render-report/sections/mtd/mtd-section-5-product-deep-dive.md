# MTD Section 5: 제품 판매 성과의 심층 분석

**report_type:** `mtd` (항상 포함)

---

## 텍스트 생성: AI가 직접 작성 (`df_dify` MCP 호출 안 함); 수치 소스는 mtd-section-6/7 — `get_naver_item_sales_daily`

⚠️ **`df_dify` MCP 서버는 현재 호출하지 않는다** (연결 불안정으로 타임아웃 시 빈 응답이 돌아옴).

```
작성 순서:
1. mtd-section-6(일일 카테고리별 매출)/mtd-section-6.1(카테고리별 월 누적 매출)이 이미 호출한
   get_naver_item_sales_daily() 결과 재사용 (group_by 파라미터 없음 — 서버가 항상 category_3rd로 반환)
2. dify 호출 없이, 1의 수치 데이터를 근거로 AI가 analysis_of_ad_performance 텍스트를 각 카테고리당 최대 두 문장으로 직접 작성한다. 작성할 때는 아래 내용을 포함한다. (2-1.은 반드시 포함한다.)
2-1. mtd-section-6(일일 카테고리별 매출)의 이번달 일일 매출 현황에서 확인되는 특이사항을 기술한다.
2-2. 월 누적 매출을 포함하여, 함께 확인되는 특이 사항(환불액, 할인율 등)과 연계하여 분석한다.
```

---

## 응답 데이터 구조

```json
{
  "analysis_of_category_performance": "Overview\n매출이 가장 많이 발생하는 5개 카테고리(국내분유, 커피, 단백질보충제, 우유/요거트, 두유)를 분석 대상으로 선정하였습니다.\n\n국내분유\n프로모션 기간 광고 효율에서 CTR과의 관계가...\n\n커피\n커피 카테고리는 매출 대비 광고비 비중이..."
}
```

- `analysis_of_category_performance`는 `\n\n`으로 구분된 블록으로 구성
- 각 블록의 첫 줄이 `Overview` 또는 카테고리명(예: `국내분유`, `커피`)이면 `<h4>` 소제목으로 렌더링
- 나머지 문장은 `<p>`로 렌더링

---

## HTML

```html
<!-- MTD SECTION 8: 카테고리별 성과 분석 -->
<div class="card" style="margin-bottom:16px;">
  <div class="section-title">카테고리별 성과 분석</div>
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