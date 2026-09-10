# laighthouse-analytics-gpt

`laighthouse-plugin` 레포의 Claude Code 플러그인(`plugins/laighthouse-analytics-prod/`)을
**ChatGPT Skills**용으로 이식한 스킬 세트입니다. 라이트하우스 MCP 연동 데이터를 브리즘
(airbridge 기반) 성과 보고서(HTML)로 렌더링합니다.

> 이 폴더는 향후 별도 저장소로 분리될 예정입니다 — 지금은 원본(Claude Code판)과의 편집
> 이력을 나란히 비교하기 쉽도록 같은 레포 안에 두었습니다.

## Claude Code판과의 차이

| | Claude Code (`plugins/laighthouse-analytics-prod/`) | ChatGPT Skills (이 폴더) |
|---|---|---|
| 배포 단위 | 마켓플레이스 하나에 여러 스킬+MCP+훅을 묶은 "플러그인" | 스킬 폴더 하나하나를 개별 업로드 (ChatGPT Skills UI, Sidebar > Plugins > Skills) |
| 스킬 매니페스트 | `.claude-plugin/plugin.json` (플러그인 전체) | 스킬별 `agents/openai.yaml` (표시 이름·아이콘·MCP 도구 의존성) |
| MCP 연동 | `.mcp.json`에 서버 등록 | ChatGPT 설정에서 별도로 MCP 커넥터 연결, 스킬은 `agents/openai.yaml`의 `dependencies.tools`로 사용할 도구만 선언 |
| 대용량 응답 처리 | PostToolUse 훅(`hooks/capture_ad_performance.py`)이 고카디널리티 응답을 파일로 우회 | **훅 없음** — 호출 자체를 좁혀(날짜 구간 축소, 매체별 분리) 응답이 애초에 커지지 않게 함. 원칙은 [`shared/references/gpt-large-response-guardrail.md`](shared/references/gpt-large-response-guardrail.md) |
| 스킬 본문(SKILL.md)·섹션 파일·asset 스크립트 | 원본 | 위 두 차이에 해당하는 부분만 수정, 나머지 보고서 로직(계산·렌더링 규칙)은 **동일** |

MCP 서버(`laighthouse`) 자체는 수정하지 않았습니다 — 이 레포는 클라이언트(스킬) 측 지침만
플랫폼에 맞게 바꿉니다.

## 구조

```
laighthouse-analytics-gpt/
├── shared/
│   └── references/           # 스킬 간 공유 데이터 스펙 (스킬 루트 기준 경로로 참조됨)
│       ├── mcp-tools.md
│       ├── generic-report-pattern.md
│       ├── report-types.md
│       └── gpt-large-response-guardrail.md   # 훅 대체 원칙 (신규)
└── skills/
    ├── daily-detailed/        # 데일리 보고서(HTML, 실무 상세)
    │   ├── SKILL.md
    │   ├── agents/openai.yaml
    │   ├── assets/
    │   └── daily-detailed-section-*.md
    ├── daily-summary/         # Executive 데일리 보고서(HTML, 임원용 요약)
    ├── mtd-detailed/          # MTD 보고서(HTML, 실무 상세)
    ├── mtd-summary/           # Executive MTD 보고서(HTML, 임원용 요약)
    ├── monthly-detailed/      # 월간 보고서(HTML, 실무 상세)
    ├── monthly-summary/       # Executive 월간 보고서(HTML, 임원용 요약)
    ├── creative-detailed/     # 소재 보고서(HTML, 실무 상세)
    └── creative-summary/      # Executive 소재 보고서(HTML, 임원용 요약)
```

## 포함된 스킬

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

## 설치 (ChatGPT)

ChatGPT Skills는 Business/Enterprise/Healthcare/Edu 요금제에서(워크스페이스 관리자가 켠
경우) 사용할 수 있습니다. Sidebar → Plugins → Skills → Create → Upload from your computer에서
`skills/` 아래 스킬 폴더를 하나씩 업로드하세요. MCP 도구(`get_ad_performance` 등)는 ChatGPT
설정에서 `laighthouse` MCP 서버를 커넥터로 먼저 연결해야 스킬이 호출할 수 있습니다.

## 유지보수 원칙

이 폴더의 스킬 로직(보고서 계산·렌더링 규칙)은 원본 Claude Code 플러그인과 **같은 소스에서
파생**됩니다. 원본 쪽에서 보고서 로직이 바뀌면(섹션 계산 규칙, MCP 호출 명세 등) 이쪽에도
반영해야 합니다 — 다만 아래 두 가지는 이 폴더에서만 다르게 유지합니다:
1. 대용량 응답 처리: 훅이 아니라 사전 예방 지침(`gpt-large-response-guardrail.md`)
2. 스킬 매니페스트: `plugin.json`/`marketplace.json`이 아니라 스킬별 `agents/openai.yaml`
