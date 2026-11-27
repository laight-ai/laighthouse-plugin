# laighthouse-analytics

라이트하우스 MCP 연동 데이터로 외부 요인 분석·예산 계획·화면 사용 안내를 하는 Cowork 플러그인입니다.
성과 보고서 스킬(daily·mtd·monthly·creative-report)은 5.0.0에서 제거했습니다.

## 컴포넌트

| 유형 | 이름 | 설명 |
|------|------|------|
| MCP | laighthouse | `https://app.laight.ai/api/mcp` 연동 |
| MCP | laighthouse_local | `https://sedative-duct-numerous.ngrok-free.dev/api/mcp` 연동(개발용) |
| 스킬 | naver-search | 외부 요인: 브랜드(자사·경쟁) 네이버 추정 검색수 비교(날짜 범위) |
| 스킬 | naver-news | 외부 요인: 브랜드 네이버 뉴스 기사 수 비교 + 자사 주요 기사 4건 |
| 스킬 | naver-blog | 외부 요인: 브랜드 네이버 블로그 글 수(제목 일치) 비교 + 자사 주요 글 4건 |
| 스킬 | weather-impact | 외부 요인: 서울 일별 기온·강수·불쾌지수, 광고 클릭이 있으면 겹치기 |
| 스킬 | nextmonth-budget-planning | 다음 달 예산 계획(HTML 보고서 + 채팅 평가) — 기준 달 실적 · 예산안 제안 · 피드백 반영 배분 비교, 사용자 피드백 반영 · 되돌리기, Claude 가 SKILL.md 의 뼈대대로 직접 작성 |
| 스킬 | media-mix-backtest-check | 예산안 백테스트 타당성 점검(HTML) — 과거 달 예산안을 그 시점 데이터로 다시 계산해 효율 추세 · 평소 월간 변동 폭 · 작년 흐름에 비춰 판정, 성과 검증 아님 |
| 스킬 | app-guide | 라이트하우스 웹 화면(app.laight.ai) 사용법 — 메뉴 위치, 매체 연동·파일 업로드·목표 설정 등 순서 안내(데이터 조회 없음) |
| 스킬 | skill-catalog |  라이트하우스 스킬 목록(이름·명령어·설명·요청 예시)을 채팅에 표로 보여 준다(파일을 만들지 않는다) |
| 훅 | ad_performance_domain | `get_ad_performance` 응답 뒤에 광고 성과 도메인 규칙(계약형 BRS, 광고집행/매출발생 상품 구분, 매체별 특이사항)을 세션당 한 번 넣는다 |

## 사용법

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

### 다음 달 예산 계획 (3.5.0~, 계획 도구 5.2.0~)
> "다라세제 다음 달 예산 계획 보여줘" → `nextmonth-budget-planning` (내가 시작한 계획 목록에서 골라 결과를 본다)
> "다라세제 3월 실적으로 4월 예산 7천만 원 계획 세워줘" → `nextmonth-budget-planning` (조건을 확인받고 새로 계산 → 끝나면 배분 표와 의견)
> "네이버는 4월 1~10일에 하루 50만 원으로 고정해줘" → 피드백으로 옮겨 되묻고, 확인받으면 반영해 다시 계산

MCP 미디어믹스 계획 도구(`start_media_mix_plan`·`get_media_mix_plan`·`propose_media_mix_claim`·`apply_media_mix_claim` 등)를 쓰고,
Claude 가 `get_media_mix_plan` 응답의 `summary`로 증감률·비중을 `python3`로 계산한 뒤 SKILL.md 의 「HTML 뼈대」대로 HTML 을 직접 쓴다
(3.12.0~, 스크립트 없음). 표는 기준 달 실적 · 예산안 제안 · 피드백 반영 배분(피드백이 있을 때만)을 나란히 두고, 배분 칸마다 앞 묶음 대비
증감을 빨강(상승)·파랑(하락)으로 붙인다. 사용자 피드백은 되묻고 확인받은 뒤에만 반영하고, 되돌리기도 한다. 잔여 예산은 처음부터 채운 배분으로 보여 준다.
첫 보고서 뒤에는 다음 행동 선지(조건 넣기 · 배분 이유 듣기)를 번호로 보여 주고,
비용 대비 효과 곡선은 물을 때만 채팅으로 답한다. 날짜별 금액은 제공하지 않는다. SKILL.md 의 원본은 laighthouse-plugin-common
레포다 — 공통 레포에서 고친 뒤 `sync.py`로 가져온다. 이전 렌더러(`assets/build_report.py`·`mm_view.js`·`mm_view.css`와 그 테스트)는 git 태그
`archive/media-mix-html-renderer`에 있다(되살리기: `git checkout archive/media-mix-html-renderer -- <경로>`).

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
