# Monthly Section 6: 카테고리별 월간 매출액 비교 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/monthly/monthly-section-6-category-monthly-comparison.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "chart",
  "heading": "카테고리별 월간 매출액 비교",
  "categories": "{category_monthly_comparison.labels}",
  "bar_series": [
    { "name": "{category_monthly_comparison.prev_month_label}", "values": "{category_monthly_comparison.prev}" },
    { "name": "{category_monthly_comparison.curr_month_label}", "values": "{category_monthly_comparison.curr}" }
  ],
  "line_series": { "name": "전월 대비 증감률(%)", "values": "{category_monthly_comparison.change_pct}" }
}
```

- `categories`는 상위 5개 카테고리명 + "기타"(카테고리 개수가 5개 미만인 브랜드는 있는 만큼만)
  배열을 그대로 넣는다.
- `bar_series`는 전월/이번달 매출 두 그룹 막대다 — 원본 Chart.js 그룹 바 차트(전월/이번달)와
  동일 구성.
- 원본 HTML은 막대 위 % 변화 배지를 캔버스에 직접 그리는 인라인 플러그인을 썼지만, 정적 문서
  차트에는 막대 위 배지를 얹을 수단이 없으므로 이를 `line_series`(전월 대비 증감률 %) 한 줄로
  대체해 같은 정보를 보존한다 — `change_pct`가 `null`(전월 매출 0)인 항목은 `0`으로 넣고, 해당
  카테고리가 신규임을 위 텍스트 섹션(monthly-section-5) 등 서술에서 별도로 언급한다.
- 위 JSON의 문자열 자리(`"{category_monthly_comparison.labels}"` 등)는 실제 렌더링 시 그
  배열/리스트 값으로 그대로 치환한다(문자열이 아니라 JSON 배열이 들어간다).
- 데이터가 비어있으면 이 섹션 자체를 생략한다(임의로 채우지 않는다).
