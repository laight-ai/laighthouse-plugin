# Executive-MTD Section 3: Executive Summary — DOCX 출력 스펙

> 데이터 스펙: 스킬 폴더 기준 `../../shared/sections/executive-mtd/executive-mtd-section-3-executive-summary.md` 를 **먼저** 읽고, 이 파일의 출력 스펙을 적용한다.

## DOCX 섹션

```json
{
  "type": "text",
  "heading": "Executive Summary",
  "body": "{executive_summary}"
}
```

- `executive_summary` 문자열을 그대로 `body`에 넣는다 — 줄바꿈(`\n`)으로 구분된 각 불릿 문장이
  하나의 문단(줄)로 렌더링되며, 별도의 리스트/색깔 점(●) 마크업으로 쪼개지 않는다(정적 문서에서는
  단락 텍스트로 충분하다) — 색깔 점(`DOT_COLOR`)에 의한 성장/하락/중립 구분은 정적 문서에서는
  표현하지 않는다.
- 강조하고 싶은 수치가 있으면 문장 자체에 자연스럽게 녹여 쓴다(굵게 표시할 별도 마크업은 없음).
- 문장 수는 3~5개로 제한하는 원문 작성 규칙은 그대로 유지한다(위 "텍스트 생성" 절 참고) — 이미
  그 단계에서 걸러진 문자열을 그대로 전달한다.
