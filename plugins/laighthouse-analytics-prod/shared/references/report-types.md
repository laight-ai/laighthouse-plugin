# report_type 정의 및 스킬 매핑

이 플러그인이 렌더링하는 보고서 종류의 단일 소스다. 보고서 종류마다 **별도 스킬**이 있고,
사용자가 report_type을 따로 지정하는 개념이 없다 — 스킬 자체가 종류를 고정한다. 모든 스킬의
대상 브랜드는 브리즘(breezm, airbridge 기반) 하나뿐이다.

## report_type 개요

| report_type | 스킬 | 대상 | 섹션 수 |
|---|---|---|---|
| `daily` (실무 상세) | `daily-detailed` | 일자별 성과, D-1 vs D-0 비교 | 5 |
| `daily` (임원 요약) | `daily-summary` | 매체 단위 D-1 vs D-0 | 5 |
| `mtd` (실무 상세) | `mtd-detailed` | 월초~기준일 누적 | 7 |
| `mtd` (임원 요약) | `mtd-summary` | 월초~기준일 누적, 전월 동기 비교 | 5 |
| `monthly` (실무 상세) | `monthly-detailed` | 월 단위, M-1 vs M0 | 5 |
| `monthly` (임원 요약) | `monthly-summary` | 월 단위, M-1 vs M0 + 분기 비교 | 5 |
| `creative` (실무 상세) | `creative-detailed` | 소재(Meta Ads) 단위, 최근 7일 | 5 |
| `creative` (임원 요약) | `creative-summary` | 소재(Meta Ads) 단위, 최근 7일 | 5 |
| (예산 최적화) | `mid-month-optimizer` | 월중 예산 리밸런싱 제안 | — |

- 섹션 구성·MCP 호출 명세는 각 스킬 폴더의 `SKILL.md`와 섹션 파일이 단일 소스다.
- MCP 도구 인벤토리와 응답 형식은 `shared/references/mcp-tools.md` 참고 — 서버 개편(ELT
  이관) 이후 성과 조회는 `get_ad_performance` 하나로 통합됐다.
- `weekly`는 지원 범위 밖이다. 사용자가 weekly 보고서를 요청하면, 아직 지원하지 않는다고
  알리고 daily/mtd/monthly/creative 중 무엇을 원하는지 확인한다.
- 예전에 존재하던 naver 기반 브랜드용 Word(.docx) 렌더러 스킬은 제거됐다 — 관련 요청이
  오면 위 HTML 스킬 중 알맞은 것을 안내한다.
