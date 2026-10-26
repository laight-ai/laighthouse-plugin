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
