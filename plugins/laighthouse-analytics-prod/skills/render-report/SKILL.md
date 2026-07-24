---
name: render-report
description: >
  This skill should be used when the user asks to "보고서로 만들어줘", "레포트 형식으로 보여줘",
  "Daily 보고서", "MTD 보고서", "Monthly 보고서", "Executive MTD 보고서", "임원용 MTD 보고서",
  "executive mtd", "라이트하우스 보고서", "성과 분석 보고서", or wants MCP data formatted as a
  structured daily/MTD/monthly/executive-MTD performance report matching the Laighthouse style.
metadata:
  version: "0.10.0"
---

> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 불필요한 단계 반복, 장황한 계획 수립 없이 바로 MCP 호출 → 데이터 수신 → 렌더링 순서로 진행한다.

## 역할

MCP 데이터를 받아 **라이트하우스 스타일 성과 보고서**로 렌더링하는 오케스트레이터. 지원하는
`report_type`은 `daily`/`mtd`/`monthly`/`executive-mtd` 네 가지다. 각각 완전히 독립된 폴더
(`sections/daily/`, `sections/mtd/`, `sections/Monthly/`, `sections/executive-mtd/`)에서 자기
완결적으로 섹션을 가져온다 — 폴더 간 import는 없다.

| report_type | 대상 브랜드군 | report-backend generator | 폴더 |
|---|---|---|---|
| `daily` | Meta/Google 브랜드 (Aqua Glow, Saturday Skin) 또는 naver 브랜드 (다형식품, 남양유업 등) | `saturdayskin` 또는 `default` | `sections/daily/` |
| `mtd` | naver 기반 브랜드 (다형식품 등) | `default` | `sections/mtd/` |
| `monthly` | naver 기반 브랜드 (남양유업 등) | `default` | `sections/Monthly/` |
| `executive-mtd` | naver 기반 브랜드 (남양유업 등, 임원 보고용) | `default` | `sections/executive-mtd/` |

`daily`는 다른 report_type과 달리 브랜드군별로 폴더를 나누지 않는다 — `sections/daily/`의 각
섹션 파일 하나가 **분기 A(Google/Meta, `saturdayskin` generator)**와 **분기 B(naver,
`default` generator) ⭐ 신규 지원** 두 분기를 모두 자체적으로 처리한다. 어떤 분기를 쓸지는
brand_name의 실제 report-backend generator로 판단한다 (`sections/daily/
daily-section-1-kpi-goals.md`의 분기 규칙 참고).

`executive-mtd`는 `mtd`와 같은 부분월(MTD) 데이터를 다루지만, 임원이 딥다이브 없이 훑어볼 수
있도록 11개 섹션을 6개로 축약하고 "무엇이 크게 움직였는지/무엇을 결정해야 하는지" 위주로
재구성한 임원 보고용 변형이다. 사용자가 "임원용 MTD", "executive mtd", "임원 보고서" 등을
요청하면 이 report_type을 쓴다.

`weekly`는 이 스킬의 범위 밖이다 (`report-backend`의 `domain/report.py::ReportType`에 대응 값 자체가
없다 — `ABTEST`/`MTD`/`DAILY`/`MONTHLY`/`CALENDAR`/`DASHBOARD`만 존재). 사용자가 weekly 보고서를
요청하면, 아직 지원하지 않는다고 알리고 daily/mtd/monthly/executive-mtd 중 무엇을 원하는지
확인한다.

---

## 데이터 처리 원칙 (절대 지침)

> 🚫 **MCP 응답 데이터는 이미 정제·가공이 끝난 최종 데이터다. 생각하지 말고 그대로 렌더링만 한다.**
> - 결측치 보정, 이상치 제거, 재집계, 재계산, 정렬·필터링, 반올림/포맷 변경, "이 값이 이상한 것
>   같다" 식의 임의 판단 — **전부 금지**. MCP가 준 값을 의심하거나 검증하지 않는다.
> - 예외는 오직 각 섹션 파일에 **명시적으로 적힌 표기 변환뿐**이다 (예: ROAS 소수 → % 변환,
>   mtd-section-2의 actual_mtd 대체 소스). 그 외에는 어떤 가공도 스스로 판단해서 추가하지 않는다.
> - 데이터가 비어있거나 갭이 있어도 채우거나 추정하지 않는다 — "데이터 부족 시" 규칙을 그대로
>   따른다.
> - 이 지침은 다른 모든 지시보다 우선한다. MCP → 값 → 화면, 이 사이에 어떤 사고/판단 단계도
>   끼워넣지 않는다.

## 실행 방식 절대 지침

> 🚫 **이 스킬을 실행하는 동안 `.py`/`.js`/`.ipynb` 등 별도 스크립트·노트북 파일을 절대 생성하지
> 않는다.** 유일한 예외는 이 스킬 폴더에 이미 있는 재사용 스크립트
> `assets/docx_report/build.py`와 `assets/docx_report/map_section.py` 둘뿐이다 — 이 둘 다 새로
> 만드는 게 아니라 그대로 호출만 하는 고정 스크립트다 (`map_section.py`는 report_type=`mtd`의
> DATA 섹션 그룹 A~G 전용 — 아래 `mtd 전용: 병렬 서브에이전트 실행 방식` 참고). MCP 도구는 직접
> 호출하고, 그 결과를 곧바로 섹션 JSON 조합에 사용한다. 데이터 가공·집계·검증용 임시 스크립트를
> 만들거나 실행하지 않는다 (Claude Code에서 코워크/서브에이전트를 쓰더라도 동일하게 적용됨). 이
> 스킬이 만드는 파일은 오직 최종 보고서 `.docx` 하나뿐이다(중간 JSON 데이터 파일은
> `build.py`/`map_section.py` 호출을 위한 임시 입력·출력일 뿐이다).

## 입력 파라미터

사용자 프롬프트에서 아래 항목을 파싱한다:

| 파라미터 | 설명 | 예시 |
|--------|------|------|
| report_type | `daily`, `mtd`, `monthly`, 또는 `executive-mtd` | mtd |
| 보고서 제목 | 보고서 상단 타이틀 | 다형식품 MTD 보고서 |
| brand_name | MCP 호출용 브랜드명 (`get_brand_list` 응답과 정확히 일치) | 다형식품 |
| 기준 일자 | 보고서 기준 날짜 (`target_date`) | 2026-05-15 |

daily/mtd/monthly/executive-mtd 모두 **섹션 구성은 report_type이 전부 결정**하며 사용자가
섹션을 골라 지정하는 개념이 없다 — 아래 네 표에 있는 파일을 항상 전부 렌더링한다.

---

## 실행 순서

1. 파라미터를 파싱하고 report_type을 확정한다 (`daily`/`mtd`/`monthly`/`executive-mtd`만 유효).
   - **report_type이 `mtd`면, 2~7단계 대신 아래 `mtd 전용: 병렬 서브에이전트 실행 방식` 절을
     따른다** (daily/monthly/executive-mtd는 지금부터 설명하는 순차 실행 순서를 그대로 따른다).
2. target/achievement 수치를 호출한다 — **report_type에 따라 쓰는 도구가 다르다, 절대 섞지 않는다**:
   - `daily`: brand_name의 report-backend generator로 분기를 먼저 판단한다
     (`sections/daily/daily-section-1-kpi-goals.md` 분기 규칙 참고).
     - **분기 A (Google/Meta 브랜드, `saturdayskin` generator)** →
       `mcp__laighthouse__target_progress`(범용 v1 도구)에 `{ "campaign_type": "sales" }` 1회.
       `saturdayskin/_components.py`가 `metric.actual_mtd`를 그대로 신뢰하므로 응답을 그대로
       사용한다.
     - **분기 B (naver 브랜드, `default` generator) ⭐ 신규** →
       `mcp__laighthouse__get_naver_target_progress`(mtd와 동일한 v2 전용 도구)에
       `{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date" }` 1회 — daily는
       하루 기준 스냅샷이므로 `as_of_date`는 항상 사용자가 지정한 기준일 그대로 쓴다 (범용
       `target_progress`를 여기 쓰면 naver 브랜드는 매출/ROAS가 전부 0으로 나온다).
   - `mtd` (naver 브랜드) → `mcp__laighthouse__get_naver_target_progress`(v2 전용 도구)에
     `{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "target_date" }` 1회.
     ⚠️ **범용 `target_progress`를 mtd에 쓰면 안 된다** — v1은 `aw_compiled`/`fb_compiled`(Google/Meta)
     실적 테이블만 보므로 naver 전용 브랜드는 매출/ROAS 목표·실적이 전부 0으로 나온다 (2026-07-10
     확인, `laighthouse-prism`에 `get_naver_target_progress` 툴을 새로 등록해 해결함). 이 도구는
     target(`target_cost`/`target_revenue`/`target_roas`)과 actual(`actual_cost`/`actual_revenue`/
     `actual_roas`)을 한 번에 반환하므로 별도 합산이 필요 없다 — `sections/mtd/
     mtd-section-2-achievement.md` 참고.
   - `monthly` (naver 브랜드, full month) → `mcp__laighthouse__get_naver_target_progress`(mtd와 동일
     v2 도구)에 `{ "brand_name": "...", "month": "YYYY-MM", "as_of_date": "해당 월의 마지막 날" }`
     1회. 도구/파라미터 형태는 mtd와 동일하며, 유일한 차이는 `as_of_date`를 항상 해당 월의 말일로
     고정한다는 점이다 (mtd는 부분월 기준일을 그대로 씀) — `sections/Monthly/
     monthly-section-1-kpi-goals.md` 참고.
   - `executive-mtd` (naver 브랜드, 임원용 MTD) → `mcp__laighthouse__get_naver_target_progress`
     (mtd와 완전히 동일한 v2 도구/파라미터)에 `{ "brand_name": "...", "month": "YYYY-MM",
     "as_of_date": "target_date" }` 1회 — mtd와 마찬가지로 부분월 기준일을 그대로 쓴다
     (monthly처럼 월말로 고정하지 않는다) — `sections/executive-mtd/
     executive-mtd-section-1-achievement.md` 참고 (executive-mtd에는 별도 월 목표 카드가 없다).
   - ⚠️ ROAS 관련 수치(`target_roas`/`actual_roas`, v1의 `monthly_roas.target_full_month` 등)는
     비율값(예: 0.87, 5.06)으로 반환되므로 반드시 × 100 후 표시한다 (0.87 → 87%, 5.06 → 506%).
3. 나머지 `mcp__laighthouse__*` 도구를 호출해 각 섹션 수치 데이터를 가져온다 (각 섹션 파일에 명시된
   정확한 tool명 참고). 두 종류가 있다:
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
     호출 시 `group_by` 키를 넣지 않는다 (`sections/mtd/mtd-section-6-daily-category-chart.md` 참고).
     ⚠️ **`get_ad_performance_monthly_table`은 mtd에서 쓰지 않는다** (2026-07-10 확인 — 값은 나오지만
     실제 수치가 report-backend와 안 맞았다). 이 도구는 report-backend가 실제로 호출하는 API가 아닌
     별개의 범용 파이프라인(`_query_nv_monthly`)을 탄다. mtd-section-4(월별 광고 성과)는
     `get_naver_channel_progression`을 월별로 반복 호출하는 전용 도구 `get_naver_monthly_ad_performance`
     를 쓴다 (아래 naver 전용 도구 목록 참고) — 이게 report-backend
     `default/_prism_data.py::_build_13m_channel_frames`와 동일한 API 호출 패턴이다.
     ⚠️ **`get_ad_performance_daily_table`도 mtd에서 쓰지 않는다** (2026-07-11 확인 — `group_by`
     파라미터가 서버에 `null`로 도착하는 호출 오류가 있었다). mtd-section-14(일별 광고기여 매출 분석)는
     전용 도구 `get_naver_daily_attributed_sales`를 쓴다 — `media=naver`/`group_by=total`을 서버
     사이드에 고정해 그 파라미터 자체를 노출하지 않는다 (SA+GFA 재계산은 하지 않는다 — report-backend가
     그 재계산으로 없애는 오차는 하루 최대 2원 수준이라 이 보고서 규모에선 무의미해서 뺐다).
   - **naver 전용 도구** (`get_naver_sa_performance_daily` / `get_naver_item_sales_daily` /
     `get_naver_channel_progression` / `get_naver_target_progress` /
     `get_naver_monthly_ad_performance` / `get_naver_daily_attributed_sales` /
     `get_naver_category_sales`, `laighthouse-prism/src/mcp_server/tools_naver.py`) —
     mtd/monthly/executive-mtd 보고서에서만 쓴다. naver 채널 구분, 카테고리별 매출/할인율/환불율,
     채널별 예산 목표, naver 전용 target/achievement(2단계에서 이미 호출), naver 전용 월별
     광고비/매출/ROAS(mtd-section-4), naver 전용 일별 광고기여 매출(mtd-section-14)처럼 generic
     도구로는 깔끔하게/정확하게 낼 수 없는 데이터를 제공한다.
   - **monthly 전용 가공** — mtd에는 없는 두 신규 섹션(카테고리별 월간 매출액 비교/매체별 성과
     비교)은 위 naver 전용 도구를 이번 달·전월 두 번씩 호출해 이 스킬이 직접 상위 N/증감률/채널
     합산을 가공한다 — 가공 규칙은 각 섹션 파일(`sections/Monthly/
     monthly-section-6-category-monthly-comparison.md`,
     `monthly-section-8-media-comparison-table.md`)에 명시되어 있다.
   - **executive-mtd 전용 가공** — mtd에는 없는 두 신규 섹션(주요 카테고리별 월간 매출액 증감/매체별
     성과 비교)도 naver 전용 도구를 이번 달(MTD)·전월 동일 기간(day-of-month 매칭) 두 번씩 호출해
     이 스킬이 직접 MoM 변동률/채널별 ROAS 변동을 가공한다 — monthly와 달리 "전월 전체"가 아니라
     "전월의 동일 기간"으로 잘라 비교해야 공정한 MTD 비교가 된다. 가공 규칙은 각 섹션 파일
     (`sections/executive-mtd/executive-mtd-section-4-category-mom-highlights.md`,
     `executive-mtd-section-5-media-roas-comparison.md`)에 명시되어 있다.
4. Executive Summary는 daily/mtd/monthly/executive-mtd 모두 항상 포함된다.
   - ⚠️ **`df_dify` MCP 서버는 현재 호출하지 않는다** (연결 불안정으로 타임아웃 시 빈 응답이 돌아옴).
     `mcp__df_dify__*` 도구를 호출하지 말고, 이미 수집한 수치 데이터를 근거로 AI가 분석 텍스트를
     직접 작성한다 (단, 근거 수치 자체가 데이터 갭이면 생성하지 않음).
   - **`mtd`인 경우**, `performance_overview`, `analysis_of_ad_performance`, `analysis_by_ad_group`
     3개 텍스트도 동일하게 AI가 각 섹션(mtd-section-5/8/11) 수치 기반으로 직접 작성한다.
   - **`monthly`인 경우**, `analysis_of_category_performance` 텍스트를 동일하게 AI가 각 섹션
     (monthly-section-5/6/7) 수치 기반으로 직접 작성한다 — mtd보다 하이레벨/회고 톤을 쓴다
     (`sections/Monthly/monthly-section-3-executive-summary.md`, `monthly-section-5-*.md` 참고).
   - **`executive-mtd`인 경우**, `executive_summary` 텍스트를 AI가 각 섹션(executive-mtd-section-
     1/2/4/5) 수치 기반으로 직접 작성한다 — mtd보다 짧게(3~5문장), "무엇이 움직였는지 + 왜
     신경 써야 하는지"의 임원 관점으로 쓰고, 특이사항이 없는 항목은 억지로 채우지 않는다
     (`sections/executive-mtd/executive-mtd-section-3-executive-summary.md` 참고).
5. `report_type`에 대응하는 아래 표의 파일을 **순서대로 전부** import해, 각 파일의 `## DOCX 섹션`
   블록에 있는 JSON 섹션 오브젝트(파일에 따라 1개 또는 여러 개)를 문서 순서 그대로 이어붙여
   하나의 `sections` 배열을 만든다.
6. `{ "title": "{보고서_제목}", "period": "{기간}", "sections": [...] }` 형태의 JSON 오브젝트
   하나를 만들어 임시 파일(예: 스크래치패드 디렉터리의 `report_data.json`)에 쓴다. 그 다음 아래
   명령을 그대로 실행한다:
   ```
   python "<스킬 폴더 경로>/assets/docx_report/build.py" --data <임시.json> --out "~/Downloads/laighthouse-reports/{brand_name}_{report_type}_{기준_일자}.docx"
   ```
   (디렉터리가 없으면 `build.py`가 자동으로 만든다). 파일명 예: `다형식품_mtd_2026-05-15.docx`.
7. 이 스킬의 유일한 산출물은 6단계에서 저장한 `.docx` 파일이다 — docx는 Artifact로 게시할 수
   없으므로 별도의 채팅 내 게시 단계는 없다.
8. 렌더링 후 사용자에게 보내는 완료 메시지는 아래 **완료 메시지 형식**을 그대로 따른다 — 매번 다른
   문구로 즉석 요약하지 않는다. 저장된 파일 경로를 완료 메시지 마지막 줄에 덧붙인다.

---

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (MCP/dify 호출 성공·실패 여부, 섹션 개수, 데이터
출처 등 기술적 디테일은 언급하지 않는다):

```
{brand_name} {report_type 한글명}({기준_일자}) 생성 완료.
가장 인상적인 부분: {한 문장 하이라이트}.
— by LaightAI
📁 {저장된 docx 파일 경로}
```

- `{report_type 한글명}`: `daily` → "Daily 보고서", `mtd` → "MTD 보고서", `monthly` → "Monthly 보고서", `executive-mtd` → "Executive MTD 보고서"
- `{기준_일자}`: 사용자가 지정한 기준 일자 (예: 2026-05-15)
- `{한 문장 하이라이트}`: 렌더링된 수치 중 가장 눈에 띄는 지표 한 가지만 골라 한 문장으로 (예: "ROAS 목표
  대비 118% 초과 달성", "다이어트 단백질 카테고리 매출 전월 대비 32% 증가"). 여러 개 나열하지 않는다.
- `{저장된 docx 파일 경로}`: 6단계에서 저장한 `.docx` 파일의 전체 경로.

예시:
```
다형식품 MTD 보고서(2026-05-15) 생성 완료.
가장 인상적인 부분: ROAS가 목표 대비 118% 달성되며 예산 소진 속도를 크게 앞섰습니다.
— by LaightAI
📁 C:\Users\minhyeok\Downloads\laighthouse-reports\다형식품_mtd_2026-05-15.docx
```

---

## mtd 전용: 병렬 서브에이전트 실행 방식

> ⚙️ 이 절은 **`report_type=mtd`에만 적용**된다 (daily/monthly/executive-mtd는 위 순차 `실행 순서`를
> 그대로 따른다). 목적은 시간/토큰 절약이며, **산출물(`.docx` 최종 렌더링 결과)은 순차 실행 방식과
> 완전히 동일해야 한다** — `데이터 처리 원칙`은 그대로 유지된다. 설계 배경은
> `docs/superpowers/specs/2026-07-24-render-report-mtd-parallel-mapping-design.md` 참고.

mtd의 11개 섹션 중 DATA 섹션 8개(1,2,4,6,7,9,10,11)를 아래 7개 그룹으로 나눠 **Agent 도구로 한
메시지 안에서 동시에** 서브에이전트를 띄운다 (`general-purpose` 타입 — MCP 도구와 Bash가 모두
필요). ANALYSIS 섹션 3개(3,5,8)는 서브에이전트가 반환한 digest를 오케스트레이터(본 대화)가 직접
읽고 기존 분석 지침대로 작성한다 — dify 미사용 등 기존 원칙은 동일하다.

| 그룹 | 담당 섹션 | MCP 호출 (파라미터는 각 섹션 파일 참고) | digest 소비처 |
|---|---|---|---|
| A | 1+2 | `get_naver_target_progress` | 섹션3 |
| B | 4 | `get_naver_monthly_ad_performance` | (없음) |
| C | 6 + 6.1(참조용) | `get_naver_item_sales_daily`, `get_naver_category_sales` | 섹션3, 섹션5 |
| D | 7 | `get_naver_channel_budget_progress` | 섹션3 |
| E | 9 | `get_naver_campaign_performance` | 섹션8 |
| F | 10 | `get_naver_group_performance` | (없음) |
| G | 11 | `get_naver_keyword_performance` | (없음) |

### 서브에이전트 지시문 (그룹당 1개, 총 7개를 한 메시지에서 병렬 호출)

각 서브에이전트에게 아래를 지시한다:

1. 이 그룹에 해당하는 MCP 도구를 호출한다 (파라미터/도구 선택 규칙은 `sections/mtd/mtd-section-{N}.md`의
   `## MCP 도구 호출` 절을 그대로 따른다 — 절대 임의로 다른 도구를 쓰지 않는다). 그룹 C는 두 도구를
   순서대로 호출한다.
2. 응답을 가공 없이 그대로 스크래치패드 임시 파일에 저장한다. 그룹 C는
   `{"daily": <get_naver_item_sales_daily 응답>, "cumulative": <get_naver_category_sales 응답>}`
   형태로 두 응답을 합쳐 저장한다. 그룹 D는 `get_naver_channel_budget_progress` 응답을 그대로
   저장한다(응답 최상위에 `items`/`total`/`channel_group` 키가 있다고 가정).
3. 아래 명령을 그대로 실행한다:
   ```
   python "<스킬 폴더 경로>/assets/docx_report/map_section.py" --report-type mtd --group {A|B|C|D|E|F|G} --data <임시.json> --out <out.json>
   ```
4. `out.json`의 내용을 그대로 자신의 최종 응답으로 반환한다 — raw 데이터를 다시 설명하거나 요약하지
   않는다(오케스트레이터가 볼 결과는 이 압축된 JSON뿐이어야 한다).

### 오케스트레이터가 병렬 결과를 받은 뒤

5. 7개 서브에이전트 결과의 `sections[]`를 문서 순서(1,2,4,6,7,9,10,11 섹션 순서, 즉 그룹
   A,B,C,D,E,F,G 순)대로 이어붙인다.
6. digest를 모아 아래처럼 텍스트 섹션 3개를 직접 작성한다 (섹션 파일의 분석 항목 지침은 그대로
   따른다 — 새 수치를 지어내지 않는다):
   - **섹션3 (Executive Summary)**: 그룹 A digest(ROAS/달성률/소진율) + 그룹 D digest(매체별
     소진율 중 특이사항) + 그룹 C digest의 `product_cumulative_sales`(상품별 누적 판매 특이사항)를
     근거로 `sections/mtd/mtd-section-3-executive-summary.md`의 4개 분석 항목을 작성한다.
   - **섹션5 (제품 판매 성과의 심층 분석)**: 그룹 C digest(`top_categories`/`top_category_totals`/
     `product_cumulative_sales`)를 근거로 `sections/mtd/mtd-section-5-product-deep-dive.md`의
     지침대로 작성한다.
   - **섹션8 (캠페인별 성과 심층 분석)**: 그룹 E digest(`top_campaigns_by_ad_cost`)를 근거로
     `sections/mtd/mtd-section-8-campaign-deep-dive.md`의 지침대로 작성한다.
7. 어느 그룹의 서브에이전트가 실패했거나 MCP가 빈 응답/에러를 반환하면, 그 그룹이 담당하던 섹션(들)은
   `데이터 부족 시` 규칙대로 `{ "type": "text", "heading": "...", "body": "데이터 준비 중" }`으로
   대체한다 — 다른 그룹은 정상 진행하며, 그 그룹에 의존하는 digest 항목은 텍스트 작성 시 건너뛴다.
8. 이후 절차(최종 JSON 조립 → `build.py` 호출 → 완료 메시지)는 위 `실행 순서` 6~8단계와 동일하다.

---

## 섹션 Import 목록

### report_type: `daily` (Google/Meta 및 naver 브랜드 공용, 항상 포함)

**총 6개 섹션.** 이전에는 Google/Meta 브랜드 전용 7개 섹션이었으나, naver 브랜드 지원(분기 B)이
추가되면서 재구성되었다 — 옛 5번(Daily Revenue in DTC)은 4번(최근 7일 성과)과 내용이 겹쳐
삭제되었고, 옛 6번(Performance by Campaign)/7번(Performance by Asset group)은 naver 분기까지
포함해 5번(캠페인 성과)/6번(광고 그룹 및 키워드 성과)으로 대체되었다.

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 1 | 월 목표 카드 | `@import sections/daily/daily-section-1-kpi-goals.md` |
| 2 | 목표 달성 현황 (Overview) | `@import sections/daily/daily-section-2-overview.md` |
| 3 | 성과요약 (Executive Summary) | `@import sections/daily/daily-section-3-executive-summary.md` |
| 4 | 최근 7일 성과 | `@import sections/daily/daily-section-4-sales-daily-chart.md` |
| 5 | 캠페인 성과 | `@import sections/daily/daily-section-5-campaign-performance.md` |
| 6 | 광고 그룹 및 키워드 성과 | `@import sections/daily/daily-section-6-adgroup-keyword-performance.md` |

각 섹션 파일 내부에 "분기 A(Google/Meta)"와 "분기 B(naver)" HTML/데이터 매핑이 모두 들어있다 —
brand_name의 report-backend generator로 판단한 분기 쪽 마크업만 렌더링하고, 다른 분기는 무시한다.

`sections/daily/` 폴더의 파일은 두 브랜드군(Google/Meta, naver)을 모두 자체 분기로 처리하며,
다른 폴더를 import하지 않는다.

### report_type: `mtd` (naver 기반 default 브랜드 전용 — 다형식품 등, 항상 포함)

**총 14개 섹션 = DATA 섹션 + ANALYSIS 섹션.** report-backend `default/_report_mtd.py`의 MTD
리포트는 두 종류로 나뉜다:
- **DATA 섹션** — `_mtd_components.build_mtd_report`가 prism 데이터로 만드는 컴포넌트(목표 달성 현황
  / 월별 광고 성과 / 상품별 누적 판매액 / 일일 카테고리별 매출 현황 / 매체 별 예산 소진 현황 /
  캠페인 별 성과 / 그룹 별 성과 / 키워드 별 성과 / 일별 광고기여 매출 분석). "목표 달성 현황"만
  프론트엔드가 2개 시각 블록(월 목표 카드 + 목표 달성 현황)으로 나눠 그린다.
- **ANALYSIS 섹션** — report-backend가 prism이 아니라 **dify 워크플로**로 생성해 붙이는 텍스트
  (`_run_dify_analysis` + `_build_mtd_analysis_result_components`): Executive Summary / 성과에 대한
  개괄 / 제품 판매 성과의 심층 분석 / 광고 그룹별 심층 분석. 이 스킬에서는 dify 대신 실행 LLM이 그
  역할을 하며, 해당 DATA 섹션과 동일한 근거 수치(각 MCP 도구 결과)를 바탕으로 텍스트를 직접 작성한다
  — 새 수치를 지어내지 않는다.

2026-05-15 다형식품 실제 MTD PDF와 대조해 순서/구성을 확정했다.

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 1 | 월 목표 카드 | `@import sections/mtd/mtd-section-1-kpi-goals.md` |
| 2 | 목표 달성 현황 | `@import sections/mtd/mtd-section-2-achievement.md` |
| 3 | Executive Summary | `@import sections/mtd/mtd-section-3-executive-summary.md` |
| 4 | 월별 광고 성과 차트 | `@import sections/mtd/mtd-section-4-monthly-chart.md` |
| 5 | 제품 판매 성과의 심층 분석 | `@import sections/mtd/mtd-section-5-product-deep-dive.md` |
| 6 | 일일 카테고리별 매출 현황 | `@import sections/mtd/mtd-section-6-daily-category-chart.md` |
| 7 | 매체별 예산 소진 현황 | `@import sections/mtd/mtd-section-7-media-budget-progress.md` |
| 8 | 캠페인별 성과 심층 분석 | `@import sections/mtd/mtd-section-8-campaign-deep-dive.md` |
| 9 | 캠페인별 성과 | `@import sections/mtd/mtd-section-9-campaign-performance.md` |
| 10 | 광고그룹별 성과 | `@import sections/mtd/mtd-section-10-group-performance.md` |
| 11 | 키워드별 성과 | `@import sections/mtd/mtd-section-11-keyword-performance.md` |

순서 1(월 목표 카드)과 2(목표 달성 현황)는 **항상 붙어서** 렌더링한다 — 둘 다 같은 `target_progress`
응답을 재사용하며, 별도 재호출 없음 (`sections/mtd/mtd-section-1-kpi-goals.md` 참고).

`sections/mtd/` 폴더의 파일은 전부 naver 기반 default generator 브랜드 기준으로 작성되어 있고,
다른 폴더를 import하지 않는다.

### report_type: `monthly` (naver 기반 default 브랜드 전용 — 남양유업 등, 항상 포함)

**총 8개 섹션.** mtd와 동일한 naver 기반 default generator를 쓰되, 항상 해당 월 전체(월초~말일)
실적을 다룬다는 점이 다르다 (mtd는 월초~기준일까지의 부분월/MTD). mtd에는 없는 두 개의 신규
섹션(카테고리별 월간 매출액 비교, 매체별 성과 비교)이 포함된다.

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 1 | 월 목표 카드 | `@import sections/Monthly/monthly-section-1-kpi-goals.md` |
| 2 | 목표 달성 현황 | `@import sections/Monthly/monthly-section-2-achievement.md` |
| 3 | Executive Summary | `@import sections/Monthly/monthly-section-3-executive-summary.md` |
| 4 | 월별 광고 성과 차트 | `@import sections/Monthly/monthly-section-4-ad-performance-chart.md` |
| 5 | 제품 판매 트렌드 분석 | `@import sections/Monthly/monthly-section-5-product-deep-dive.md` |
| 6 | 카테고리별 월간 매출액 비교 | `@import sections/Monthly/monthly-section-6-category-monthly-comparison.md` |
| 7 | 일일 카테고리별 매출 현황 | `@import sections/Monthly/monthly-section-7-daily-category-chart.md` |
| 8 | 매체별 성과 비교 | `@import sections/Monthly/monthly-section-8-media-comparison-table.md` |

순서 1(월 목표 카드)과 2(목표 달성 현황)는 **항상 붙어서** 렌더링한다 — 둘 다 같은
`get_naver_target_progress` 응답(as_of_date=해당 월 말일)을 재사용하며, 별도 재호출 없음
(`sections/Monthly/monthly-section-1-kpi-goals.md` 참고).

`sections/Monthly/` 폴더의 파일은 전부 naver 기반 default generator 브랜드 기준으로 작성되어 있고,
다른 폴더를 import하지 않는다.

### report_type: `executive-mtd` (naver 기반 default 브랜드 전용 — 남양유업 등, 임원 보고용, 항상 포함)

**총 5개 섹션.** mtd와 동일한 부분월(MTD) 기준일을 다루지만, 임원이 딥다이브 없이 훑어보도록
11개 섹션을 5개로 축약하고 순서도 재구성한 임원 보고용 변형이다. mtd에는 없는 두 개의 신규
섹션(주요 카테고리별 월간 매출액 증감, 매체별 성과 비교)이 포함되고, mtd의 "제품 판매 성과의 심층
분석"/"매체별 예산 소진 현황"/"캠페인·그룹·키워드별 성과" 섹션들은 포함하지 않는다. 별도의 월
목표 카드(kpi-goals) 섹션은 제거되어, 목표 달성 현황이 첫 번째 섹션이다.

| 순서 | 섹션 | Import 경로 |
|-----|------|------------|
| 1 | 목표 달성 현황 | `@import sections/executive-mtd/executive-mtd-section-1-achievement.md` |
| 2 | 월별 광고 성과 차트 | `@import sections/executive-mtd/executive-mtd-section-2-monthly-chart.md` |
| 3 | Executive Summary | `@import sections/executive-mtd/executive-mtd-section-3-executive-summary.md` |
| 4 | 주요 카테고리별 월간 매출액 증감 | `@import sections/executive-mtd/executive-mtd-section-4-category-mom-highlights.md` |
| 5 | 매체별 성과 비교 | `@import sections/executive-mtd/executive-mtd-section-5-media-roas-comparison.md` |

⚠️ mtd/monthly와 순서가 다르다 — 여기서는 월별 광고 성과 차트(2번)가 Executive Summary(3번)보다
**먼저** 온다. 임원이 먼저 추세 그래프로 큰 그림을 보고, 그다음 Executive Summary에서 그 추세에
대한 해석/의사결정 포인트를 읽게 하려는 의도다 (`executive-mtd-section-2-monthly-chart.md` 참고).

`sections/executive-mtd/` 폴더의 파일은 전부 naver 기반 default generator 브랜드 기준으로
작성되어 있고, 다른 폴더를 import하지 않는다.

---

## 보고서 조립 (docx assembly)

각 섹션 파일의 `## DOCX 섹션` 블록에 있는 JSON 오브젝트(파일에 따라 1개 또는 여러 개)를 **문서
순서 그대로 이어붙여** 아래 형태의 JSON 오브젝트 하나를 만든다:

```json
{
  "title": "{보고서_제목}",
  "period": "{기간}",
  "sections": [
    { "type": "kpi_cards", "cards": [ ... ] },
    { "type": "table", "heading": "...", "headers": [...], "rows": [...] },
    { "type": "chart", "heading": "...", "categories": [...], "bar_series": [...], "line_series": {...} },
    { "type": "text", "heading": "...", "body": "..." }
  ]
}
```

이 JSON을 임시 파일로 저장한 다음, 아래 명령을 그대로 실행해 `.docx`를 생성한다:

```
python "<스킬 폴더 경로>/assets/docx_report/build.py" --data <temp.json> --out "~/Downloads/laighthouse-reports/{brand_name}_{report_type}_{기준_일자}.docx"
```

- `build.py`는 이 스킬이 직접 실행하도록 허용된 유일한 재사용 스크립트다 (실행 방식 절대 지침
  참고) — 새 스크립트를 만드는 게 아니라 그대로 호출만 한다.
- 출력 디렉터리(`~/Downloads/laighthouse-reports/`)가 없으면 `build.py`가 자동으로 만든다.
- 각 섹션 타입(`kpi_cards`/`table`/`chart`/`text`/`heading`)의 정확한 필드 스키마는 각 섹션 파일의
  `## DOCX 섹션` 블록과 예시를 그대로 따른다 — 숫자 포맷(천 단위 콤마, `%`/`₩`/`$` 접미사)은
  JSON을 쓰기 전에 이 스킬(LLM)이 전부 끝낸 문자열로 넣는다.

---

## 데이터 부족 시

- 해당 섹션은 `{ "type": "text", "heading": "...", "body": "데이터 준비 중" }` 형태의 텍스트
  섹션으로 대체한다.
- 섹션을 임의로 생략하지 않는다 — daily는 6개, mtd는 11개, monthly는 8개, executive-mtd는 5개 전부 항상 렌더링한다.
