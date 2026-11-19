# report_type 정의 및 스킬 매핑

이 플러그인이 렌더링하는 보고서 종류의 단일 소스다. 보고서 종류마다 **별도 스킬**이 있고,
사용자가 report_type을 따로 지정하는 개념이 없다 — 스킬 자체가 종류를 고정한다. 모든 스킬은
**브랜드 비종속**이다: 사용자가 말한 브랜드명을 그대로 쓰고, 매체 목록·지표 키는 실행 시작의
디스커버리 호출로 알아낸다 (`shared/references/generic-report-pattern.md`). 매출 지표가 없는
브랜드는 매출 없음 모드(노출·클릭·CTR·CPC), Organic 데이터가 있는 브랜드만 Organic 표시.

## report_type 개요

| report_type | 스킬 | 대상 | 섹션 수 |
|---|---|---|---|
| `daily` | `daily-report` | 일자별 성과 — 최근 7일 추이, 매체 비교·매체→광고 계층 표로 D-1 vs D-0 | 6 |
| `mtd` | `mtd-report` | 월초~기준일 누적 — 전월 동기 비교, 캠페인 분석, 매체별 예산, 계층 표 | 8 |
| `monthly` | `monthly-report` | 월 단위 — 6개월 추이, M-1 vs M0 매체 비교·계층 표 | 6 |
| `creative` | `creative-report` | 소재 단위(디스커버리로 선택한 매체 1개), 최근 7일 — 상위 소재 추이·소재 누적 표 | 6 |

- 임원용(요약)·실무용(상세)을 따로 두지 않는다(4.0.0에서 8개 스킬을 4개로 합쳤다). 요약은 앞 섹션
  (목표·Executive Summary·추이·매체 비교)이, 상세는 뒤의 계층 표가 맡는다.

- 섹션 구성·MCP 호출 명세는 각 스킬 폴더의 `SKILL.md`와 섹션 파일이 단일 소스다.
- MCP 도구 인벤토리와 응답 형식은 `shared/references/mcp-tools.md` 참고 — 서버 개편(ELT
  이관) 이후 성과 조회는 `get_ad_performance` 하나로 통합됐다.
- `weekly`는 지원 범위 밖이다. 사용자가 weekly 보고서를 요청하면, 아직 지원하지 않는다고
  알리고 daily/mtd/monthly/creative 중 무엇을 원하는지 확인한다.
- 예전에 존재하던 naver 기반 브랜드용 Word(.docx) 렌더러 스킬은 제거됐다 — 관련 요청이
  오면 위 HTML 스킬 중 알맞은 것을 안내한다.
