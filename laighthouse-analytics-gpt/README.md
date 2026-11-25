# laighthouse-analytics-gpt

Claude Code판 `plugins/laighthouse-analytics-prod`의 스킬을 ChatGPT(데스크톱 Work 모드)·Codex용 플러그인으로 옮긴 버전입니다.
성과 보고서 스킬(daily·mtd·monthly·creative-report)은 5.0.0에서 제거했고, 대신 Claude Code판에만 있던 스킬을 모두 옮겼습니다.

## 포함된 스킬

| 스킬 | 설명 |
|---|---|
| `naver-search` | 브랜드(자사·경쟁) 네이버 추정 검색수 비교(날짜 범위, HTML) |
| `naver-news` | 브랜드 네이버 뉴스 기사 수 비교 + 자사 주요 기사 4건(HTML) |
| `naver-blog` | 브랜드 네이버 블로그 글 수 비교 + 자사 주요 글 4건(HTML) |
| `weather-impact` | 서울 일별 기온·강수·불쾌지수(+광고 클릭이 있으면 비 온 날 차이, HTML) |
| `nextmonth-budget-planning` | 다음 달 예산 계획(HTML) — 기준 달 실적 · 추천 배분 · 피드백 반영 배분 비교, 사용자 피드백 반영 |
| `app-guide` | 라이트하우스 웹 화면(app.laight.ai) 사용법 안내(데이터 조회 없음) |
| `skill-catalog` | 라이트하우스 스킬 목록을 채팅에 표로 보여 준다 |

훅: `get_ad_performance` 대용량 응답 캡처(`capture_ad_performance.py`), 응답 원본 저장(`save_responses.py`),
광고 성과 도메인 규칙 주입(`ad_performance_domain.py`·`.md`).

## Claude Code판과의 차이

| | Claude Code (`plugins/laighthouse-analytics-prod/`) | ChatGPT / Codex (`laighthouse-analytics-gpt/`) |
|---|---|---|
| 매니페스트 | `.claude-plugin/plugin.json` | `.codex-plugin/plugin.json` + 스킬별 `agents/openai.yaml`(원본은 `agents-meta/`) |
| MCP | `.mcp.json` (`"type": "http"`) | `.mcp.json` (`"type": "streamable-http"`) |
| 훅 | `hooks/hooks.json` (`${CLAUDE_PLUGIN_ROOT}`, SessionStart(compact) 포함) | `hooks/hooks.json` (`${PLUGIN_ROOT}`, PostToolUse만 — 압축 뒤 도메인 규칙을 다시 넣지 않는다) |
| SKILL.md | 원본 | 외부 요인 스킬만 첫 제목 아래 ChatGPT/Codex 환경 안내(훅이 없는 웹 Chat에서의 응답 저장 방법)를 덧붙인다 |

## 구조

```
laighthouse-analytics-gpt/
├── .codex-plugin/plugin.json   # 플러그인 매니페스트 (skills/·hooks/ 경로 선언)
├── .mcp.json                   # laighthouse MCP 서버 (streamable-http)
├── agents-meta/<스킬>.yaml     # ChatGPT 스킬 메타 원본 → skills/<스킬>/agents/openai.yaml
├── hooks/                      # hooks.json + laighthouse-plugin-common 사본(capture_ad_performance·save_responses·ad_performance_domain)
├── skills/                     # sync_from_claude.py가 만드는 사본 — 직접 고치지 않는다
├── sync_from_claude.py         # Claude Code판 스킬 → skills/
└── build_skill_zips.ps1        # 웹 업로드용 스킬별 zip 생성 + 규격 검증
```

## 고치는 순서

1. 스킬은 Claude Code판에서 고칩니다. 공통 레포(laighthouse-plugin-common) 스킬이면 공통 레포에서 고치고 레포 루트에서
   `python3 ../laighthouse-plugin-common/sync.py`로 가져옵니다.
2. `python3 laighthouse-analytics-gpt/sync_from_claude.py`로 GPT판 사본을 다시 만듭니다(Claude Code판 스킬 폴더의 `shared/` 사본도 함께 맞춘다).
   `--check`는 사본이 어긋났는지만 보고 1로 끝나며, `tests/test_gpt_sync.py`가 같은 검사를 합니다.
3. 스킬을 새로 만들면 `agents-meta/<스킬>.yaml`을 함께 만듭니다(없으면 sync가 멈춘다).
4. 버전은 Claude Code판 `plugin.json`과 맞춥니다.

## 설치 A — 플러그인 (ChatGPT 데스크톱 Work 모드 / Codex)

1. 이 레포를 클론합니다. 레포 루트의 `.agents/plugins/marketplace.json`이 이 폴더를 플러그인으로 가리킵니다.
   레포 밖에서 쓰려면 `codex plugin marketplace add <레포 루트 경로>`.
2. Plugins Directory에서 소스 "Laighthouse (local)"을 선택해 **Laighthouse Analytics**를 설치합니다(MCP 인증은 설치 시).
3. 대화에서 `/hooks`를 열어 `capture_ad_performance.py`·`save_responses.py`·`ad_performance_domain.py`(get_ad_performance 응답에
   광고 성과 도메인 규칙 주입)를 신뢰합니다. 실행 환경에 `python3`가 필요합니다. 신뢰하지 않아도 스킬은 동작하지만, 외부 요인 스킬은
   모델이 응답을 직접 파일로 저장해야 합니다(각 SKILL.md의 ChatGPT/Codex 환경 안내).
4. 새 대화에서 `@`를 입력해 플러그인을 호출합니다. 플러그인 파일을 바꾼 뒤에는 앱을 재시작합니다.

## 설치 B — 스킬 zip (chatgpt.com 웹 일반 Chat)

웹에서는 스킬을 하나씩 업로드하고 MCP는 커넥터로 따로 연결합니다. 훅은 동작하지 않습니다.

```powershell
.\build_skill_zips.ps1                       # 전부
.\build_skill_zips.ps1 -Skill naver-search   # 하나만
```

`~/Downloads/laighthouse-gpt-skills/<스킬>.zip`이 만들어집니다. 스킬 폴더가 자기완결이라(`shared/` 사본 포함) 폴더를 그대로 묶고,
OpenAI Skills 규격(단일 최상위 폴더 / `SKILL.md` 1개 / 크기·파일 수 한도)을 검증합니다.
Sidebar → Plugins → Skills → Create → Upload from your computer에서 zip을 하나씩 올립니다.
