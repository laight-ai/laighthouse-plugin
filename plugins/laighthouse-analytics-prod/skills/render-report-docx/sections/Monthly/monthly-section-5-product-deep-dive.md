# Monthly Section 5: 제품 판매 성과의 심층 분석 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/monthly/monthly-section-5-product-deep-dive.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "text",
  "heading": "제품 판매 트렌드 분석",
  "body": "{analysis_of_category_performance}"
}
```

- `analysis_of_category_performance`는 `\n\n`으로 구분된 블록 문자열(첫 줄이 `Overview` 또는
  주제 소제목, 나머지가 설명)을 그대로 `body`에 넣는다 — 정적 문서에서는 소제목/본문을 별도
  마크업으로 나누지 않고 하나의 텍스트 블록으로 낸다.
- 강조하고 싶은 수치가 있으면 문장 자체에 자연스럽게 녹여 쓴다.
- 섹션 타이틀은 "제품 판매 트렌드 분석"이다.
