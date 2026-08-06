# 병렬 서브에이전트 실행 방식 (render-report-docx 전용 레퍼런스)

> 이 파일은 **Agent(서브에이전트) 도구가 있는 환경 전용** 실행 경로다. 기본 경로는
> SKILL.md의 「고속 실행 공통 규칙 (map_report.py)」이며, 그룹 표·MCP 파라미터·저장
> 형식·분석(digest) 지침은 두 경로가 공유한다. Agent 도구가 없거나 확신이 없으면 이
> 파일을 읽지 말고 공통 규칙을 따른다.
>
> 섹션 파일 경로는 데이터 스펙(`shared/sections/{type}/`, 플러그인 루트 기준) 기준으로
> 표기했다. 같은 파일명의 DOCX 출력 스펙은 스킬의 `sections/{type}/`에 있다
> (SKILL.md 「섹션 읽기 규칙」 참고).

## daily 전용: 병렬 서브에이전트 실행 방식

> ⚡ **기본 경로는 위 `고속 실행 공통 규칙(map_report.py)`이다.** 이 절의 서브에이전트 메커니즘은 Agent 도구가 있는 환경 전용 옵션이며, 그룹 표·MCP 파라미터·저장 형식·분석 지침은 두 경로가 공유한다.

> ⚙️ 이 절은 **`report_type=daily`에만 적용**된다 (mtd/monthly/executive-mtd는 각자의 절을 따른다).
> 목적은 시간/토큰 절약이며, **산출물(`.docx` 최종 렌더링 결과)은 순차 실행 방식과 완전히 동일해야
> 한다** — `데이터 처리 원칙`은 그대로 유지된다. daily는 다른 세 report_type과 달리 **분기(A:
> Google/Meta, B: naver)가 있는 유일한 report_type**이라 그룹 분리 외에 분기 판단이 하나 더
> 필요하다.

### 0단계: 분기를 먼저, 단 한 번만 판단한다

병렬 서브에이전트를 띄우기 **전에** brand_name의 report-backend generator로 분기(A/B)를 판단한다
(`shared/sections/daily/daily-section-1-kpi-goals.md`의 분기 규칙, `실행 순서` 2단계와 동일한 판단 기준).
이 판단은 **한 번만** 하고, 그 결과(A 또는 B)를 아래 4개 그룹 서브에이전트 전원에게 지시문에
포함해 전달한다 — 각 서브에이전트가 호출할 MCP 도구/실행할 `map_section.py --group` 값이 이
분기 하나로 전부 결정되기 때문이다 (서브에이전트가 스스로 분기를 재판단하지 않는다).

daily의 DATA 섹션 4개(1+2, 4, 5, 6)를 아래 4개 그룹으로 나눠 **Agent 도구로 한 메시지 안에서
동시에** 서브에이전트를 띄운다 (`general-purpose` 타입). ANALYSIS 섹션 1개(3, Executive Summary)는
서브에이전트가 반환한 digest를 오케스트레이터(본 대화)가 직접 읽고 기존 분석 지침대로 작성한다.

### 그룹 표 (분기별 MCP 호출)

| 그룹 | 담당 섹션 | 분기 A (Google/Meta) MCP 호출 | 분기 B (naver) MCP 호출 | digest 소비처 |
|---|---|---|---|---|
| A | 1+2 | `target_progress`(v1, `campaign_type="sales"`) | `get_target_progress_v2`(`as_of_date`=target_date) | **분기 A만**: 섹션3 |
| B | 4 | `get_sales_performance_daily`(start=week_start, end=target_date) | `get_naver_daily_attributed_sales`(start=target_date-6일, end=target_date) | **분기 B만**: 섹션3 |
| C | 5 | `get_sales_by_campaign_monthly`(day_offset=target_date.day) | `get_naver_campaign_performance`(start=end=target_date) | (없음 — 아래 참고) |
| D | 6 | `get_sales_by_asset_group_monthly`(day_offset=target_date.day) | `get_naver_sa_performance_daily` ×2(`group_by="ad-group"`/`"keyword"`, 둘 다 target_date 당일) | (없음 — 아래 참고) |

⚠️ **그룹 A/B의 digest 소비 방향이 분기마다 다르다** — 분기 A는 그룹 A digest를, 분기 B는 그룹 B
digest를 각각 섹션3에서 쓰고, 반대쪽은 쓰지 않는다(아래 "오케스트레이터가 병렬 결과를 받은 뒤"
참고). 두 분기 모두를 동시에 실행하는 일은 없으므로(브랜드 하나는 항상 한쪽 분기), 실제로는 항상
"그 브랜드의 분기에 해당하는 digest 하나"만 쓰인다.

⚠️ **그룹 C/D는 두 분기 모두 digest=None이다** — daily-section-3(분기 B)의 캠페인/광고그룹별
특이사항 문단은 그룹 C/D가 만드는 것과 **다른 날짜 범위**의 호출(target_date 당일 + 비교 기준
기간, `get_naver_sa_performance_daily(group_by="campaign"/"ad-group")`)이 필요하다 — 그룹 C(캠페인
성과)는 `get_naver_campaign_performance`를, 그룹 D(광고그룹/키워드)는 `get_naver_sa_performance_daily`를
쓰지만 **둘 다 target_date 하루치뿐**이라 섹션3이 필요로 하는 "비교 기준 기간 대비" 계산의 재료가
되지 못한다. 아래 "섹션3 작성" 항목 참고.

### 서브에이전트 지시문 (그룹당 1개, 총 4개를 한 메시지에서 병렬 호출)

각 서브에이전트에게 아래를 지시한다:

1. 0단계에서 판단한 분기(A 또는 B)에 해당하는 MCP 도구를 호출한다 (파라미터는
   `shared/sections/daily/daily-section-{N}.md`의 해당 분기 절 `## 분기 A`/`## 분기 B` 아래 `MCP 도구`
   설명을 그대로 따른다 — 절대 반대 분기의 도구를 쓰지 않는다). 그룹 D의 분기 B는 같은 도구를
   `group_by`만 바꿔 2회 호출한다.
2. 응답을 가공 없이 그대로 스크래치패드 임시 파일에 저장한다.
   - 그룹 A(분기 A)는 `target_progress` 응답을 `{"sales": {...}}` 형태 그대로 저장한다(응답이
     이미 `sales` 키 아래에 필요한 필드를 담고 있다고 가정).
   - 그룹 A(분기 B)는 `get_target_progress_v2` 응답에 `"as_of_date": "target_date"` 필드 하나를
     더해 저장한다(예: `{ ...응답 그대로..., "as_of_date": "2026-04-28" }`) — 이 값은 이미 MCP 호출
     파라미터로 쓴 것과 동일한 문자열이며, `map_section.py`가 "기간 진척률"(day-of-month/월
     일수)을 계산하는 데 쓴다.
   - 그룹 B(분기 B)는 `get_naver_daily_attributed_sales` 응답을 `{"items": [...]}` 형태 그대로
     저장한다.
   - 그룹 D(분기 B)는 두 호출 결과를 `{"ad_group": <group_by="ad-group" 응답>, "keyword":
     <group_by="keyword" 응답>}` 형태로 합쳐 저장한다.
3. 아래 명령을 그대로 실행한다 (`--group` 값은 `{A|B|C|D}_{google_meta|naver}` 중 0단계에서
   정한 분기에 해당하는 쪽 하나):
   ```
   python "<스킬 폴더 경로>/assets/docx_report/map_section.py" --report-type daily --group {A|B|C|D}_{google_meta|naver} --data <임시.json> --out <out.json>
   ```
4. `out.json`의 내용을 그대로 자신의 최종 응답으로 반환한다 — raw 데이터를 다시 설명하거나 요약하지
   않는다(오케스트레이터가 볼 결과는 이 압축된 JSON뿐이어야 한다).

### 오케스트레이터가 병렬 결과를 받은 뒤

5. 4개 서브에이전트 결과의 `sections[]`를 문서 순서(1,2,4,5,6 섹션 순서, 즉 그룹 A,B,C,D 순 —
   그룹 A는 `sections[]`에 1번, 2번 섹션이 이미 이 순서로 들어있다)대로 이어붙인다.
6. 텍스트 섹션 1개(섹션3, Executive Summary)를 분기에 따라 다르게 작성한다 — 두 분기의 형식과
   근거 데이터가 완전히 다르므로 절대 교차 적용하지 않는다:
   - **분기 A (Google/Meta)**: 그룹 A digest(`period_progress_pct`/`budget_utilization_*`/
     `revenue_achievement_*`/`roas_achievement_*` 등)를 근거로
     `shared/sections/daily/daily-section-3-executive-summary.md`의 분기 A 지침대로 작성한다 (dify는
     호출하지 않고, `실행 순서` 4단계 원칙대로 수치 기반 AI 직접 작성 — 개조식 문체 유지).
   - **분기 B (naver)**: 그룹 B digest(`daily_items` — target_date 포함 최근 7일의
     `logdate`/`ad_cost`/`revenue`/`roas`)로 최상위 불릿(`top_bullet`, 오늘 vs. 직전 7일 평균)의
     수치 근거를 얻는다. 그룹 C/D의 digest는 없으므로(위 "그룹 C/D는 두 분기 모두 digest=None"
     참고), 캠페인별/광고그룹별 특이사항 불릿에 필요한 데이터는 **이 시점에 오케스트레이터가 직접**
     아래를 추가로 호출한다 (mtd-section-5/execmtd-section-3의 `list_promotions` 직접 호출 선례와
     동일한 패턴 — ANALYSIS 섹션은 DATA 그룹이 커버하지 못하는 범위를 스스로 채운다):
     - `get_naver_sa_performance_daily(group_by="campaign")` / `(group_by="ad-group")`를 각각
       target_date와 비교 기준 기간에 대해 호출.
     - `list_promotions(start_date=target_date-21일, end_date=target_date)`로 최근 프로모션 여부
       확인.
     - `daily-section-3-executive-summary.md` 분기 B의 "작성 원칙" 1~6번을 그대로 따라
       `daily_summary_subheading`/`top_bullet`/`campaign_bullets`/`adgroup_bullets`를 만들고,
       그 파일의 "DOCX 섹션 (분기 B)" 조립 규칙대로 `body` 문자열을 조립한다.
7. 어느 그룹의 서브에이전트가 실패했거나 MCP가 빈 응답/에러를 반환하면, 그 그룹이 담당하던 섹션(들)은
   `데이터 부족 시` 규칙대로 `{ "type": "text", "heading": "...", "body": "데이터 준비 중" }`으로
   대체한다 — 다른 그룹은 정상 진행하며, 그 그룹에 의존하는 digest 항목은 텍스트 작성 시 건너뛴다.
8. 이후 절차(최종 JSON 조립 → `build.py` 호출 → 완료 메시지)는 위 `실행 순서` 6~8단계와 동일하다.

---

## mtd 전용: 병렬 서브에이전트 실행 방식

> ⚡ **기본 경로는 위 `고속 실행 공통 규칙(map_report.py)`이다.** 이 절의 서브에이전트 메커니즘은 Agent 도구가 있는 환경 전용 옵션이며, 그룹 표·MCP 파라미터·저장 형식·분석 지침은 두 경로가 공유한다.

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
| A | 1+2 | `get_target_progress_v2` | 섹션3 |
| B | 4 | `get_naver_monthly_ad_performance` | (없음) |
| C | 6 + 6.1(참조용) | `get_naver_item_sales_daily`, `get_naver_category_sales` | 섹션3, 섹션5 |
| D | 7 | `get_naver_channel_budget_progress` | 섹션3 |
| E | 9 | `get_naver_campaign_performance` | 섹션8 |
| F | 10 | `get_naver_group_performance` | (없음) |
| G | 11 | `get_naver_keyword_performance` | (없음) |

### 서브에이전트 지시문 (그룹당 1개, 총 7개를 한 메시지에서 병렬 호출)

각 서브에이전트에게 아래를 지시한다:

1. 이 그룹에 해당하는 MCP 도구를 호출한다 (파라미터/도구 선택 규칙은 `shared/sections/mtd/mtd-section-{N}.md`의
   `## MCP 도구 호출` 절을 그대로 따른다 — 절대 임의로 다른 도구를 쓰지 않는다). 그룹 C는 두 도구를
   순서대로 호출한다.
2. 응답을 가공 없이 그대로 스크래치패드 임시 파일에 저장한다. 그룹 C는
   `{"daily": <get_naver_item_sales_daily 응답>, "cumulative": <get_naver_category_sales 응답>}`
   형태로 두 응답을 합쳐 저장한다. 그룹 D는 `get_naver_channel_budget_progress` 응답을 그대로
   저장한다(응답 최상위에 `items`/`total`/`channel_group` 키가 있다고 가정).
   - ⚡ **그룹 E/F/G 상위 60행 저장 규칙 (유일하게 허용된 절단)**: 이 세 그룹의 응답 `items`는
     수백~수천 행일 수 있으나 docx 표는 매출 0원 행을 제외한 뒤 상위 50행만 싣는다. 따라서 임시
     파일에는 `items`를 **응답 순서 그대로 앞 60개만** 적고, 최상위에 `"items_total": <원본 items
     길이>`를 추가한다 (60개 이하면 전부 적되 `items_total`은 그래도 기록). 행 순서 변경/재정렬/선별은 여전히
     금지 — 응답이 준 순서에서 앞부분을 자르는 것만 허용된다. `map_section.py`가 `items_total`을
     `rows_total`로 전달해 "외 n행 생략" 캡션이 전체 기준으로 표시된다. 이 규칙은 `데이터 처리
     원칙`의 문서화된 예외이며, 그룹 E digest(`top_campaigns_by_ad_cost`)는 저장된 상위 60행
     내에서 계산된다.
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
     근거로 `shared/sections/mtd/mtd-section-3-executive-summary.md`의 4개 분석 항목을 작성한다.
   - **섹션5 (제품 판매 성과의 심층 분석)**: 그룹 C digest(`top_categories`/`top_category_totals`/
     `product_cumulative_sales`)를 근거로 `shared/sections/mtd/mtd-section-5-product-deep-dive.md`의
     지침대로 작성한다.
   - **섹션8 (캠페인별 성과 심층 분석)**: 그룹 E digest(`top_campaigns_by_ad_cost`)를 근거로
     `shared/sections/mtd/mtd-section-8-campaign-deep-dive.md`의 지침대로 작성한다.
7. 어느 그룹의 서브에이전트가 실패했거나 MCP가 빈 응답/에러를 반환하면, 그 그룹이 담당하던 섹션(들)은
   `데이터 부족 시` 규칙대로 `{ "type": "text", "heading": "...", "body": "데이터 준비 중" }`으로
   대체한다 — 다른 그룹은 정상 진행하며, 그 그룹에 의존하는 digest 항목은 텍스트 작성 시 건너뛴다.
8. 이후 절차(최종 JSON 조립 → `build.py` 호출 → 완료 메시지)는 위 `실행 순서` 6~8단계와 동일하다.

---

## monthly 전용: 병렬 서브에이전트 실행 방식

> ⚡ **기본 경로는 위 `고속 실행 공통 규칙(map_report.py)`이다.** 이 절의 서브에이전트 메커니즘은 Agent 도구가 있는 환경 전용 옵션이며, 그룹 표·MCP 파라미터·저장 형식·분석 지침은 두 경로가 공유한다.

> ⚙️ 이 절은 **`report_type=monthly`에만 적용**된다 (daily/mtd/executive-mtd는 각자의 절을 따른다).
> 목적은 시간/토큰 절약이며, **산출물(`.docx` 최종 렌더링 결과)은 순차 실행 방식과 완전히 동일해야
> 한다** — `데이터 처리 원칙`은 그대로 유지된다. mtd와 달리 monthly-section-6/8은 이 스킬이 직접
> 상위 N/증감률/채널 합산을 가공해야 하는 "monthly 전용 가공" 섹션이므로, 그 가공 규칙은 각 섹션
> 파일(`monthly-section-6-category-monthly-comparison.md`, `monthly-section-8-media-comparison-table.md`)에
> 문서화된 그대로 `section_mapping.py`가 실행한다 — 서브에이전트는 규칙을 재판단하지 않는다.

monthly의 8개 섹션 중 DATA 섹션 6개(1,2,4,6,7,8)를 아래 4개 그룹으로 나눠 **Agent 도구로 한
메시지 안에서 동시에** 서브에이전트를 띄운다 (`general-purpose` 타입 — MCP 도구와 Bash가 모두
필요). ANALYSIS 섹션 2개(3,5)는 서브에이전트가 반환한 digest를 오케스트레이터(본 대화)가 직접
읽고 기존 분석 지침대로 작성한다 — dify 미사용 등 기존 원칙은 동일하다.

mtd와 달리 monthly-section-6(카테고리별 월간 매출액 비교)과 monthly-section-7(일일 카테고리별
매출 현황)은 **하나의 그룹(C)으로 묶인다** — section-7의 문서는 "이 섹션의 5개 라인은
monthly-section-6에서 뽑은 상위 5개 카테고리와 동일한 카테고리로 맞춘다"고 명시하므로, 두 섹션이
서로 다른 서브에이전트에서 독립적으로 상위 5개를 계산하면 두 섹션의 카테고리 목록이 어긋날 수
있다 — 반드시 같은 서브에이전트/같은 매핑 호출 안에서 상위 5개를 한 번만 계산해 두 섹션 모두에
쓴다.

| 그룹 | 담당 섹션 | MCP 호출 (파라미터는 각 섹션 파일 참고) | digest 소비처 |
|---|---|---|---|
| A | 1+2 | `get_target_progress_v2` (`as_of_date`=해당 월 말일) | 섹션3 |
| B | 4 | `get_naver_monthly_ad_performance` | 섹션3 |
| C | 6+7 | `get_naver_category_sales` ×2(이번 달/전월), `get_naver_item_sales_daily` | 섹션3, 섹션5 |
| D | 8 | `get_naver_channel_progression` ×2(이번 달/전월) | 섹션3 |

### 서브에이전트 지시문 (그룹당 1개, 총 4개를 한 메시지에서 병렬 호출)

각 서브에이전트에게 아래를 지시한다:

1. 이 그룹에 해당하는 MCP 도구를 호출한다 (파라미터/도구 선택 규칙은
   `shared/sections/monthly/monthly-section-{N}.md`의 `## MCP 도구 호출` 절을 그대로 따른다 — 절대 임의로
   다른 도구를 쓰지 않는다). 그룹 C/D는 각각 두세 개 도구를 순서대로 호출한다.
2. 응답을 가공 없이 그대로 스크래치패드 임시 파일에 저장한다.
   - 그룹 C는 `{"curr": <이번 달 get_naver_category_sales 응답>, "prev": <전월 get_naver_category_sales
     응답>, "daily": <get_naver_item_sales_daily 응답>, "curr_month_label": "26년 3월",
     "prev_month_label": "26년 2월"}` 형태로 저장한다 — `curr_month_label`/`prev_month_label`은 MCP
     응답에 없으므로, MCP 호출 시 이미 계산해 둔 연월 문자열(예: `"26년 3월"`, 2자리 연도)을 그대로
     써서 채운다.
   - 그룹 D는 `{"curr": <이번 달 get_naver_channel_progression 응답>, "prev": <전월
     get_naver_channel_progression 응답>, "curr_month_label": "2026년 3월", "prev_month_label":
     "2026년 2월"}` 형태로 저장한다 — 이쪽은 4자리 연도 포맷이다(`monthly-section-8-media-
     comparison-table.md`의 예시와 동일하게).
3. 아래 명령을 그대로 실행한다:
   ```
   python "<스킬 폴더 경로>/assets/docx_report/map_section.py" --report-type monthly --group {A|B|C|D} --data <임시.json> --out <out.json>
   ```
4. `out.json`의 내용을 그대로 자신의 최종 응답으로 반환한다 — raw 데이터를 다시 설명하거나 요약하지
   않는다(오케스트레이터가 볼 결과는 이 압축된 JSON뿐이어야 한다).

### 오케스트레이터가 병렬 결과를 받은 뒤

5. 4개 서브에이전트 결과의 `sections[]`를 문서 순서(1,2,4,6,7,8 섹션 순서, 즉 그룹 A,B,C,D 순 —
   그룹 C는 `sections[]`에 6번, 7번 섹션이 이 순서 그대로 이미 들어있다)대로 이어붙인다.
6. digest를 모아 아래처럼 텍스트 섹션 2개를 직접 작성한다 (섹션 파일의 분석 항목 지침은 그대로
   따른다 — 새 수치를 지어내지 않는다):
   - **섹션3 (Executive Summary)**: 그룹 A digest(ROAS/달성률/소진율) + 그룹 B digest(`items`,
     최근 6개월 추이) + 그룹 C digest(`category_monthly_comparison`, 카테고리 트렌드 특이사항) +
     그룹 D digest(`media_monthly_comparison`, 채널 ROAS 변화)를 근거로
     `shared/sections/monthly/monthly-section-3-executive-summary.md`의 5개 분석 항목을 작성한다.
   - **섹션5 (제품 판매 트렌드 분석)**: 그룹 C digest(`category_monthly_comparison`,
     `daily_sales`)를 근거로 `shared/sections/monthly/monthly-section-5-product-deep-dive.md`의 지침대로
     작성한다 — 3-3(급등/급락일 프로모션 연계)이 필요하면 `list_promotions` MCP 도구를 별도로
     호출해 근거를 찾고, 찾지 못하면 그 문장은 생략한다.
7. 어느 그룹의 서브에이전트가 실패했거나 MCP가 빈 응답/에러를 반환하면, 그 그룹이 담당하던 섹션(들)은
   `데이터 부족 시` 규칙대로 `{ "type": "text", "heading": "...", "body": "데이터 준비 중" }`으로
   대체한다 — 다른 그룹은 정상 진행하며, 그 그룹에 의존하는 digest 항목은 텍스트 작성 시 건너뛴다.
8. 이후 절차(최종 JSON 조립 → `build.py` 호출 → 완료 메시지)는 위 `실행 순서` 6~8단계와 동일하다.

---

## executive-mtd 전용: 병렬 서브에이전트 실행 방식

> ⚡ **기본 경로는 위 `고속 실행 공통 규칙(map_report.py)`이다.** 이 절의 서브에이전트 메커니즘은 Agent 도구가 있는 환경 전용 옵션이며, 그룹 표·MCP 파라미터·저장 형식·분석 지침은 두 경로가 공유한다.

> ⚙️ 이 절은 **`report_type=executive-mtd`에만 적용**된다 (daily/mtd/monthly는 각자의 절을 따른다).
> 목적은 시간/토큰 절약이며, **산출물(`.docx` 최종 렌더링 결과)은 순차 실행 방식과 완전히 동일해야
> 한다** — `데이터 처리 원칙`은 그대로 유지된다. executive-mtd-section-4(주요 카테고리별 월간
> 매출액 증감)와 executive-mtd-section-5(매체별 성과 비교)는 mtd/monthly에는 없는 "executive-mtd
> 전용 가공" 섹션이므로, 그 가공 규칙은 각 섹션 파일(`executive-mtd-section-4-category-mom-
> highlights.md`, `executive-mtd-section-5-media-roas-comparison.md`)에 문서화된 그대로
> `section_mapping.py`가 실행한다 — 서브에이전트는 규칙을 재판단하지 않는다.

executive-mtd의 5개 섹션 중 DATA 섹션 4개(1,2,4,5)를 아래 4개 그룹으로 나눠 **Agent 도구로 한
메시지 안에서 동시에** 서브에이전트를 띄운다 (`general-purpose` 타입 — MCP 도구와 Bash가 모두
필요). ANALYSIS 섹션 1개(3, Executive Summary)는 서브에이전트가 반환한 digest를
오케스트레이터(본 대화)가 직접 읽고 기존 분석 지침대로 작성한다 — dify 미사용 등 기존 원칙은
동일하다.

executive-mtd는 mtd/monthly와 달리 **월 목표 카드(kpi-goals) 섹션이 없다** — 그룹 A는
`get_target_progress_v2` 응답 하나로 섹션(kpi_cards) 1개만 만든다(mtd/monthly의 그룹 A처럼
2개 섹션 쌍을 만들지 않는다). 또한 **섹션 순서가 mtd/monthly와 다르다** — 월별 광고 성과 차트
(그룹 B, 2번 섹션)가 Executive Summary(3번 섹션)보다 먼저 온다 (임원이 추세 그래프를 먼저 보고
그 해석을 Executive Summary에서 읽게 하려는 의도, `executive-mtd-section-2-monthly-chart.md`
참고).

| 그룹 | 담당 섹션 | MCP 호출 (파라미터는 각 섹션 파일 참고) | digest 소비처 |
|---|---|---|---|
| A | 1 | `get_target_progress_v2` (`as_of_date`=target_date, mtd와 동일한 부분월 기준) | 섹션3 |
| B | 2 | `get_naver_monthly_ad_performance` | 섹션3 |
| C | 4 | `get_naver_category_sales` ×2(이번 달 MTD/전월 동일 기간) | 섹션3 |
| D | 5 | `get_naver_channel_progression` ×2(이번 달/전월 동일 기간) | 섹션3 |

### 서브에이전트 지시문 (그룹당 1개, 총 4개를 한 메시지에서 병렬 호출)

각 서브에이전트에게 아래를 지시한다:

1. 이 그룹에 해당하는 MCP 도구를 호출한다 (파라미터/도구 선택 규칙은
   `shared/sections/executive-mtd/executive-mtd-section-{N}.md`의 `## MCP 도구 호출` 절을 그대로
   따른다 — 절대 임의로 다른 도구를 쓰지 않는다). 그룹 C/D는 각각 두 도구(또는 같은 도구 2회
   호출)를 순서대로 호출한다.
   - **그룹 C/D의 전월 구간은 "전월 전체"가 아니라 "전월의 동일 기간"이다** (monthly와 다른 부분,
     반드시 정확히 지킬 것) — 기준일(`target_date`)의 일(day)만큼 전월 1일부터 잘라 쓴다. 예:
     기준일 2026-03-15 → 전월 구간은 2026-02-01~02-15. 기준일의 일자가 전월 마지막 날보다 크면
     전월 마지막 날로 clamp한다 (예: 기준일 3/31, 2월이 28일까지면 전월 구간은 2/1~2/28).
     (`executive-mtd-section-4-category-mom-highlights.md`,
     `executive-mtd-section-5-media-roas-comparison.md` 참고)
2. 응답을 가공 없이 그대로 스크래치패드 임시 파일에 저장한다.
   - 그룹 C는 `{"curr": <이번 달 MTD get_naver_category_sales 응답>, "prev": <전월 동일 기간
     get_naver_category_sales 응답>}` 형태로 저장한다(월 레이블은 필요 없다 — section-4의 최종
     출력은 카테고리명+증감률 카드뿐이라 연월 문자열을 쓰지 않는다).
   - 그룹 D는 `{"curr": <이번 달 get_naver_channel_progression 응답>, "curr_as_of_date":
     "target_date", "prev": <전월 get_naver_channel_progression 응답>, "prev_as_of_date":
     "전월 동일 기간의 마지막 날(위 1번 규칙으로 계산, clamp 포함)", "prev_period_label": "2월",
     "curr_period_label": "3월"}` 형태로 저장한다 — `get_naver_channel_progression`은 항상 해당
     월 전체를 반환하므로, `*_as_of_date` 이후 일자의 일별 항목은 `section_mapping.py`가 직접
     걸러내고 합산한다(도구가 잘라주지 않는다). `*_period_label`은 MCP 응답에 없으므로 MCP 호출
     시 이미 계산해 둔 "N월" 문자열(연도 없이, `executive-mtd-section-5-media-roas-comparison.md`
     예시와 동일한 포맷)을 그대로 채운다.
3. 아래 명령을 그대로 실행한다:
   ```
   python "<스킬 폴더 경로>/assets/docx_report/map_section.py" --report-type executive-mtd --group {A|B|C|D} --data <임시.json> --out <out.json>
   ```
4. `out.json`의 내용을 그대로 자신의 최종 응답으로 반환한다 — raw 데이터를 다시 설명하거나 요약하지
   않는다(오케스트레이터가 볼 결과는 이 압축된 JSON뿐이어야 한다).

### 오케스트레이터가 병렬 결과를 받은 뒤

5. 4개 서브에이전트 결과의 `sections[]`를 **문서 순서(1,2,3,4,5)**대로 이어붙인다 — 그룹
   A(섹션1) → 그룹 B(섹션2) → **오케스트레이터가 작성하는 Executive Summary(섹션3)** → 그룹
   C(섹션4) → 그룹 D(섹션5) 순서다 (`실행 순서` 절과 달리 그룹 알파벳 순서와 문서 순서 사이에
   Executive Summary가 끼어드는 것이 executive-mtd만의 특징이다 — 위 "섹션 순서가 mtd/monthly와
   다르다" 참고).
6. digest를 모아 텍스트 섹션 1개(Executive Summary, 섹션3)를 직접 작성한다 (섹션 파일의 분석 항목
   지침은 그대로 따른다 — 새 수치를 지어내지 않는다):
   - **섹션3 (Executive Summary)**: 그룹 A digest(ROAS/달성률/소진율) + 그룹 B digest(`items`,
     최근 6개월 광고비/매출/ROAS 추이) + 그룹 C digest(`category_mom_highlights`, 카테고리별 MoM
     특이사항) + 그룹 D digest(`media_roas_comparison`, 채널별 ROAS MoM 변동)를 근거로
     `shared/sections/executive-mtd/executive-mtd-section-3-executive-summary.md`의 작성 원칙(3~5문장,
     "무엇이 움직였는지 + 왜 임원이 신경 써야 하는지", `list_promotions` 참고 가능)대로 작성한다.
7. 어느 그룹의 서브에이전트가 실패했거나 MCP가 빈 응답/에러를 반환하면, 그 그룹이 담당하던 섹션은
   `데이터 부족 시` 규칙대로 `{ "type": "text", "heading": "...", "body": "데이터 준비 중" }`으로
   대체한다 — 다른 그룹은 정상 진행하며, 그 그룹에 의존하는 digest 항목은 텍스트 작성 시 건너뛴다.
   그룹 D가 유효한 채널 행을 하나도 만들지 못하면(`section_mapping.py`가 `sections: []`를 반환)
   섹션5 전체를 생략한다 — `executive-mtd-section-5-media-roas-comparison.md`의 "데이터가
   비어있으면 이 섹션 전체를 생략한다" 규칙 그대로다.
8. 이후 절차(최종 JSON 조립 → `build.py` 호출 → 완료 메시지)는 위 `실행 순서` 6~8단계와 동일하다.

---
