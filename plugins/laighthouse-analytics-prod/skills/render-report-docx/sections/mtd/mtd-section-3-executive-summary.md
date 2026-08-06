# MTD Section 3: Executive Summary — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/mtd/mtd-section-3-executive-summary.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "text",
  "heading": "Executive Summary",
  "body": "{executive_summary}"
}
```

- `executive_summary` 문자열을 그대로 `body`에 넣는다 — 줄바꿈(`\n`)이 있는 하나의 문자열을
  그대로 전달하면 되고, 별도의 리스트/HTML 마크업으로 쪼개지 않는다(정적 문서에서는 단락 텍스트로
  충분하다).
- 빈 줄은 작성 단계에서 이미 걸러서 넣는다.
- 강조하고 싶은 수치가 있으면 문장 자체에 자연스럽게 녹여 쓴다(굵게 표시할 별도 마크업은 없음).
