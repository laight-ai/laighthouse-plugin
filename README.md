# laighthouse-plugin

Laighthouse Analytics 플러그인을 위한 Claude Code 플러그인 마켓플레이스 저장소입니다. MCP로 연동된 라이트하우스에 적재된 데이터를 성과 보고서 형태로 렌더링하는 스킬들을 제공합니다.

> **ChatGPT Skills판**: 같은 보고서 로직을 ChatGPT Skills용으로 이식한 버전이
> [`laighthouse-analytics-gpt/`](laighthouse-analytics-gpt/README.md)에 있습니다(향후 별도
> 저장소로 분리 예정). Claude Code판과의 차이(스킬 매니페스트 형식, 훅 부재에 따른 대용량
> 응답 대응 방식)는 해당 폴더의 README를 참고하세요.

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
        ├── hooks/                 # PostToolUse 캡처 훅 (대용량 get_ad_performance 응답 → 파일)
        ├── shared/                # 스킬 간 공유 (플러그인 루트 기준 경로로 참조됨)
        │   ├── references/        # MCP 도구 규칙·브랜드 비종속 패턴·목표 카드 규칙
        │   └── assets/            # 공용 렌더링 킷 report_kit.py/.js/.css (카드·차트·비교 표·계층 표)
        └── skills/
            ├── daily-detailed/    #  데일리 보고서(HTML, 실무 상세)
            ├── daily-summary/     #  Executive 데일리 보고서(HTML, 임원용 요약)
            ├── mtd-detailed/      #  MTD 보고서(HTML, 실무 상세)
            ├── mtd-summary/       #  Executive MTD 보고서(HTML, 임원용 요약)
            ├── monthly-detailed/  #  월간 보고서(HTML, 실무 상세)
            ├── monthly-summary/   #  Executive 월간 보고서(HTML, 임원용 요약)
            ├── creative-detailed/ #  소재 보고서(HTML, 실무 상세)
            ├── creative-summary/  #  Executive 소재 보고서(HTML, 임원용 요약)
            ├── naver-search/      #  외부 요인: 네이버 검색량(HTML, 날짜 범위)
            ├── naver-news/        #  외부 요인: 네이버 뉴스 언급·주요 기사(HTML, 날짜 범위)
            ├── naver-blog/        #  외부 요인: 네이버 블로그 언급·주요 글(HTML, 날짜 범위)
            └── weather-impact/    #  외부 요인: 서울 날씨 + 광고 클릭 겹치기(HTML, 날짜 범위)
```

## 포함된 플러그인

### laighthouse-analytics-prod

라이트하우스 MCP 연동 데이터를 성과 보고서로 렌더링하는 플러그인입니다.

| 스킬 | 설명 |
|------|------|
| `daily-detailed` |  데일리 보고서(HTML, 실무 상세) 렌더링 |
| `daily-summary` |  Executive 데일리 보고서(HTML, 임원용 핵심 요약) 렌더링 |
| `mtd-detailed` |  MTD 보고서(HTML, 실무 상세) 렌더링 |
| `mtd-summary` |  Executive MTD 보고서(HTML, 임원용 핵심 요약) 렌더링 |
| `monthly-detailed` |  월간 보고서(HTML, 실무 상세) 렌더링 |
| `monthly-summary` |  Executive 월간 보고서(HTML, 임원용 핵심 요약) 렌더링 |
| `creative-detailed` |  소재 보고서(HTML, 실무 상세) 렌더링 |
| `creative-summary` |  Executive 소재 보고서(HTML, 임원용 핵심 요약) 렌더링 |
| `naver-search` | 브랜드(자사·경쟁) 네이버 추정 검색수 비교(날짜 범위) |
| `naver-news` | 브랜드 네이버 뉴스 기사 수 비교 + 자사 주요 기사 4건 |
| `naver-blog` | 브랜드 네이버 블로그 글 수 비교 + 자사 주요 글 4건 |
| `weather-impact` | 서울 일별 기온·강수·불쾌지수(+광고 클릭이 있으면 비 온 날 차이) |
| `skill-catalog` |  라이트하우스 스킬 목록(이름·명령어·설명·요청 예시)을 채팅에 표로 보여 준다 — "스킬 목록", "어떤 스킬 있어" |

자세한 사용법은 [플러그인 README](plugins/laighthouse-analytics-prod/README.md)를 참고하세요.

## 사용법 예시

- "<브랜드>의 MTD 보고서로 보여줘"
- "임원용 데일리 보고서 만들어줘"
- "<브랜드> 최근 2주 네이버 검색량을 경쟁사와 비교해줘", "<브랜드> 지난주 뉴스 주요 기사 뭐였어?"

## 마켓플레이스 등록

Claude Code에서 이 저장소를 마켓플레이스로 추가하면 `laighthouse-analytics-prod` 플러그인을 설치할 수 있습니다.
