# MTD Section 8: 캠페인별 성과 심층 분석 — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/mtd/mtd-section-8-campaign-deep-dive.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "text",
  "heading": "캠페인별 성과 심층 분석",
  "body": "{analysis_by_campaign}"
}
```

- `analysis_by_campaign`은 `\n\n`으로 구분된 블록 문자열(첫 블록은 인트로 문단, 이후 블록은
  캠페인명 + 설명)을 그대로 `body`에 넣는다 — 정적 문서에서는 소제목/본문을 별도 마크업으로
  나누지 않고 하나의 텍스트 블록으로 낸다.
- 강조하고 싶은 수치가 있으면 문장 자체에 자연스럽게 녹여 쓴다.
