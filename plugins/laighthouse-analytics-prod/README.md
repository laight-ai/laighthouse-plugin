# laighthouse-analytics

라이트하우스 MCP 연동 데이터를 브리즘(airbridge 기반) 성과 보고서(HTML)와 Word(.docx) 보고서로
렌더링하는 Cowork 플러그인입니다.

## 컴포넌트

| 유형 | 이름 | 설명 |
|------|------|------|
| MCP | laighthouse | `https://app.laight.ai/data/mcp` 연동 |
| 스킬 | mtd-detailed | 브리즘 MTD 보고서(HTML, 7개 섹션, 실무 상세) 렌더링 |
| 스킬 | mtd-summary | 브리즘 Executive MTD 보고서(HTML, 5개 섹션, 임원용 핵심 요약) 렌더링 |
| 스킬 | daily-detailed | 브리즘 데일리 보고서(HTML, 5개 섹션, 실무 상세) 렌더링 |
| 스킬 | daily-summary | 브리즘 Executive 데일리 보고서(HTML, 5개 섹션, 임원용 핵심 요약) 렌더링 |
| 스킬 | monthly-detailed | 브리즘 월간 보고서(HTML, 5개 섹션, 실무 상세) 렌더링 |
| 스킬 | monthly-summary | 브리즘 Executive 월간 보고서(HTML, 5개 섹션, 임원용 핵심 요약) 렌더링 |
| 스킬 | creative-detailed | 브리즘 소재 보고서(HTML, 5개 섹션, 실무 상세) 렌더링 |
| 스킬 | creative-summary | 브리즘 Executive 소재 보고서(HTML, 5개 섹션, 임원용 핵심 요약) 렌더링 |
| 스킬 | render-report-docx | MCP 결과를 편집 가능한 Word(.docx) 보고서로 렌더링 |

## 사용법

### 보고서 렌더링 (HTML)
> "MTD 보고서로 보여줘" → `mtd-detailed`
> "임원용 MTD 보고서로 보여줘" → `mtd-summary`
> "데일리 보고서 만들어줘" → `daily-detailed`
> "임원용 데일리 보고서 만들어줘" → `daily-summary`
> "월간 보고서로 보여줘" → `monthly-detailed`
> "임원용 월간 보고서로 보여줘" → `monthly-summary`
> "소재 보고서 만들어줘" → `creative-detailed`
> "임원용 소재 보고서 만들어줘" → `creative-summary`

각 보고서 종류는 별도 스킬로 나뉘어 있으며, report_type을 별도로 지정할 필요 없이 스킬 자체가
보고서 종류를 고정한다.

### Word 문서 렌더링 (.docx)
> "브리즘 MTD 보고서를 워드로 만들어줘"
> "Monthly 보고서 docx로 저장해줘"

대용량 표(키워드/캠페인 등)는 docx에서 매출 0원 행을 자동 제외하고 상위 50행까지 싣습니다.

`render-report-docx`는 `python-docx`가 필요합니다 (`assets/docx_report/requirements.txt` 참고).

## MCP 서버

- **이름**: laighthouse
- **타입**: HTTP (Streamable HTTP transport)
- **URL**: `https://app.laight.ai/data/mcp`
- **인증**: 없음 (공개 엔드포인트)

## 설정

별도의 환경 변수 설정이 필요 없습니다.
MCP 서버가 인증을 요구하는 경우 `.mcp.json`의 `headers`에 토큰을 추가하세요:

```json
{
  "mcpServers": {
    "laighthouse": {
      "type": "http",
      "url": "https://app.laight.ai/data/mcp",
      "headers": {
        "Authorization": "Bearer ${LAIGHTHOUSE_API_TOKEN}"
      }
    }
  }
}
```
