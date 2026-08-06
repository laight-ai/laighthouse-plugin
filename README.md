# laighthouse-plugin

Laighthouse Analytics 플러그인을 위한 Claude Code 플러그인 마켓플레이스 저장소입니다. MCP로 연동된 라이트하우스(브리즘, airbridge 기반) 데이터를 성과 보고서 형태로 렌더링하는 스킬들을 제공합니다.

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
        ├── shared/                # 스킬 간 공유 데이터 스펙 (플러그인 루트 기준 경로로 참조됨)
        │   ├── references/
        │   └── sections/          # daily / mtd / monthly / executive-mtd 섹션 데이터 스펙
        └── skills/
            ├── daily-detailed/    # 브리즘 데일리 보고서(HTML, 실무 상세)
            ├── daily-summary/     # 브리즘 Executive 데일리 보고서(HTML, 임원용 요약)
            ├── mtd-detailed/      # 브리즘 MTD 보고서(HTML, 실무 상세)
            ├── mtd-summary/       # 브리즘 Executive MTD 보고서(HTML, 임원용 요약)
            ├── monthly-detailed/  # 브리즘 월간 보고서(HTML, 실무 상세)
            ├── monthly-summary/   # 브리즘 Executive 월간 보고서(HTML, 임원용 요약)
            ├── creative-detailed/ # 브리즘 소재 보고서(HTML, 실무 상세)
            ├── creative-summary/  # 브리즘 Executive 소재 보고서(HTML, 임원용 요약)
            └── render-report-docx/       # MCP 결과를 편집 가능한 Word(.docx) 보고서로 렌더링
                ├── sections/      # DOCX 섹션 정의 (daily / mtd / monthly / executive-mtd / creative)
                └── assets/docx_report/   # python-docx 렌더러 + 매핑 스크립트
```

## 포함된 플러그인

### laighthouse-analytics-prod

라이트하우스 MCP 연동 데이터를 브리즘(airbridge 기반) 성과 보고서로 렌더링하는 플러그인입니다.

| 스킬 | 설명 |
|------|------|
| `daily-detailed` | 브리즘 데일리 보고서(HTML, 실무 상세) 렌더링 |
| `daily-summary` | 브리즘 Executive 데일리 보고서(HTML, 임원용 핵심 요약) 렌더링 |
| `mtd-detailed` | 브리즘 MTD 보고서(HTML, 실무 상세) 렌더링 |
| `mtd-summary` | 브리즘 Executive MTD 보고서(HTML, 임원용 핵심 요약) 렌더링 |
| `monthly-detailed` | 브리즘 월간 보고서(HTML, 실무 상세) 렌더링 |
| `monthly-summary` | 브리즘 Executive 월간 보고서(HTML, 임원용 핵심 요약) 렌더링 |
| `creative-detailed` | 브리즘 소재 보고서(HTML, 실무 상세) 렌더링 |
| `creative-summary` | 브리즘 Executive 소재 보고서(HTML, 임원용 핵심 요약) 렌더링 |
| `render-report-docx` | MCP 결과를 편집 가능한 Word(.docx) 보고서로 렌더링 — 배너 섹션 헤더/카드/네이티브 차트, 대용량 표는 매출 0원 행 제외 + 상위 50행 |

자세한 사용법은 [플러그인 README](plugins/laighthouse-analytics-prod/README.md)를 참고하세요.

## 사용법 예시

- "브리즘 MTD 보고서로 보여줘"
- "임원용 데일리 보고서 만들어줘"
- "브리즘 MTD 보고서를 워드로 만들어줘"

## 마켓플레이스 등록

Claude Code에서 이 저장소를 마켓플레이스로 추가하면 `laighthouse-analytics-prod` 플러그인을 설치할 수 있습니다.
