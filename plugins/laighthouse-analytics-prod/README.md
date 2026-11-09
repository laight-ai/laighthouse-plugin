# laighthouse-analytics

라이트하우스 MCP 연동 데이터를 성과 보고서(HTML)로 렌더링하는 Cowork
플러그인입니다.

## 컴포넌트

| 유형 | 이름 | 설명 |
|------|------|------|
| MCP | laighthouse | `https://app.laight.ai/api/mcp` 연동 |
| MCP | laighthouse_local | `https://sedative-duct-numerous.ngrok-free.dev/api/mcp` 연동(개발용) |
| 스킬 | mtd-detailed |  MTD 보고서(HTML, 7개 섹션, 실무 상세) 렌더링 |
| 스킬 | mtd-summary |  Executive MTD 보고서(HTML, 5개 섹션, 임원용 핵심 요약) 렌더링 |
| 스킬 | daily-detailed |  데일리 보고서(HTML, 4개 섹션, 실무 상세 — 매체·캠페인·광고그룹·광고 계층 표) 렌더링 |
| 스킬 | daily-summary |  Executive 데일리 보고서(HTML, 5개 섹션, 임원용 핵심 요약) 렌더링 |
| 스킬 | monthly-detailed |  월간 보고서(HTML, 5개 섹션, 실무 상세) 렌더링 |
| 스킬 | monthly-summary |  Executive 월간 보고서(HTML, 5개 섹션, 임원용 핵심 요약) 렌더링 |
| 스킬 | creative-detailed |  소재 보고서(HTML, 5개 섹션, 실무 상세) 렌더링 |
| 스킬 | creative-summary |  Executive 소재 보고서(HTML, 5개 섹션, 임원용 핵심 요약) 렌더링 |
| 스킬 | naver-search | 외부 요인: 브랜드(자사·경쟁) 네이버 추정 검색수 비교(날짜 범위) |
| 스킬 | naver-news | 외부 요인: 브랜드 네이버 뉴스 기사 수 비교 + 자사 주요 기사 4건 |
| 스킬 | naver-blog | 외부 요인: 브랜드 네이버 블로그 글 수(제목 일치) 비교 + 자사 주요 글 4건 |
| 스킬 | weather-impact | 외부 요인: 서울 일별 기온·강수·불쾌지수, 광고 클릭이 있으면 겹치기 |
| 스킬 | media-mix-result | 월간 미디어믹스 결과 보고서(HTML) — 라이트하우스 웹 결과 화면과 같은 모양, 전용 킷(`assets/mm_view.*`) |
| 스킬 | skill-catalog |  라이트하우스 스킬 목록(이름·명령어·설명·요청 예시)을 채팅에 표로 보여 준다(파일을 만들지 않는다) |

## 사용법

### 보고서 렌더링 (HTML)
> "MTD 보고서로 보여줘" → `mtd-detailed`
> "임원용 MTD 보고서로 보여줘" → `mtd-summary`
> "데일리 보고서 만들어줘" → `daily-detailed`
> "임원용 데일리 보고서 만들어줘" → `daily-summary`
> "월간 보고서로 보여줘" → `monthly-detailed`
> "임원용 월간 보고서로 보여줘" → `monthly-summary`
> "소재 보고서 만들어줘" → `creative-detailed`
> "임원용 소재 보고서 만들어줘" → `creative-summary`

### 외부 요인 보고서 (3.3.0~)
> "현대카드 최근 2주 네이버 검색량" → `naver-search`
> "지난 2주 뉴스 얼마나 나왔고 주요 기사 뭐였어?" → `naver-news`
> "블로그에서 얼마나 얘기 나와?" → `naver-blog`
> "최근 2주 날씨가 광고 성과에 영향 줬는지" → `weather-impact`

입력은 브랜드와 날짜 범위(기본 어제까지 14일)다. 스킬은 MCP 도구 `get_external_context`(report-backend가 laighthouse-elt의
외부 맥락 데이터를 중계)를 1회 부르고(날씨는 `get_ad_performance`와 함께 2회), 저장 훅이 남긴 응답을 `assets/prepare.py`가
읽어 집계한다. 집계·HTML은 공통 킷 `shared/assets/external_context/`가
한다. 이 폴더와 스킬 4개는 laighthouse-plugin-agency(`laighthouse-agency`)와 같은 파일이다 — 고칠 때는 양쪽을 함께 고친다.
외부 데이터 수집 대상이 아닌 브랜드는 도구가 "is not collected for external context"로 거절한다.
수치 회귀 비교: `python3 tests/regress_external_context.py --responses <응답 폴더> --baseline <기준 폴더>`(기준은 같은 명령에 `--write`로 먼저 만든다),
자체 검사: `python3 tests/test_weather_trend.py`·`tests/test_responses.py`·`tests/test_range_rules.py`·`tests/test_citations.py`.

### 미디어믹스 결과 (3.5.0~)
> "다라세제 미디어믹스 결과 보여줘, job id …" → `media-mix-result` (이미 끝난 계산)
> "다라세제 3월 실적으로 4월 예산 7천만 원 미디어믹스 돌려줘" → `media-mix-result` (조건을 확인받고 새로 실행 → 끝나면 보고서)

MCP 도구 `get_media_mix_job`을 `include_allocation`·`include_diagnostics`로 1회 부르고, 저장 훅이 남긴 응답을
`assets/build_report.py`가 그대로 HTML에 넣는다(응답 읽기는 `shared/assets/prepare_kit.py`). 계산·모양은 전용 킷
`assets/mm_view.js`·`mm_view.css`가 맡고, laighthouse-web 결과 화면(`src/pages/marketing/MediaMixResult.tsx`·`src/lib/mediaMix.ts`)을
옮긴 것이다 — 웹 화면이 바뀌면 함께 고친다. 이 스킬(`build_report.py`의 응답 읽기 부분 제외)은 laighthouse-plugin-agency와 같은 파일이다 —
고칠 때는 양쪽을 함께 고친다. 자체 검사: `python3 tests/test_media_mix_result.py`(node 가 있으면 `mm_view.js` 계산도 웹과 같은지 본다,
입력은 웹 목 데이터 사본 `tests/fixtures/media_mix/`).

각 보고서 종류는 별도 스킬로 나뉘어 있으며, report_type을 별도로 지정할 필요 없이 스킬 자체가
보고서 종류를 고정한다.

### 실행 흐름 (3.1.0~)

1. 스킬의 MCP 호출을 **한 메시지에서 동시에** 보낸다(필터 없는 호출 위주 — mtd-detailed 7개, 소재 보고서 3개 등).
2. PostToolUse 저장 훅(`hooks/save_responses.py`)이 응답 원본을 `<tmp>/laighthouse_mcp_responses/<session>/`에 남긴다.
3. 스킬의 `assets/prepare.py`(본체 `shared/assets/prepare_kit.py`)가 저장된 응답을 (도구 + 인자)로 골라 빌더 기본
   입력(`base.json`)과 요약 근거(`facts`)를 만든다. 모델은 응답 원문을 읽거나 옮겨 적지 않는다.
4. 모델은 `facts`로 요약 문장만 쓰고 `build_report.py`에 `{"base": <경로>, "s2": …}`를 넘긴다.

라형식품 MTD 상세(2026-10-25) 실측: 기존 245.6초·MCP 22회 → 44.2초·MCP 7회, 보고서 수치는 동일.
저장 훅이 동작하지 않는 호스트에서는 prepare.py가 `note`를 내고, 각 스킬의 `references/legacy-flow.md`(기존 절차)로
진행한다. 캡처 훅(`hooks/capture_ad_performance.py`)은 대용량 응답을 스텁으로 바꿔 컨텍스트를 아끼는 역할로 남아 있다.

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
