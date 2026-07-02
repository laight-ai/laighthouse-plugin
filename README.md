# laighthouse-plugin

Laighthouse Analytics 플러그인을 위한 Claude Code 플러그인 마켓플레이스 저장소입니다. MCP로 연동된 라이트하우스 데이터를 표, 차트, 성과 보고서 형태로 렌더링하는 스킬들을 제공합니다.

## 구조

```
laighthouse-plugin/
├── .claude-plugin/
│   └── marketplace.json          # 마켓플레이스 정의 (플러그인 목록/메타데이터)
└── plugins/
    └── laighthouse-analytics-local-env-v1/
        ├── .claude-plugin/plugin.json
        ├── .mcp.json              # laighthouse MCP 서버 연동 설정
        ├── README.md
        └── skills/
            ├── render-table/      # MCP 결과를 HTML 테이블로 렌더링
            ├── render-chart/      # MCP 결과를 Chart.js 차트로 렌더링
            └── render-report/     # MCP 결과를 일간/주간/월간 성과 보고서로 렌더링
                └── sections/      # 보고서 섹션별 스킬 (daily / weekly·mtd·monthly)
```

## 포함된 플러그인

### laighthouse-analytics-local-env-v1

라이트하우스 MCP 연동 데이터를 표, 차트, 성과 보고서로 렌더링하는 플러그인입니다.

| 스킬 | 설명 |
|------|------|
| `render-table` | MCP 결과를 HTML 표로 렌더링 |
| `render-chart` | MCP 결과를 Chart.js 기반 차트(막대/선/도넛/레이더)로 렌더링 |
| `render-report` | MCP 결과를 라이트하우스 스타일 일간/주간/MTD/월간 성과 보고서로 렌더링 |


자세한 사용법은 [플러그인 README](plugins/laighthouse-analytics-local-env-v1/README.md)를 참고하세요.

## 사용법 예시

- "target-progress 결과를 표로 보여줘"
- "이번 주 매출을 차트로 그려줘"
- "주간 성과 보고서로 보여줘"

## 마켓플레이스 등록

Claude Code에서 이 저장소를 마켓플레이스로 추가하면 `laighthouse-analytics-local-env-v1` 플러그인을 설치할 수 있습니다.
