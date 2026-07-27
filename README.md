# laighthouse-plugin

Laighthouse Analytics 플러그인을 위한 Claude Code 플러그인 마켓플레이스 저장소입니다. MCP로 연동된 라이트하우스 데이터를 표, 차트, 성과 보고서 형태로 렌더링하는 스킬들을 제공합니다.

## 구조

```
laighthouse-plugin/
├── .claude-plugin/
│   └── marketplace.json          # 마켓플레이스 정의 (플러그인 목록/메타데이터)
└── plugins/
    └── laighthouse-analytics-prod/
        ├── .claude-plugin/plugin.json
        ├── .mcp.json              # laighthouse MCP 서버 연동 설정
        ├── README.md
        └── skills/
            ├── render-table/      # MCP 결과를 HTML 테이블로 렌더링
            ├── render-chart/      # MCP 결과를 Chart.js 차트로 렌더링
            ├── render-report/     # MCP 결과를 일간/MTD/월간 성과 보고서(HTML)로 렌더링
            │   └── sections/      # 보고서 섹션 정의 (daily / mtd / Monthly / executive-mtd)
            ├── render-ppt/        # MCP 결과를 16:9 발표용 PPT(.pptx)로 렌더링
            │   ├── sections/      # PPT 섹션 정의 (daily / mtd / Monthly / executive-mtd)
            │   └── assets/pptx_report/   # python-pptx 렌더러 + 매핑 스크립트
            └── render-report-docx/       # MCP 결과를 편집 가능한 Word(.docx) 보고서로 렌더링
                ├── sections/      # DOCX 섹션 정의 (daily / mtd / Monthly / executive-mtd)
                └── assets/docx_report/   # python-docx 렌더러 + 매핑 스크립트
```

## 포함된 플러그인

### laighthouse-analytics-prod

라이트하우스 MCP 연동 데이터를 표, 차트, 성과 보고서로 렌더링하는 플러그인입니다.

| 스킬 | 설명 |
|------|------|
| `render-table` | MCP 결과를 HTML 표로 렌더링 |
| `render-chart` | MCP 결과를 Chart.js 기반 차트(막대/선/도넛/레이더)로 렌더링 |
| `render-report` | MCP 결과를 라이트하우스 스타일 Daily/MTD/Monthly/Executive-MTD 성과 보고서(HTML)로 렌더링 |
| `render-ppt` | MCP 결과를 라이트하우스 스타일 16:9 발표용 PPT(.pptx)로 렌더링 — 네이티브 카드/표/차트, 긴 표는 상위 12행 요약 |
| `render-report-docx` | MCP 결과를 편집 가능한 Word(.docx) 보고서로 렌더링 — 배너 섹션 헤더/카드/네이티브 차트, 대용량 표는 매출 0원 행 제외 + 상위 50행 |


자세한 사용법은 [플러그인 README](plugins/laighthouse-analytics-prod/README.md)를 참고하세요.

## 사용법 예시

- "target-progress 결과를 표로 보여줘"
- "이번 주 매출을 차트로 그려줘"
- "다형식품 MTD 보고서로 보여줘"
- "다형식품 MTD 성과를 PPT로 만들어줘"

## 마켓플레이스 등록

Claude Code에서 이 저장소를 마켓플레이스로 추가하면 `laighthouse-analytics-prod` 플러그인을 설치할 수 있습니다.
