# MCP 도구 라우팅 규칙 (render-report / render-ppt / render-report-docx 공용)

세 렌더러 스킬(HTML/PPT/DOCX)이 동일하게 따르는 데이터 수집 규칙이다. 이 파일이 단일
소스(single source of truth)이며, 각 SKILL.md의 실행 순서 2~4단계가 이 파일을 참조한다.
"render-report 전용"이라고 표기된 항목은 mtd 분기 B(type-b) 등 HTML 보고서에만 존재하는
분기에 관한 것이다.

## 1. target/achievement 도구 라우팅 (실행 순서 2단계)

**report_type에 따라 쓰는 도구가 다르다 — 절대 섞지 않는다:**

- `daily`: brand_name의 report-backend generator로 분기를 먼저 판단한다
  (`shared/sections/daily/daily-section-1-kpi-goals.md` 분기 규칙 참고).
  - **분기 A (Google/Meta 브랜드, `saturdayskin` generator)** →
    `mcp__laighthouse__target_progress`(범용 v1 도구)에 `{ "campaign_type": "sales" }` 1회.
    `saturdayskin/_components.py`가 `metric.actual_mtd`를 그대로 신뢰하므로 응답을 그대로
    사용한다.
  - **분기 B (naver 브랜드, `default` generator)** →
    `mcp__laighthouse__get_target_progress_v2`(mtd와 동일한 v2 전용 도구)에
    `{ "brand_name": "...", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }` 1회 — daily는
    하루 기준 스냅샷이므로 `as_of_date`는 항상 사용자가 지정한 기준일 그대로 쓴다 (범용
    `target_progress`를 여기 쓰면 naver 브랜드는 매출/ROAS가 전부 0으로 나온다).
- `mtd` **분기 B(type-b, airbridge 기반 — render-report 전용)** →
  `mcp__laighthouse__get_target_progress_v2`를
  `{ "brand_name": "...", "month": "YYYY-MM", "media": "...", "as_of_date": "target_date" }`로
  **google/meta/naver 세 번** (`media`만 바꿔) 호출한다 —
  `render-report/sections/mtd-type-b/mtd-type-b-section-1-target-achievement.md` 참고. 세 매체 모두
  `"No {media} budget/target available for {month}."` 메시지가 돌아오면(type-b 브랜드에 media_mix
  데이터가 없는 현재 상태 — **오류가 아니다**) 목표 필드는 전부 N/A로 표시하고, 실적은
  `get_ad_performance_daily_table`에서 대신 가져온다 (섹션 파일의 대체 규칙 참고).
- `mtd` 분기 A (naver 브랜드) → `mcp__laighthouse__get_target_progress_v2`(v2 전용 도구)에
  `{ "brand_name": "...", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }` 1회.
  ⚠️ **범용 `target_progress`를 mtd에 쓰면 안 된다** — v1은 `aw_compiled`/`fb_compiled`(Google/Meta)
  실적 테이블만 보므로 naver 전용 브랜드는 매출/ROAS 목표·실적이 전부 0으로 나온다 (2026-07-10
  확인, `laighthouse-prism`에 `get_target_progress_v2` 툴을 새로 등록해 해결함). 이 도구는
  target(`target_cost`/`target_revenue`/`target_roas`)과 actual(`actual_cost`/`actual_revenue`/
  `actual_roas` — markdown 표의 target/actual 열)을 한 번에 반환하므로 별도 합산이 필요 없다 —
  `shared/sections/mtd/mtd-section-2-achievement.md` 참고.
- `monthly` (naver 브랜드, full month) → `mcp__laighthouse__get_target_progress_v2`(mtd와 동일
  v2 도구)에 `{ "brand_name": "...", "month": "YYYY-MM", "media": "naver", "as_of_date": "해당 월의 마지막 날" }`
  1회. 도구/파라미터 형태는 mtd와 동일하며, 유일한 차이는 `as_of_date`를 항상 해당 월의 말일로
  고정한다는 점이다 (mtd는 부분월 기준일을 그대로 씀) —
  `shared/sections/monthly/monthly-section-1-kpi-goals.md` 참고.
- `executive-mtd` (naver 브랜드, 임원용 MTD) → `mcp__laighthouse__get_target_progress_v2`
  (mtd와 완전히 동일한 v2 도구/파라미터)에 `{ "brand_name": "...", "month": "YYYY-MM",
  "media": "naver", "as_of_date": "target_date" }` 1회 — mtd와 마찬가지로 부분월 기준일을 그대로 쓴다
  (monthly처럼 월말로 고정하지 않는다) —
  `shared/sections/executive-mtd/executive-mtd-section-1-achievement.md` 참고
  (executive-mtd에는 별도 월 목표 카드가 없다).
- ⚠️ ROAS 관련 수치(`target_roas`/`actual_roas`, v1의 `monthly_roas.target_full_month` 등)는
  비율값(예: 0.87, 5.06)으로 반환되므로 반드시 × 100 후 표시한다 (0.87 → 87%, 5.06 → 506%).

## 2. 섹션별 데이터 도구 (실행 순서 3단계)

나머지 `mcp__laighthouse__*` 도구를 호출해 각 섹션 수치 데이터를 가져온다 (각 섹션 데이터
스펙 파일에 명시된 정확한 tool명 참고). 두 종류가 있다:

- **generic 도구** (`get_ad_performance_daily_table` / `get_ad_performance_monthly_table` /
  `get_sales_performance_daily` / `get_sku_sales_daily` 등) — 여러 매체(google/meta/tiktok/naver)를
  `media` 파라미터로 다루며, naver는 채널(BRS/PLINK/NVSHOP/GFA) 구분 없이 하나로 통합된다.
  ⚠️ 이 계열 도구의 `group_by`는 **문자열 enum**(`total`/`media`/`campaign`/`ad-set`/`ad`)이다 —
  `true`/`false` boolean으로 절대 보내지 않는다. 각 섹션 파일에 적힌 값(대부분 `"total"`)을
  문자열 그대로 그 섹션에서만 쓴다.
  ⚠️ **모든 `group_by`류 enum 파라미터는 각 섹션 파일에 적힌 문자열 그대로 보낸다 — 절대 숫자/
  불린으로 "해석"하지 않는다.** `ad-set` 같은 값 안의 숫자·서수는 그냥 문자열의 일부일 뿐이며
  계산/변환 대상이 아니다. `get_naver_item_sales_daily`는 `"category-3rd"`를 서수로 오해해
  `-3`(정수)으로 보낸 오류가 토크나이저 레벨에서 반복 재현되어(언더스코어로 바꿔도 재발),
  **`group_by` 파라미터 자체를 도구에서 제거**했다 — 항상 `category_3rd` 기준으로 반환하므로
  호출 시 `group_by` 키를 넣지 않는다 (`shared/sections/mtd/mtd-section-6-daily-category-chart.md` 참고).
  ⚠️ **`get_ad_performance_monthly_table`은 mtd 분기 A에서 쓰지 않는다** (분기 B(type-b,
  render-report 전용)는 naver 전용 도구가 아예 적용되지 않으므로 이 도구를 그대로 쓴다)
  (2026-07-10 확인 — 값은 나오지만 실제 수치가 report-backend와 안 맞았다). 이 도구는
  report-backend가 실제로 호출하는 API가 아닌 별개의 범용 파이프라인(`_query_nv_monthly`)을 탄다.
  mtd-section-4(월별 광고 성과)는 `get_naver_channel_progression`을 월별로 반복 호출하는 전용 도구
  `get_naver_monthly_ad_performance`를 쓴다 (아래 naver 전용 도구 목록 참고) — 이게 report-backend
  `default/_prism_data.py::_build_13m_channel_frames`와 동일한 API 호출 패턴이다.
  ⚠️ **`get_ad_performance_daily_table`도 mtd 분기 A에서 쓰지 않는다** (분기 B(type-b)는 그대로
  쓴다) (2026-07-11 확인 — `group_by` 파라미터가 서버에 `null`로 도착하는 호출 오류가 있었다).
  mtd-section-14(일별 광고기여 매출 분석)는 전용 도구 `get_naver_daily_attributed_sales`를 쓴다 —
  `media=naver`/`group_by=total`을 서버 사이드에 고정해 그 파라미터 자체를 노출하지 않는다
  (SA+GFA 재계산은 하지 않는다 — report-backend가 그 재계산으로 없애는 오차는 하루 최대 2원
  수준이라 이 보고서 규모에선 무의미해서 뺐다).
- **naver 전용 도구** (`get_naver_sa_performance_daily` / `get_naver_item_sales_daily` /
  `get_naver_channel_progression` / `get_target_progress_v2`(이 하나만 `tools_general.py`) /
  `get_naver_monthly_ad_performance` / `get_naver_daily_attributed_sales` /
  `get_naver_category_sales`, `laighthouse-prism/src/mcp_server/tools_naver.py`) —
  mtd/monthly/executive-mtd 보고서에서만 쓴다. naver 채널 구분, 카테고리별 매출/할인율/환불율,
  채널별 예산 목표, naver 전용 target/achievement(2단계에서 이미 호출), naver 전용 월별
  광고비/매출/ROAS(mtd-section-4), naver 전용 일별 광고기여 매출(mtd-section-14)처럼 generic
  도구로는 깔끔하게/정확하게 낼 수 없는 데이터를 제공한다.
- **monthly 전용 가공** — mtd에는 없는 두 신규 섹션(카테고리별 월간 매출액 비교/매체별 성과
  비교)은 위 naver 전용 도구를 이번 달·전월 두 번씩 호출해 스킬이 직접 상위 N/증감률/채널
  합산을 가공한다 — 가공 규칙은 각 섹션 데이터 스펙
  (`shared/sections/monthly/monthly-section-6-category-monthly-comparison.md`,
  `monthly-section-8-media-comparison-table.md`)에 명시되어 있다.
- **executive-mtd 전용 가공** — mtd에는 없는 두 신규 섹션(주요 카테고리별 월간 매출액 증감/매체별
  성과 비교)도 naver 전용 도구를 이번 달(MTD)·전월 동일 기간(day-of-month 매칭) 두 번씩 호출해
  스킬이 직접 MoM 변동률/채널별 ROAS 변동을 가공한다 — monthly와 달리 "전월 전체"가 아니라
  "전월의 동일 기간"으로 잘라 비교해야 공정한 MTD 비교가 된다. 가공 규칙은 각 섹션 데이터 스펙
  (`shared/sections/executive-mtd/executive-mtd-section-4-category-mom-highlights.md`,
  `executive-mtd-section-5-media-roas-comparison.md`)에 명시되어 있다.

## 3. Executive Summary / ANALYSIS 텍스트 (실행 순서 4단계)

Executive Summary는 daily/mtd/monthly/executive-mtd 모두 항상 포함된다.

- ⚠️ **`df_dify` MCP 서버는 현재 호출하지 않는다** (연결 불안정으로 타임아웃 시 빈 응답이 돌아옴).
  `mcp__df_dify__*` 도구를 호출하지 말고, 이미 수집한 수치 데이터를 근거로 AI가 분석 텍스트를
  직접 작성한다 (단, 근거 수치 자체가 데이터 갭이면 생성하지 않음).
- **`mtd`인 경우**, `performance_overview`, `analysis_of_ad_performance`, `analysis_by_ad_group`
  3개 텍스트도 동일하게 AI가 각 섹션(mtd-section-5/8/11) 수치 기반으로 직접 작성한다.
- **`monthly`인 경우**, `analysis_of_category_performance` 텍스트를 동일하게 AI가 각 섹션
  (monthly-section-5/6/7) 수치 기반으로 직접 작성한다 — mtd보다 하이레벨/회고 톤을 쓴다
  (`shared/sections/monthly/monthly-section-3-executive-summary.md`, `monthly-section-5-*.md` 참고).
- **`executive-mtd`인 경우**, `executive_summary` 텍스트를 AI가 각 섹션(executive-mtd-section-
  1/2/4/5) 수치 기반으로 직접 작성한다 — mtd보다 짧게(3~5문장), "무엇이 움직였는지 + 왜
  신경 써야 하는지"의 임원 관점으로 쓰고, 특이사항이 없는 항목은 억지로 채우지 않는다
  (`shared/sections/executive-mtd/executive-mtd-section-3-executive-summary.md` 참고).
