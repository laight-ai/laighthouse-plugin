# laighthouse-analytics

라이트하우스 MCP 연동 데이터를 표, 차트, 성과 보고서(HTML), 발표용 PPT로 렌더링하는 Cowork 플러그인입니다.

## 컴포넌트

| 유형 | 이름 | 설명 |
|------|------|------|
| MCP | laighthouse | `https://app.laight.ai/data/mcp` 연동 |
| 스킬 | render-table | MCP 결과를 HTML 테이블로 렌더링 |
| 스킬 | render-chart | MCP 결과를 Chart.js 차트로 시각화 |
| 스킬 | render-report | MCP 결과를 라이트하우스 Daily/MTD/Monthly/Executive-MTD 성과 보고서(HTML)로 렌더링 |
| 스킬 | render-ppt | MCP 결과를 라이트하우스 스타일 16:9 발표용 PPT(.pptx)로 렌더링 |
| 스킬 | render-report-docx | MCP 결과를 편집 가능한 Word(.docx) 보고서로 렌더링 |
| 스킬 | analysis-creative | Shot-by-Shot 데모 #4~#5 — 성과 하락 진단·소재 원인 분석을 채팅 대화로 재현 (실데이터) |
| 스킬 | create-creative | Shot-by-Shot 데모 #6~#8 — A/B 테스트·신규 시안 생성·스케일업을 채팅 대화로 재현 |

## 사용법

### 표 렌더링
> "{MCP 도구 이름} 결과를 표로 보여줘"

### 차트 렌더링
> "{MCP 도구 이름} 결과를 차트로 그려줘"

### 보고서 렌더링 (HTML)
> "{MCP 도구 이름} 결과를 보고서로 만들어줘"
> "다형식품 MTD 보고서로 보여줘"

### PPT 렌더링 (.pptx)
> "다형식품 MTD 성과를 PPT로 만들어줘"
> "임원용 MTD 발표자료 만들어줘"

### Shot-by-Shot 데모 대화 (채팅 내 재현)
> "{브랜드명}의 Meta 성과가 떨어졌어. 무슨 일이야?" → analysis-creative (#4~#5)
> "빠른 A/B 테스트를 돌려줄 수 있어?" → create-creative (#6~#8)

### Word 문서 렌더링 (.docx)
> "다형식품 MTD 보고서를 워드로 만들어줘"
> "Monthly 보고서 docx로 저장해줘"

대용량 표(키워드/캠페인 등)는 docx에서 매출 0원 행을 자동 제외하고 상위 50행까지 싣습니다.

`render-ppt`는 `python-pptx`, `render-report-docx`는 `python-docx`가 필요합니다
(각 스킬의 `assets/*/requirements.txt` 참고).

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
