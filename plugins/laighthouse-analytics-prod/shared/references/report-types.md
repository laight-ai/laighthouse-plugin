# report_type 정의 및 섹션 구성 (render-ppt / render-report-docx 공용)

렌더러 스킬이 공유하는 report_type별 대상 브랜드군·섹션 구성·순서 규칙의 단일 소스다.
아래 표의 파일명은 `shared/sections/{type}/` (데이터 스펙)과 각 스킬의 `sections/{type}/`
(출력 스펙)에 **같은 이름으로** 존재한다 — 두 파일을 짝으로 읽는다 (각 SKILL.md의 "섹션 읽기
규칙" 참고). 소비 스킬은 **render-ppt(PPT)와 render-report-docx(Word)** 두 개다 —
render-report(HTML)는 브리즘(breezm, airbridge type-b) 전용 스킬이라 이 파일의 report_type을
렌더링하지 않는다 (type-b의 `mtd`/`executive-mtd`는 render-report SKILL.md에, `creative`는
render-report-docx SKILL.md에 정의).

## report_type 개요

| report_type | 대상 브랜드군 | report-backend generator | 섹션 수 |
|---|---|---|---|
| `daily` | Meta/Google 브랜드 (Aqua Glow, Saturday Skin) 또는 naver 브랜드 (다형식품, 남양유업 등) | `saturdayskin` 또는 `default` | 6 |
| `mtd` (분기 A) | naver 기반 브랜드 (다형식품 등) | `default` | 11 |
| `monthly` | naver 기반 브랜드 (남양유업 등) | `default` | 8 |
| `executive-mtd` | naver 기반 브랜드 (남양유업 등, 임원 보고용) | `default` | 5 |

- `daily`는 브랜드군별로 폴더를 나누지 않는다 — 각 섹션 파일 하나가 **분기 A(Google/Meta,
  `saturdayskin` generator)**와 **분기 B(naver, `default` generator)** 두 분기를 모두 자체적으로
  처리한다. 어떤 분기를 쓸지는 brand_name의 실제 report-backend generator로 판단한다
  (`shared/sections/daily/daily-section-1-kpi-goals.md`의 분기 규칙 참고).
- `executive-mtd`는 `mtd`와 같은 부분월(MTD) 데이터를 다루지만, 임원이 딥다이브 없이 훑어볼 수
  있도록 섹션을 축약하고 "무엇이 크게 움직였는지/무엇을 결정해야 하는지" 위주로 재구성한 임원
  보고용 변형이다. 사용자가 "임원용 MTD", "executive mtd", "임원 보고서" 등을 요청하면 이
  report_type을 쓴다.
- `weekly`는 지원 범위 밖이다 (`report-backend`의 `domain/report.py::ReportType`에 대응 값 자체가
  없다 — `ABTEST`/`MTD`/`DAILY`/`MONTHLY`/`CALENDAR`/`DASHBOARD`만 존재). 사용자가 weekly 보고서를
  요청하면, 아직 지원하지 않는다고 알리고 daily/mtd/monthly/executive-mtd 중 무엇을 원하는지
  확인한다.
- daily/mtd/monthly/executive-mtd 모두 **섹션 구성은 report_type이 전부 결정**하며 사용자가
  섹션을 골라 지정하는 개념이 없다 — 아래 표에 있는 파일을 항상 전부 렌더링한다.

## `daily` — 6개 섹션 (Google/Meta 및 naver 브랜드 공용)

| 순서 | 섹션 | 파일명 |
|-----|------|--------|
| 1 | 월 목표 카드 | `daily-section-1-kpi-goals.md` |
| 2 | 목표 달성 현황 (Overview) | `daily-section-2-overview.md` |
| 3 | 성과요약 (Executive Summary) | `daily-section-3-executive-summary.md` |
| 4 | 최근 7일 성과 | `daily-section-4-sales-daily-chart.md` |
| 5 | 캠페인 성과 | `daily-section-5-campaign-performance.md` |
| 6 | 광고 그룹 및 키워드 성과 | `daily-section-6-adgroup-keyword-performance.md` |

각 섹션 파일 내부에 "분기 A(Google/Meta)"와 "분기 B(naver)" 매핑이 모두 들어있다 —
brand_name의 report-backend generator로 판단한 분기 쪽만 렌더링하고, 다른 분기는 무시한다.

## `mtd` 분기 A — 11개 섹션 (naver 기반 default 브랜드 전용 — 다형식품 등)

**DATA 섹션 + ANALYSIS 섹션으로 구성.** report-backend `default/_report_mtd.py`의 MTD 리포트는
두 종류로 나뉜다:
- **DATA 섹션** — `_mtd_components.build_mtd_report`가 prism 데이터로 만드는 컴포넌트(목표 달성 현황
  / 월별 광고 성과 / 상품별 누적 판매액 / 일일 카테고리별 매출 현황 / 매체 별 예산 소진 현황 /
  캠페인 별 성과 / 그룹 별 성과 / 키워드 별 성과 / 일별 광고기여 매출 분석). "목표 달성 현황"만
  프론트엔드가 2개 시각 블록(월 목표 카드 + 목표 달성 현황)으로 나눠 그린다.
- **ANALYSIS 섹션** — report-backend가 prism이 아니라 **dify 워크플로**로 생성해 붙이는 텍스트
  (`_run_dify_analysis` + `_build_mtd_analysis_result_components`): Executive Summary / 성과에 대한
  개괄 / 제품 판매 성과의 심층 분석 / 광고 그룹별 심층 분석. 스킬에서는 dify 대신 실행 LLM이 그
  역할을 하며, 해당 DATA 섹션과 동일한 근거 수치(각 MCP 도구 결과)를 바탕으로 텍스트를 직접
  작성한다 — 새 수치를 지어내지 않는다.

2026-05-15 다형식품 실제 MTD PDF와 대조해 순서/구성을 확정했다.

| 순서 | 섹션 | 파일명 |
|-----|------|--------|
| 1 | 월 목표 카드 | `mtd-section-1-kpi-goals.md` |
| 2 | 목표 달성 현황 | `mtd-section-2-achievement.md` |
| 3 | Executive Summary | `mtd-section-3-executive-summary.md` |
| 4 | 월별 광고 성과 차트 | `mtd-section-4-monthly-chart.md` |
| 5 | 제품 판매 성과의 심층 분석 | `mtd-section-5-product-deep-dive.md` |
| 6 | 일일 카테고리별 매출 현황 | `mtd-section-6-daily-category-chart.md` |
| 7 | 매체별 예산 소진 현황 | `mtd-section-7-media-budget-progress.md` |
| 8 | 캠페인별 성과 심층 분석 | `mtd-section-8-campaign-deep-dive.md` |
| 9 | 캠페인별 성과 | `mtd-section-9-campaign-performance.md` |
| 10 | 광고그룹별 성과 | `mtd-section-10-group-performance.md` |
| 11 | 키워드별 성과 | `mtd-section-11-keyword-performance.md` |

- 순서 1(월 목표 카드)과 2(목표 달성 현황)는 **항상 붙어서** 렌더링한다 — 둘 다 같은
  target/achievement 응답을 재사용하며, 별도 재호출 없음 (`mtd-section-1-kpi-goals.md` 참고).
- `mtd-section-6.1-product-cumulative-sales.md`(카테고리별 월 누적 매출)는 **참조용 데이터
  스펙**이다 — 자체 출력 섹션은 없고, 섹션 5/6과 Executive Summary의 근거 데이터로만 쓴다
  (`shared/sections/mtd/`에만 존재하고 각 스킬 `sections/mtd/`에는 출력 스펙 파일이 없다).

## `monthly` — 8개 섹션 (naver 기반 default 브랜드 전용 — 남양유업 등)

mtd와 동일한 naver 기반 default generator를 쓰되, 항상 해당 월 전체(월초~말일) 실적을 다룬다는
점이 다르다 (mtd는 월초~기준일까지의 부분월/MTD). mtd에는 없는 두 개의 신규 섹션(카테고리별
월간 매출액 비교, 매체별 성과 비교)이 포함된다.

| 순서 | 섹션 | 파일명 |
|-----|------|--------|
| 1 | 월 목표 카드 | `monthly-section-1-kpi-goals.md` |
| 2 | 목표 달성 현황 | `monthly-section-2-achievement.md` |
| 3 | Executive Summary | `monthly-section-3-executive-summary.md` |
| 4 | 월별 광고 성과 차트 | `monthly-section-4-ad-performance-chart.md` |
| 5 | 제품 판매 트렌드 분석 | `monthly-section-5-product-deep-dive.md` |
| 6 | 카테고리별 월간 매출액 비교 | `monthly-section-6-category-monthly-comparison.md` |
| 7 | 일일 카테고리별 매출 현황 | `monthly-section-7-daily-category-chart.md` |
| 8 | 매체별 성과 비교 | `monthly-section-8-media-comparison-table.md` |

순서 1과 2는 **항상 붙어서** 렌더링한다 — 둘 다 같은 `get_target_progress_v2` 응답
(as_of_date=해당 월 말일)을 재사용하며, 별도 재호출 없음 (`monthly-section-1-kpi-goals.md` 참고).

## `executive-mtd` — 5개 섹션 (naver 기반 default 브랜드 전용, 임원 보고용)

mtd와 동일한 부분월(MTD) 기준일을 다루지만, 임원이 딥다이브 없이 훑어보도록 11개 섹션을 5개로
축약하고 순서도 재구성한 임원 보고용 변형이다. mtd에는 없는 두 개의 신규 섹션(주요 카테고리별
월간 매출액 증감, 매체별 성과 비교)이 포함되고, mtd의 "제품 판매 성과의 심층 분석"/"매체별 예산
소진 현황"/"캠페인·그룹·키워드별 성과" 섹션들은 포함하지 않는다. 별도의 월 목표 카드(kpi-goals)
섹션은 제거되어, 목표 달성 현황이 첫 번째 섹션이다.

| 순서 | 섹션 | 파일명 |
|-----|------|--------|
| 1 | 목표 달성 현황 | `executive-mtd-section-1-achievement.md` |
| 2 | 월별 광고 성과 차트 | `executive-mtd-section-2-monthly-chart.md` |
| 3 | Executive Summary | `executive-mtd-section-3-executive-summary.md` |
| 4 | 주요 카테고리별 월간 매출액 증감 | `executive-mtd-section-4-category-mom-highlights.md` |
| 5 | 매체별 성과 비교 | `executive-mtd-section-5-media-roas-comparison.md` |

⚠️ mtd/monthly와 순서가 다르다 — 여기서는 월별 광고 성과 차트(2번)가 Executive Summary(3번)보다
**먼저** 온다. 임원이 먼저 추세 그래프로 큰 그림을 보고, 그다음 Executive Summary에서 그 추세에
대한 해석/의사결정 포인트를 읽게 하려는 의도다 (`executive-mtd-section-2-monthly-chart.md` 참고).
