# render-ppt 신규 스킬 — 16:9 PPT 성과 보고서

날짜: 2026-07-24
상태: 구현됨 (샘플 PDF 시각 검수 통과)

## 배경과 결정 경로

render-report의 산출물 전환 시도 이력:

1. **1세대 docx 네이티브 렌더러** (`feature/render-report-docx`) — Word 기본 스타일 의존으로
   시각 품질 미달, 폐기.
2. **스크린샷 임베드 docx** (설계만) — 본문이 이미지가 되어 복사/편집 불가, 사용자 거부.
3. **2세대 docx 네이티브 렌더러** (디자인 토큰 기반 전면 재작성) — "나쁘지 않지만 좋지도
   않다" 평가. Word의 흐름 레이아웃에서는 카드 UI가 근본적으로 근사치에 그친다.
4. **최종 (사용자 결정)**: docx는 폐기하고 render-report를 HTML 시절로 롤백, **별도
   신규 스킬 `render-ppt`**로 16:9 PowerPoint 산출.

PPT가 맞는 이유: 절대 좌표 + 진짜 도형(둥근 모서리 카드) + 네이티브 편집 가능 차트/표 —
HTML 카드 대시보드의 디자인 언어가 슬라이드 매체와 1:1로 호환된다.

## 확정 파라미터 (사용자 선택)

- 판형: **16:9 가로** (13.333in × 7.5in)
- render-report: **HTML 산출로 롤백** (c85fb13 상태 유지), render-ppt는 독립 스킬
- 수백~수천 행 표: **상위 N(12)행만** + "외 n행 생략" 캡션, 합계 행은 항상 보존

## 구조

```
skills/render-ppt/
├── SKILL.md                  # fce1c8f docx SKILL.md 기반, pptx로 전환 (오케스트레이션 동일)
├── sections/{daily,mtd,Monthly,executive-mtd}/*.md   # "## PPT 섹션" JSON 블록
└── assets/pptx_report/
    ├── theme.py              # HTML 디자인 토큰 + 슬라이드 지오메트리 (단일 소스)
    ├── slides.py             # 커버/간지/KPI카드/표/텍스트/차트 슬라이드 빌더
    ├── charts.py             # 콤보 차트 chartSpace XML 수제 생성 + graphicFrame 주입
    ├── build.py              # CLI: 섹션 JSON → .pptx (섹션 1개 = 슬라이드 1장)
    ├── section_mapping.py    # MCP 응답 → 섹션 JSON (fce1c8f 검증본 그대로)
    ├── map_section.py
    └── tests/                # 63 tests (매핑 43 + 렌더러 20)
```

## 렌더링 규칙

| 요소 | 구현 |
|---|---|
| 슬라이드 배경 | `#f8fafc` (HTML body 배경) |
| 커버 | 파랑 액센트 라인 + 30pt 제목 + 기간 |
| 슬라이드 제목 | 파랑 세로 액센트 바 + 18pt bold (.section-title 대응) |
| KPI 카드 | 둥근 모서리 흰 카드 + `#e2e8f0` 테두리, 라벨 12pt/값 24pt bold/증감 초록·빨강 |
| 표 | "No Style, No Grid" 스타일 강제, 헤더 밴드 `#f1f5f9`, 행 하단 헤어라인, 합계행 강조, 리치 셀(`{text,color,bold}`)·바 셀(색 라벨) 지원 |
| 표 상위 N | body 12행 초과 시 truncate, 합계 행 보존, "외 n행 생략" 캡션 |
| 텍스트 | 둥근 카드 안 13pt, 줄간 1.3 |
| 차트 | 네이티브 콤보(막대+보조축 라인) chartSpace XML 수제 생성 — 시리즈색(회색/파랑/빨강 라인), Y축만 연회색 그리드, 축 숫자 `#,##0`, 하단 범례, 맑은 고딕. `c:ser` 자식 순서(idx→order→tx→spPr→marker→cat→val→smooth)는 스키마 필수 |
| 간지 heading | 뒤따르는 섹션에 heading이 없으면 그 슬라이드 제목으로 흡수(간지 슬라이드 낭비 방지) |
| 폰트 | 맑은 고딕, 한글은 `a:ea` 슬롯까지 지정 |

## 검증

- pytest 63개 통과.
- 전 XML 파트 well-formed + 차트 시리즈 순서 검사.
- PowerPoint COM으로 샘플을 PDF 변환(복구 오류 없이 열림 = 차트 XML 스키마 검증)
  후 페이지별 시각 검수 통과. (Word COM은 비대화형 세션에서 블로킹됐지만 PowerPoint
  COM은 정상 작동.)
