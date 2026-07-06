# laighthouse-analytics

라이트하우스 MCP 연동 데이터를 표, 차트, 주간 성과 보고서로 렌더링하는 Cowork 플러그인입니다.

## 컴포넌트

| 유형 | 이름 | 설명 |
|------|------|------|
| MCP | laighthouse | `https://alien-watching-jane-nextel.trycloudflare.com/api/mcp` 연동 |
| 스킬 | render-table | MCP 결과를 HTML 테이블로 렌더링 |
| 스킬 | render-chart | MCP 결과를 Chart.js 차트로 시각화 |
| 스킬 | render-report | MCP 결과를 라이트하우스 주간 성과 보고서 형식으로 렌더링 |

## 사용법

### 표 렌더링
> "{MCP 도구 이름} 결과를 표로 보여줘"

### 차트 렌더링
> "{MCP 도구 이름} 결과를 차트로 그려줘"

### 보고서 렌더링
> "{MCP 도구 이름} 결과를 보고서로 만들어줘"
> "주간 성과 보고서로 보여줘"

## MCP 서버

- **이름**: laighthouse
- **타입**: HTTP (Streamable HTTP transport)
- **URL**: `https://alien-watching-jane-nextel.trycloudflare.com/api/mcp`
- **인증**: 없음 (공개 엔드포인트)

## 설정

별도의 환경 변수 설정이 필요 없습니다.
MCP 서버가 인증을 요구하는 경우 `.mcp.json`의 `headers`에 토큰을 추가하세요:

```json
{
  "mcpServers": {
    "laighthouse": {
      "type": "http",
      "url": "https://alien-watching-jane-nextel.trycloudflare.com/api/mcp",
      "headers": {
        "Authorization": "Bearer ${LIGHTHOUSE_API_TOKEN}"
      }
    }
  }
}
```
