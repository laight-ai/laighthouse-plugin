# render-report: HTML → DOCX 전환 설계

**날짜:** 2026-07-23
**대상:** `plugins/laighthouse-analytics-prod/skills/render-report/`

## 배경

현재 `render-report` 스킬은 MCP 데이터를 받아 HTML 문자열(카드/Chart.js 캔버스/테이블)로 조합해
Artifact 게시 + `.html` 파일 저장 두 곳에 낸다. 앞으로는 이 스킬의 산출물을 **Word(.docx)** 파일로
바꾼다. 기존 HTML 버전은 더 이상 유지하지 않지만, git 브랜치로 백업만 남겨둔다.

## 1. Git 브랜치 전략

1. 현재 `main` 상태를 `backup/render-report-html`이라는 브랜치로 백업한다 (현재 커밋을 그대로
   가리키는 브랜치 생성, push는 사용자가 별도로 요청할 때만).
2. 실제 작업은 `feature/render-report-docx` 브랜치에서 진행한다.
3. 완료 후 `main`에 머지한다 — 머지 이후 `main`의 `render-report`는 docx 버전이 되고, html
   버전은 `backup/render-report-html`에서만 조회 가능하다.

## 2. 산출물 변화

- 기존: `{SECTIONS}`를 HTML 골격에 삽입 → Artifact 게시 + `~/Downloads/laighthouse-reports/*.html` 저장.
- 이후: 각 섹션을 **구조화된 JSON**(표/카드/차트 스펙)으로 만들어 → 생성 스크립트에 넘겨 →
  `~/Downloads/laighthouse-reports/{brand_name}_{report_type}_{기준_일자}.docx` 파일 하나로 저장.
  Artifact(브라우저) 게시는 docx를 렌더링할 수 없으므로 더 이상 하지 않는다 — 완료 메시지에 저장된
  docx 경로만 안내한다.

## 3. 생성 메커니즘

python-docx(문서 구조: 제목/문단/표/스타일) + 커스텀 OOXML 헬퍼(네이티브 Word 차트,
`c:barChart`/`c:lineChart` combo)로 구성된 재사용 스크립트를 스킬 `assets/`에 둔다:

- `assets/docx_report/build.py` — CLI 진입점. `--report-type`, `--data <json 파일>`, `--out <경로>`
  인자를 받아 최종 `.docx`를 만든다.
- `assets/docx_report/sections.py` — report_type별 섹션 순서/타입(표/카드/차트/텍스트)에 따라
  python-docx 문서에 요소를 추가하는 렌더러.
- `assets/docx_report/charts.py` — python-docx가 지원하지 않는 네이티브 차트 파트를 직접 만드는
  모듈. `word/charts/chartN.xml`, 관계(`_rels`), `[Content_Types].xml` 엔트리, 그래픽프레임
  drawing XML을 조립해 문서에 삽입한다. bar+line combo(광고비/매출 막대 + ROAS 선) 한 종류를
  먼저 구현하고, 이후 필요한 차트 종류(단일 line 등)를 같은 모듈에 추가한다.
- 이 스크립트는 **데이터 가공/집계를 하지 않는다** — LLM이 MCP 응답을 그대로 옮겨 적은 JSON을
  입력받아 그대로 문서에 채워 넣기만 한다 (기존 "MCP 데이터 그대로 렌더링" 절대 지침 유지).
- Claude Code 실행 흐름: MCP 호출 → 섹션별 JSON 조립 → 임시 JSON 파일 저장 → Bash로
  `python assets/docx_report/build.py ...` 1회 실행 → 결과 docx 확인.
- 이 스킬은 이 생성 스크립트 외의 임시 스크립트(데이터 가공용 등)는 만들지 않는다는 지침은
  유지한다 — 유일한 예외가 이 재사용 가능한 build 스크립트다.

## 4. 섹션 `.md` 파일 전환

각 `sections/{report_type}/*.md`의 `## HTML` + `## Script` 블록을, 아래 구조를 설명하는
`## DOCX 구조` 블록으로 교체한다 (섹션마다 필요한 것만 사용):

- **KPI 카드형 섹션** (예: mtd-section-1/2) → 2~3열 표(테두리 있는 표로 카드 흉내) + 굵게/색상은
  런(run) 단위 폰트 색으로 표현 (Word 표는 flexbox 그라디언트 등은 못 쓰므로 단순화).
- **표 섹션** (예: campaign/keyword/group performance) → 그대로 Word 표. 기존 HTML의 검색창/
  페이지네이션(JS 기능)은 정적 문서에 의미가 없으므로 제거하고, 전체 행을 한 표에 다 낸다.
- **차트 섹션** (예: monthly-chart, sales-daily-chart) → `charts.py`가 그리는 네이티브 콤보 차트
  하나로 대체. Chart.js의 이중 y축(막대+선)과 동일한 형태를 유지한다.
- **텍스트 섹션** (Executive Summary 등) → 일반 문단(Heading + Paragraph).

기존 "필요 데이터 (MCP)" 절과 도구 호출 규칙, 데이터 처리 절대 지침은 그대로 유지 — 바뀌는 것은
마크업 형식뿐이다.

## 5. 범위

daily/mtd/monthly/executive-mtd 4종 모두 최종 지원 대상. 구현 순서는 `mtd`(가장 대표적인 11개
섹션 구성)로 생성기(표+카드+콤보차트 1개)를 먼저 끝까지 검증한 뒤, 검증된 패턴으로 나머지 3종을
포팅한다.

## 6. 검증 방법

시각적 프리뷰가 없으므로:
1. 스크립트가 에러 없이 종료하고 `.docx`가 생성되는지 확인.
2. `python -c "from docx import Document; Document('out.docx')"` 로 파일이 깨지지 않고 열리는지
   왕복 확인.
3. mtd 첫 결과물은 사용자가 직접 Word로 열어 눈으로 확인 — 이후 나머지 3종 포팅 전에 통과 여부를
   확인받는다.

## 7. SKILL.md 갱신 사항

- 완료 메시지 형식에서 "Artifact 게시" 관련 문구 제거, 저장된 `.docx` 경로만 안내.
- "별도 스크립트 생성 금지" 절대 지침에 `assets/docx_report/build.py` 호출은 예외임을 명시.
- 보고서 골격(HTML 템플릿) 절 전체를 docx 조립 순서 설명으로 교체.
- Chart.js 인라인 관련 경고(`assets/chart.umd.min.js`) 제거 — 더 이상 쓰지 않음.
