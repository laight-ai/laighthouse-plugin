# laighthouse-plugin

Laighthouse Analytics 플러그인을 위한 Claude Code 플러그인 마켓플레이스 저장소입니다. MCP로 연동된 라이트하우스 데이터로 외부 요인 분석, 예산 계획, 화면 사용 안내를 하는 스킬과, `get_ad_performance` 응답 해석을 돕는 훅을 제공합니다.
성과 보고서 스킬(daily·mtd·monthly·creative-report)은 5.0.0에서 제거했습니다.

> **ChatGPT/Codex판**: Claude Code판 스킬을 그대로 옮긴 버전이 [`laighthouse-analytics-gpt/`](laighthouse-analytics-gpt/README.md)에
> 있습니다. `python3 laighthouse-analytics-gpt/sync_from_claude.py`가 Claude Code판 스킬 폴더를 복사해 만듭니다(직접 고치지 않습니다).

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
        ├── hooks/                 # PostToolUse·SessionStart 훅 (대용량 응답 캡처·응답 저장·get_ad_performance 도메인 규칙 주입)
        ├── shared/                # 스킬 간 공유 원본 (스킬 폴더마다 필요한 부분을 사본으로 넣는다)
        │   ├── references/        # MCP 도구 규칙
        │   └── assets/            # 외부 요인 보고서 킷(external_context/)
        └── skills/
            ├── naver-search/      #  외부 요인: 네이버 검색량(HTML, 날짜 범위)
            ├── naver-news/        #  외부 요인: 네이버 뉴스 언급·주요 기사(HTML, 날짜 범위)
            ├── naver-blog/        #  외부 요인: 네이버 블로그 언급·주요 글(HTML, 날짜 범위)
            ├── weather-impact/    #  외부 요인: 서울 날씨 + 광고 클릭 겹치기(HTML, 날짜 범위)
            ├── nextmonth-budget-planning/  #  다음 달 예산 계획(HTML, Claude 가 직접 작성)
            ├── app-guide/         #  라이트하우스 화면 사용법
            └── skill-catalog/     #  스킬 목록
```

**스킬 폴더는 혼자서 돌아야 합니다.** Claude Desktop Cowork는 스킬 폴더를 하나씩 따로 올리고 플러그인
루트의 `shared/`는 올리지 않습니다. 그래서 각 스킬은 필요한 공용 파일을 `skills/<스킬>/shared/`에 사본으로
갖고, 문서·스크립트는 스킬 폴더 기준 경로(`shared/references/…`, `shared/assets/…`)만 씁니다. 원본은 플러그인
루트 `shared/`이며 사본은 손으로 고치지 않습니다. `shared/`를 고쳤거나 스킬을 새로 만들었으면
`scripts/bundle_skills.py`의 목록을 확인하고 `python3 scripts/bundle_skills.py`로 사본을 다시 만듭니다.
사본이 어긋나면 `tests/test_skill_bundles.py`가 실패합니다.

세 플러그인이 함께 쓰는 파일(외부 요인 킷과 스킬 4개, nextmonth-budget-planning, app-guide, 훅)의 원본은
laighthouse-plugin-common 레포입니다. 어느 파일을 어느 태그로 가져오는지는 `common.json`에 적혀 있습니다. 공통 레포에서
고치고 태그를 붙인 뒤 `common.json`의 `version`을 바꾸고 `python3 ../laighthouse-plugin-common/sync.py`로 가져온 뒤
`python3 scripts/bundle_skills.py`를 실행합니다. 사본이 어긋나면 CI(`.github/workflows/common-check.yml`)가 실패합니다.
공통 레포에서 받는 스킬의 SKILL.md `metadata.version`은 그 스킬이 마지막으로 바뀐 공통 레포 태그를 따르므로 이 레포에서 올리지 않습니다.
플러그인 릴리스 버전(`plugin.json`·`marketplace.json`)은 공통 레포 태그를 새로 받을 때도 올립니다.

## 포함된 플러그인

### laighthouse-analytics-prod

라이트하우스 MCP 연동 데이터로 외부 요인 분석·예산 계획·화면 사용 안내를 하는 플러그인입니다.

| 스킬 | 설명 |
|------|------|
| `naver-search` | 브랜드(자사·경쟁) 네이버 추정 검색수 비교(날짜 범위) |
| `naver-news` | 브랜드 네이버 뉴스 기사 수 비교 + 자사 주요 기사 4건 |
| `naver-blog` | 브랜드 네이버 블로그 글 수 비교 + 자사 주요 글 4건 |
| `weather-impact` | 서울 일별 기온·강수·불쾌지수(+광고 클릭이 있으면 비 온 날 차이) |
| `nextmonth-budget-planning` | 다음 달 예산 계획(HTML) — 기준 달 실적 · 예산안 제안 · 피드백 반영 배분 비교, Claude 가 직접 작성. 조건 확인 후 새로 계산, 사용자 피드백 반영 · 되돌리기 · 잔여 예산 채우기 |
| `app-guide` | 라이트하우스 웹 화면(app.laight.ai) 사용법 — 메뉴 위치, 매체 연동·파일 업로드·목표 설정 등 순서 안내(데이터 조회 없음) — "라이트하우스 사용법", "메뉴 어디 있어" |
| `skill-catalog` |  라이트하우스 스킬 목록(이름·명령어·설명·요청 예시)을 채팅에 표로 보여 준다 — "스킬 목록", "어떤 스킬 있어" |

자세한 사용법은 [플러그인 README](plugins/laighthouse-analytics-prod/README.md)를 참고하세요.

## 사용법 예시

- "<브랜드>의 다음 달 예산 계획 세워줘"
- "<브랜드> 최근 2주 네이버 검색량을 경쟁사와 비교해줘", "<브랜드> 지난주 뉴스 주요 기사 뭐였어?"

## 마켓플레이스 등록

Claude Code에서 이 저장소를 마켓플레이스로 추가하면 `laighthouse-analytics-prod` 플러그인을 설치할 수 있습니다.
