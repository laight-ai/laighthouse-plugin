# laighthouse-analytics

라이트하우스 MCP 연동 데이터를 성과 보고서(HTML)로 렌더링하는 Cowork
플러그인입니다.

## 컴포넌트

| 유형 | 이름 | 설명 |
|------|------|------|
| MCP | laighthouse | `https://app.laight.ai/api/mcp` 연동 |
| MCP | laighthouse_local | `https://sedative-duct-numerous.ngrok-free.dev/api/mcp` 연동(개발용) |
| 스킬 | daily-report |  데일리 보고서(HTML, 6개 섹션 — 목표·Summary·7일 성과·매체별 추이·매체 비교·계층 표) 렌더링 |
| 스킬 | mtd-report |  MTD 보고서(HTML, 8개 섹션 — 목표·Summary·월별 성과·매체별 추이·매체 비교·캠페인 분석·매체별 예산·계층 표) 렌더링 |
| 스킬 | monthly-report |  월간 보고서(HTML, 6개 섹션 — 목표·Summary·월별 성과·매체별 추이·매체 비교·계층 표) 렌더링 |
| 스킬 | creative-report |  소재 보고서(HTML, 6개 섹션 — 최우수 소재·Summary·전체 추이·상위 5개 CTR·ROAS·소재 누적 표) 렌더링 |
| 스킬 | naver-search | 외부 요인: 브랜드(자사·경쟁) 네이버 추정 검색수 비교(날짜 범위) |
| 스킬 | naver-news | 외부 요인: 브랜드 네이버 뉴스 기사 수 비교 + 자사 주요 기사 4건 |
| 스킬 | naver-blog | 외부 요인: 브랜드 네이버 블로그 글 수(제목 일치) 비교 + 자사 주요 글 4건 |
| 스킬 | weather-impact | 외부 요인: 서울 일별 기온·강수·불쾌지수, 광고 클릭이 있으면 겹치기 |
| 스킬 | nextmonth-budget-planning | 월간 미디어믹스 결과 보고서(HTML) — 라이트하우스 웹 결과 화면과 같은 모양, Claude 가 SKILL.md 의 뼈대대로 직접 작성 |
| 스킬 | app-guide | 라이트하우스 웹 화면(app.laight.ai) 사용법 — 메뉴 위치, 매체 연동·파일 업로드·목표 설정 등 순서 안내(데이터 조회 없음) |
| 스킬 | skill-catalog |  라이트하우스 스킬 목록(이름·명령어·설명·요청 예시)을 채팅에 표로 보여 준다(파일을 만들지 않는다) |

## 사용법

### 보고서 렌더링 (HTML)
> "MTD 보고서로 보여줘", "임원용 MTD 보고서로 보여줘" → `mtd-report`
> "데일리 보고서 만들어줘", "임원용 데일리 보고서 만들어줘" → `daily-report`
> "월간 보고서로 보여줘", "임원용 월간 보고서로 보여줘" → `monthly-report`
> "소재 보고서 만들어줘", "임원용 소재 보고서 만들어줘" → `creative-report`

4.0.0부터 임원용(요약)·실무용(상세) 스킬을 하나로 합쳤다 — 앞 섹션(목표·Executive Summary·추이·매체 비교)이 요약,
뒤의 계층 표(매체 단위로 접힌 채 시작)가 상세를 맡는다.

### 외부 요인 보고서 (3.3.0~)
> "현대카드 최근 2주 네이버 검색량" → `naver-search`
> "지난 2주 뉴스 얼마나 나왔고 주요 기사 뭐였어?" → `naver-news`
> "블로그에서 얼마나 얘기 나와?" → `naver-blog`
> "최근 2주 날씨가 광고 성과에 영향 줬는지" → `weather-impact`

입력은 브랜드와 날짜 범위(기본 어제까지 14일)다. 스킬은 MCP 도구 `get_external_context`(report-backend가 laighthouse-elt의
외부 맥락 데이터를 중계)를 1회 부르고(날씨는 `get_ad_performance`와 함께 2회), 저장 훅이 남긴 응답을 `assets/prepare.py`가
읽어 집계한다. 집계·HTML은 공통 킷 `shared/assets/external_context/`가
한다. 이 폴더와 스킬 4개의 원본은 laighthouse-plugin-common 레포다 — 여기서 고치지 말고 공통 레포에서 고친 뒤
레포 루트의 `common.json`대로 `python3 ../laighthouse-plugin-common/sync.py`로 가져온다(레포 루트 README 참고).
외부 데이터 수집 대상이 아닌 브랜드는 도구가 "is not collected for external context"로 거절한다.
수치 회귀 비교와 자체 검사는 공통 레포의 `tests/`에 있다.

### 미디어믹스 결과 (3.5.0~)
> "다라세제 미디어믹스 결과 보여줘" → `nextmonth-budget-planning` (내가 실행한 job 목록에서 골라 결과를 본다)
> "다라세제 3월 실적으로 4월 예산 7천만 원 미디어믹스 돌려줘" → `nextmonth-budget-planning` (조건을 확인받고 새로 실행 → 끝나면 보고서)

MCP 도구 `get_media_mix_job`을 기본 인자로 부르고, Claude 가 응답의 `summary`로 증감률·비중을 `python3`로 계산한 뒤
SKILL.md 의 「HTML 뼈대」대로 HTML 을 직접 쓴다(3.12.0~, 스크립트 없음). 표는 기준 달 「N월 현재까지」와 「M월 제안」을 나란히 두고,
제안 칸마다 현재 대비 증감을 빨강(상승)·파랑(하락)으로 붙인다. SKILL.md 의 원본은 laighthouse-plugin-common
레포다 — 공통 레포에서 고친 뒤 `sync.py`로 가져온다. 이전 렌더러(`assets/build_report.py`·`mm_view.js`·`mm_view.css`와 그 테스트)는 git 태그
`archive/media-mix-html-renderer`에 있다(되살리기: `git checkout archive/media-mix-html-renderer -- <경로>`).

각 보고서 종류는 별도 스킬로 나뉘어 있으며, report_type을 별도로 지정할 필요 없이 스킬 자체가
보고서 종류를 고정한다.

### 실행 흐름 (3.1.0~, 라운드 구조 4.0.0~)

1. **라운드 A** — 응답이 작은 호출(매체 단위·목표·프로모션)을 한 메시지에서 동시에 보낸다(4.0.0~).
2. PostToolUse 저장 훅(`hooks/save_responses.py`)이 응답 원본을 `<tmp>/laighthouse_mcp_responses/<session>/`에 남긴다.
3. 스킬의 `assets/prepare.py`(본체 `shared/assets/prepare_kit.py`)가 저장된 응답을 (도구 + 인자)로 골라 빌더 기본
   입력(`base.json`)과 요약 근거(`facts`)를 만든다. 모델은 응답 원문을 읽거나 옮겨 적지 않는다.
   저장된 응답이 없거나 최근 30분 안에 저장된 것이 없으면(같은 PC의 예전 응답 오판 방지) `note`를 낸다.
4. **라운드 B(·C)** — `note`가 없으면 `missing`에 나온 큰 호출(계층 표 3레벨, 소재 total, 상위 소재만의 소재 일별)을
   그대로 보내고 prepare.py를 다시 돌린다. 소재 일별은 `filters`(매체·상위 소재명)로 좁혀 받는다
   (ELENSILIA 실측 1,924,778자 → 27,428자).
5. 모델은 `facts`로 요약 문장만 쓰고 `build_report.py`에 `{"base": <경로>, "s2": …}`를 넘긴다.

라형식품 MTD 상세(2026-10-25) 실측: 기존 245.6초·MCP 22회 → 44.2초·MCP 7회, 보고서 수치는 동일.
저장 훅이 동작하지 않는 호스트에서는 prepare.py가 `note`를 내고, 각 스킬의 `references/legacy-flow.md`(기존 절차)로
진행한다 — 라운드 B를 보내지 않고, 계층 표는 캠페인·광고그룹까지(역할 지표 5개, 비율 열은 빌더가 채움)만 받는다. 캡처 훅(`hooks/capture_ad_performance.py`)은 대용량 응답을 스텁으로 바꿔 컨텍스트를 아끼는 역할로 남아 있다.

### 브랜드 비종속 동작

- 매체 목록과 지표 키는 응답에서 알아낸다(`prepare.py`, 폴백 절차에서는 `assets/discover.py`). 지표 키는 대소문자를
  무시하고 동의어(`광고비`/`cost`/`spend`/`Spending`, `노출`/`impressions`/`Imps` …)와 접두 일치
  (`매출_AB`)로 찾는다 — 규칙은 `shared/references/generic-report-pattern.md`.
- **매출 지표가 없는 브랜드**는 매출·ROAS 자리에 노출·클릭·CTR·CPC를 보여준다.
- **Organic(광고 외 귀속 매출)**은 데이터가 있는 브랜드에서만 표·차트·요약에 나온다.
- 목표는 `get_target_progress_v2`를 전체 매체(`media` 생략)로 1회 조회한다. 매체별 목표는 응답의 두 번째 표를 쓴다.
- 실무 상세 보고서의 캠페인 이하 성과는 매체→캠페인→광고그룹→광고 계층 표(펼치기·정렬·검색·
  지표 선택)로 보여준다.
- 렌더링 부품(목표 카드·차트·비교 표·계층 표)은 공용 킷 `shared/assets/report_kit.*` 한 곳에 있다.

## MCP 서버

- **이름**: laighthouse
- **타입**: HTTP (Streamable HTTP transport)
- **URL**: `https://app.laight.ai/api/mcp`
- **인증**: oauth2.1

- **이름**: laighthouse_local(개발용)
- **타입**: HTTP (Streamable HTTP transport)
- **URL**: `https://sedative-duct-numerous.ngrok-free.dev/api/mcp`
- **인증**: oauth2.1

## 설정

별도의 환경 변수 설정이 필요 없습니다.
MCP 서버가 인증을 요구하는 경우 `.mcp.json`의 `headers`에 토큰을 추가하세요:

```json
{
  "mcpServers": {
    "laighthouse": {
      "type": "http",
      "url": "https://app.laight.ai/api/mcp",
      "headers": {
        "Authorization": "Bearer ${LAIGHTHOUSE_API_TOKEN}"
      }
    }
  }
}
```
