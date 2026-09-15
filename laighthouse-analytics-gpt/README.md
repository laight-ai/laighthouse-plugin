# laighthouse-analytics-gpt

`laighthouse-plugin` 레포의 Claude Code 플러그인(`plugins/laighthouse-analytics-prod/`)을
**ChatGPT / Codex 플러그인**으로 이식한 것입니다. 라이트하우스 MCP 연동 데이터를 브리즘
(airbridge 기반) 성과 보고서(HTML)로 렌더링합니다.

두 가지 배포 형태를 한 폴더에서 지원합니다:

| 배포 형태 | 대상 | 스킬 | MCP | 훅 |
|---|---|---|---|---|
| **플러그인** (`.codex-plugin/plugin.json` + `.mcp.json` + `hooks/` + `skills/`) | ChatGPT 데스크톱 Work 모드, Codex CLI, ChatGPT 안의 Codex — 로컬 마켓플레이스로 설치 | 8개 일괄 | 플러그인에 포함 | PostToolUse 캡처 훅 동작 |
| **스킬 zip** (`build_skill_zips.ps1` 산출물) | chatgpt.com 웹 일반 Chat — 개인/워크스페이스 스킬로 업로드 | 하나씩 업로드 | ChatGPT 설정에서 커넥터로 별도 연결 | 없음 (사전 예방 규칙으로 대체) |

스킬 본문은 두 형태에서 **같은 파일**을 쓰며, 대용량 응답 처리만 실행 시점에 "훅 스텁이 왔는지"로
분기합니다(`shared/references/gpt-large-response-guardrail.md`).

> 이 폴더는 향후 별도 저장소로 분리될 예정입니다 — 지금은 원본(Claude Code판)과의 편집
> 이력을 나란히 비교하기 쉽도록 같은 레포 안에 두었습니다.

## Claude Code판과의 차이

| | Claude Code (`plugins/laighthouse-analytics-prod/`) | ChatGPT / Codex (이 폴더) |
|---|---|---|
| 플러그인 매니페스트 | `.claude-plugin/plugin.json` + 레포 루트 `.claude-plugin/marketplace.json` | `.codex-plugin/plugin.json` + 레포 루트 `.agents/plugins/marketplace.json` (로컬 마켓플레이스) |
| 스킬 메타데이터 | SKILL.md frontmatter만 | 추가로 스킬별 `agents/openai.yaml` (표시 이름·색, `dependencies.tools`에 MCP **서버** 단위 의존성 — `value`는 서버 이름 `laighthouse`, 사용 도구 목록은 description에 기재) |
| MCP 연동 | `.mcp.json` (`"type": "http"`) | `.mcp.json` (`"type": "streamable-http"`, Agent Plugins 스키마). 웹 스킬 zip 경로에서는 ChatGPT 설정에서 커넥터로 별도 연결 |
| 대용량 응답 처리 | PostToolUse 훅(`hooks/capture_ad_performance.py`) | **같은 훅 스크립트**를 `hooks/`에 포함 (`${PLUGIN_ROOT}` 기준). Codex 런타임(Work 모드·Codex)에서만 실행되며 웹 Chat에서는 사전 예방 규칙으로 대체 — [`shared/references/gpt-large-response-guardrail.md`](shared/references/gpt-large-response-guardrail.md) |
| 스킬 본문(SKILL.md)·섹션 파일·asset 스크립트 | 원본 | Claude 고유 표현·훅 분기 서술만 수정, 나머지 보고서 로직(계산·렌더링 규칙)은 **동일** |

MCP 서버(`laighthouse`) 자체는 수정하지 않았습니다 — 이 레포는 클라이언트(스킬) 측 지침만
플랫폼에 맞게 바꿉니다.

## 구조

```
laighthouse-plugin/
├── .agents/plugins/marketplace.json   # 로컬 마켓플레이스 (ChatGPT 데스크톱/Codex가 읽는 위치)
└── laighthouse-analytics-gpt/
    ├── .codex-plugin/plugin.json      # 플러그인 매니페스트 (skills/·hooks/ 경로 선언)
    ├── .mcp.json                      # laighthouse MCP 서버 (streamable-http)
    ├── hooks/
    │   ├── hooks.json                 # PostToolUse: get_ad_performance 대용량 응답 캡처
    │   └── capture_ad_performance.py  # Claude Code판과 동일한 스크립트
    ├── build_skill_zips.ps1           # 웹 업로드용 스킬별 zip 생성 + 규격 검증
    ├── shared/
    │   └── references/                # 스킬 간 공유 데이터 스펙 (스킬 루트 기준 경로로 참조됨)
    │       ├── mcp-tools.md
    │       ├── generic-report-pattern.md
    │       ├── report-types.md
    │       └── gpt-large-response-guardrail.md   # 훅 스텁 / 원본 분기 규칙
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

## 설치 A — 플러그인 (ChatGPT 데스크톱 Work 모드 / Codex)

스킬 8개 + MCP 서버 + 캡처 훅이 한 번에 설치됩니다. OpenAI 심사 없이 로컬 마켓플레이스로 배포하는
경로이며, **ChatGPT 데스크톱 앱 또는 Codex에서만** 됩니다(웹 chatgpt.com은 설치 B 참고).

1. 이 레포를 클론합니다. 레포 루트의 `.agents/plugins/marketplace.json`이 이 폴더를 플러그인으로
   가리키고 있어, 레포를 열면 ChatGPT 데스크톱/Codex가 마켓플레이스로 인식합니다. 레포 밖에서
   쓰려면 CLI로 등록합니다:
   ```bash
   codex plugin marketplace add <레포 루트 경로>
   ```
   개인 범위로 두려면 `~/.agents/plugins/marketplace.json`에 같은 항목을 넣고 `source.path`를
   플러그인 폴더의 경로로 바꿉니다.
2. ChatGPT 데스크톱 앱 → Work 탭(또는 Codex) → Plugins Directory에서 소스 "Laighthouse (local)"을
   선택해 **Laighthouse Analytics**를 설치합니다. MCP 서버 인증은 설치 시점에 요청됩니다
   (`policy.authentication: ON_INSTALL`).
3. **훅 신뢰 승인**: 플러그인 훅은 설치만으로 실행되지 않습니다. 대화에서 `/hooks`를 열어
   `capture_ad_performance.py` 정의를 검토·신뢰해야 PostToolUse 캡처가 동작합니다. 실행 환경에
   `python3`가 있어야 합니다. 승인하지 않아도 스킬은 동작하며(원본이 그대로 전달됨), 대용량 응답은
   웹과 같은 사전 예방 규칙으로 처리됩니다.
4. 새 대화에서 `@`를 입력해 플러그인을 호출합니다.

플러그인 파일을 수정한 뒤에는 ChatGPT 데스크톱 앱을 재시작해야 반영됩니다.

> 검증 포인트: 훅이 실제로 응답을 교체했는지는 `<임시 디렉터리>/laighthouse_mcp_capture/hook.log`
> (`ran:`/`skip:`/`captured:`)로 확인합니다. Codex PostToolUse가 `updatedToolOutput`으로 도구 응답을
> 교체하는 동작과 MCP 도구 matcher 이름 형식은 공식 문서에 명시가 없어, 첫 설치 때 이 로그로
> 확인해야 합니다. matcher는 접미 매칭(`.*get_ad_performance$`)이라 도구 이름 접두어 형식이 달라도
> 걸립니다.

## 설치 B — 스킬 zip (chatgpt.com 웹 일반 Chat)

웹에서는 플러그인 로컬 설치가 안 되므로 스킬을 하나씩 업로드하고 MCP는 커넥터로 따로 연결합니다.
ChatGPT Skills는 Business/Enterprise/Healthcare/Edu 요금제에서(워크스페이스 관리자가 켠
경우) 사용할 수 있습니다. 훅은 동작하지 않습니다.

### 1. 업로드용 zip 생성

`skills/` 아래 폴더를 그대로 올리면 **`shared/`가 zip 밖이라 빠집니다** — 스킬 본문이
참조하는 `shared/references/...`가 전부 깨집니다. 반드시 빌드 스크립트를 거치세요.

```powershell
.\build_skill_zips.ps1                      # 8개 전부
.\build_skill_zips.ps1 -Skill daily-detailed # 하나만
```

`~/Downloads/laighthouse-gpt-skills/<skill-name>.zip` 8개가 생성됩니다. 스크립트는 스킬
폴더에 `shared/references/*`를 **같은 경로 그대로** 주입한 뒤, 만들어진 zip을 다시 열어
OpenAI Skills 규격(단일 최상위 폴더 / `SKILL.md` 1개 / 50MB·500파일·단일 25MB 한도)과
본문의 `shared/references` 참조가 번들 안에서 실제로 해석되는지까지 검증합니다.

> `Compress-Archive`는 엔트리 경로에 백슬래시를 넣어 업로드 시 폴더 구조가 깨지므로
> 쓰지 않습니다. 스크립트는 .NET `ZipArchive`로 슬래시 경로를 직접 기록합니다.

### 2. 업로드

Sidebar → Plugins → Skills → Create → Upload from your computer에서 zip을 **하나씩**
올립니다. zip 하나에 `SKILL.md`가 정확히 하나여야 해서 8개를 한 번에 묶을 수 없습니다.

MCP 도구(`get_ad_performance` 등)는 ChatGPT 설정에서 `laighthouse` MCP 서버를 커넥터로
먼저 연결해야 스킬이 호출할 수 있습니다.

## 유지보수 원칙

이 폴더의 스킬 로직(보고서 계산·렌더링 규칙)은 원본 Claude Code 플러그인과 **같은 소스에서
파생**됩니다. 원본 쪽에서 보고서 로직이 바뀌면(섹션 계산 규칙, MCP 호출 명세 등) 이쪽에도
반영해야 합니다 — 다만 아래는 이 폴더에서만 다르게 유지합니다:
1. 대용량 응답 처리: 훅 스텁이 오면 `json_files`, 원본이 오면 `json` — 두 경로를 모두 서술하고
   판별 규칙은 `gpt-large-response-guardrail.md`에 둡니다. "이 환경에는 훅이 없다"고 단정하는
   문구를 쓰지 않습니다(Work 모드/Codex에서는 훅이 돕니다).
2. 훅 스크립트: `hooks/capture_ad_performance.py`는 Claude Code판과 동일 파일을 복사한 것입니다.
   원본이 바뀌면 그대로 다시 복사합니다. `hooks.json`만 `${PLUGIN_ROOT}` 기준으로 다릅니다.
3. 매니페스트: `.codex-plugin/plugin.json`(플러그인)과 스킬별 `agents/openai.yaml`(스킬 메타)을
   함께 유지합니다. 버전은 Claude Code판 `plugin.json`과 맞춥니다.
4. 공유 참조 배포: 레포에서는 `shared/references/`가 단일 소스지만, 웹 업로드 단위가 스킬
   폴더 하나라서 `build_skill_zips.ps1`이 빌드 시점에 각 zip 안으로 복사합니다. 플러그인 설치
   경로에서는 복사 없이 그대로 참조됩니다.

`shared/references/`에 파일을 추가할 때는 경로를 `shared/references/<name>.md`로 참조하면
됩니다 — 스크립트가 폴더 전체를 통째로 넣으므로 스크립트 수정은 필요 없습니다. 반대로
스킬 본문에서 참조 경로를 다른 형태로 바꾸면 빌드 검증이 실패합니다.

> 웹(chatgpt.com)에서도 스킬+MCP+훅을 한 번에 설치하려면 플러그인 포털에 Skills-plus-MCP로
> 제출해 OpenAI 심사를 받아야 합니다. 스킬 본문·도구 스키마가 바뀔 때마다 재심사가 필요하므로,
> 개발 단계에서는 설치 A(로컬 마켓플레이스)와 설치 B(스킬 zip)를 쓰고 안정화 후 제출합니다.
> 제출 시 `.codex-plugin/plugin.json`은 그대로 쓰이고 `.mcp.json` 대신 포털에 HTTPS 엔드포인트를
> 입력합니다.
