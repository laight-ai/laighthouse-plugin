# mtd-detailed 성능 최적화 변경 이력

`daily-summary`에서 검증된 최적화(`daily-summary/CLAUDE.md` 참고)를 `mtd-detailed`에 구조적으로
적용 가능한 범위 내에서 이식한 작업 기록.

## 2026-08-09 (4차) — 섹션 7을 `get_ad_performance_range_table`로 전환

새 MCP 도구 `get_ad_performance_daily_table`이 추가됐다 — 같은 파라미터(`brand_name`/
`start_date`/`end_date`/`group_by`/`media`/`campaign_type`/`limit`/`offset`)를 받지만, 날짜별
행이 아니라 **지정한 기간 전체를 dimension-group(media/campaign/asset_group/ad_name)당 1행으로
합산**해 반환한다(`is_active`는 항상 None, span 최대 92일).

- **적용 대상 판단**: 섹션 7(Campaign별 성과)은 캠페인별로 MTD(월초~target_date) 구간 전체를
  합산한 값(노출/클릭/광고비/매출/예약 완료 합계)으로 광고비 내림차순 랭킹 표를 만드는
  섹션이다 — 캠페인×날짜 세부 트렌드가 아니라 **캠페인당 기간 합계 1행**이 필요한 구조라서,
  `get_ad_performance_range_table`의 반환 형태와 정확히 일치한다. MTD 구간은 최대 31일로 92일
  cap에도 항상 들어간다. → **적용 대상 확정, 전환함.**
  - 참고로 다른 섹션(예: 섹션 4 일일 매출 현황, 섹션 3 월별 광고 성과)은 날짜별/월별 트렌드가
    필요해 이 도구와 맞지 않으므로 손대지 않았다 — 섹션 7만 이 도구의 조건(기간 합계 랭킹)에
    해당한다.
- **변경 내용**: `mtd-detailed-section-7-campaign-performance.md`의 매체별 4회 호출
  (`get_ad_performance_daily_table` × google/meta/naver/airbridge, `group_by:"campaign"`)을
  **동일한 4회 호출 구조를 유지한 채** 도구명만 `get_ad_performance_range_table`로 교체했다
  (`media` 생략 통합은 이번 변경과 무관 — 위 "2026-08-09 (2차)"에서 되돌린 그 통합을 다시
  적용한 것이 아니다. 매체별 4회 명시적 호출은 그대로다). 이에 맞춰:
  - "필요 데이터" 절의 "캠페인별로 일별 행을 합산" 문구를 "캠페인당 이미 합산된 행을 그대로
    읽음"으로 수정 — 값 계산 로직(CTR/CPA/ROAS 공식, exact-match 조인 규칙)은 전혀 바꾸지
    않았다.
  - 이전에 **필수**였던 "SKILL.md 「실행 방식 절대 지침」에 따른 Bash 캠페인별 합산" 절차를,
    이 도구가 서버 쪽에서 이미 합산을 마쳐 반환하므로 **불필요**하다고 명시했다(정렬은 필요시
    Bash를 써도 되지만 합산과 달리 필수 절차는 아님).
  - `SKILL.md`의 「실행 방식 절대 지침」에서 "Bash 집계 필수" 규칙이 적용되는 대상을
    `get_ad_performance_daily_table`/`weekly_table`/`monthly_table`(날짜별 행 반환)로 명확히
    하고, `get_ad_performance_range_table`(구간 전체 사전 합산)은 이 규칙의 예외라고 명시했다.
    예시로 들던 "섹션 7"도 "섹션 5"로 교체했다(섹션 7은 더 이상 이 규칙의 적용 대상이
    아니므로).
  - `SKILL.md` 3단계의 generic 도구 목록에 `get_ad_performance_range_table`을 추가했다.
- **출력값 불변**: 최종 렌더링 값·정렬·조인 규칙은 전혀 바꾸지 않았다 — 도구가 서버에서
  이미 수행하던 합산을 모델이 Bash로 다시 하지 않게 됐을 뿐, 계산 결과는 동일해야 한다.
- **영향받은 파일**: `mtd-detailed-section-7-campaign-performance.md`, `SKILL.md`.

## 2026-08-09 (3차) — chart.js 상대 경로 되돌림 + Bash 집계 예외를 필수로 강화

같은 날 형제 스킬 `creative-detailed`의 실제 운영(real-world) 실행에서 아래 두 가지가 실제로
깨지는 것이 확인되어, 이전 두 차례 변경 중 일부를 되돌리거나 강화했다.

- **문제 1 (chart.js 상대 경로 되돌림)**: "2026-08-09" 항목의 4번에서 도입한
  "`chart.umd.min.js`를 저장 폴더에 파일로 복사해두고 상대 경로 `<script src>`로 참조"
  방식이 `creative-detailed` 실행에서 실패했다. 리포트를 샌드박스 출력 디렉터리
  (`/mnt/user-data/outputs/`)에 저장했을 때, 플랫폼 프리뷰가 HTML과 `chart.umd.min.js`를
  서로 별개의 다운로드 파일로 취급해 상대 경로 `<script src>`가 로드되지 않았고, 그 결과
  모든 차트가 빈 캔버스로 렌더링됐다. **되돌림**: 존재 확인/1회 복사/상대 경로 참조라는
  분기 로직을 완전히 제거하고, `chart.umd.min.js`를 항상 리포트 HTML의
  `<script>{CHART_JS_INLINE}</script>` 안에 완전히 인라인하는 방식(3차 변경 이전 방식)으로
  복귀했다. 외부 CDN `<script src>` 금지 경고는 그대로 유지했다(무관한 별개 이슈).
  - **영향받은 파일**: `SKILL.md`(6/7단계, 보고서 골격의 `<head>` 부분).
- **문제 2 (Bash 집계 예외를 필수로 강화)**: "2026-08-09 (2차)" 항목에서 추가한 "`group_by`가
  `ad`/`campaign`/`ad-set`인 응답에는 1회성 Bash 집계를 써도 된다"는 허용(may) 문구가 충분히
  강하지 않았다. `creative-detailed`(같은 호출 계열, `group_by:"ad"`) 실행에서, 모델이 처음엔
  Bash 파일에 데이터를 쓰기 시작했다가 도중에 "effort 예산이 부족하다"며 포기하고 "표를
  눈으로 훑어보고 나머지는 추정"하는 방식으로 전환했다 — "백여 개 조합을 전부 확인하지
  못했다"고 스스로 인정하면서도 결과를 보고서에 그대로 냈다. 이는 이 스킬이 막으려던 바로
  그 correctness 위반이다. **강화**: `SKILL.md`「실행 방식 절대 지침」의 해당 문단을 "해도
  되는 선택"에서 "**반드시** 해야 하는 필수 절차"로 재작성했다 — 부분 처리·추정 금지를
  명시하고, effort가 부족하면 근사치로 넘어가지 말고 더 작은 단위(예: 날짜별)로 쪼개 Bash
  집계를 끝까지 완료하도록 요구하며, 그래도 안 되면 해당 섹션을 "데이터 준비 중"으로
  표시하는 쪽이 근사치보다 낫다고 명시했다. `mtd-detailed-section-7-campaign-performance.md`의
  참조 문구도 동일한 어조로 맞췄다.
  - **영향받은 파일**: `SKILL.md`, `mtd-detailed-section-7-campaign-performance.md`.

## 2026-08-09 (2차) — section-7 `media` 생략 통합 되돌림 + Bash 집계 예외 추가

같은 날 앞선 최적화(아래 "2026-08-09" 항목의 1번, section-7 부분)에서 섹션 7의
`get_ad_performance_daily_table` 4회(google/meta/naver/airbridge, `group_by:"campaign"`) 호출을
`media` 생략 1회 호출로 통합했었다. 이는 잘못된 일반화였다 — **되돌림**.

- **문제**: 이 통합 논리("`media`가 `None`이면 모든 `DataSource`를 순회해 합치므로 안전하다")는
  `group_by`가 `total`/`media`처럼 저(低)카디널리티일 때만 응답 크기 면에서 안전하다. `campaign`/
  `ad-set`/`ad`처럼 행 단위가 세분화되는 `group_by`에서는 `media`를 생략하면 불필요한 매체의
  행까지 한 응답에 전부 섞여 응답 크기가 매체 수만큼 곱해진다. 형제 스킬 `creative-summary`
  (`group_by:"ad"`)의 실제 운영 사례에서, 7일치 기간만으로도 `media` 생략 응답이 766,576자에
  달해 모델 컨텍스트에 담기 어려웠고, 모델이 큰 표를 bash heredoc 파일로 손수 나눠 옮기고
  일부 합계를 근사치로 채우는 correctness 위반까지 발생했다(해당 단계에 약 6분 소요). 섹션
  7은 MTD(월초~target_date, 최대 한 달치) 기간에 캠페인 단위 granularity이므로 같은 위험이
  있다.
- **변경**: `mtd-detailed-section-7-campaign-performance.md`의 MCP 호출을 `media` 생략 1회
  호출에서 **매체별 4회 명시적 호출**(google/meta/naver/airbridge, 각각 `group_by:"campaign"`,
  동일 날짜 범위)로 되돌렸다. `SKILL.md`의 「실행 방식 절대 지침」 근처 서술과 「병렬 호출
  지침」 절에서 섹션 7을 "media 생략 1회 통합" 사례로 언급하던 부분도 함께 수정했다.
- **section-1/2/3의 `group_by:"media"` 통합은 영향받지 않음**: 이들은 저카디널리티
  `group_by:"media"`(또는 `"total"`) 호출이라 `media` 생략이 여전히 안전하다 — 손대지
  않았다.
- **section-6(광고 매체별 현황) 확인**: section-6은 section-7의 데이터를 전혀 참조하지 않고,
  section-1이 호출한 `get_ad_performance_monthly_table`(`group_by:"media"`, `media` 생략)
  응답만 무조건 재사용한다. section-7의 되돌림과 무관한 별개 호출이므로 **영향 없음** —
  section-6 파일 자체는 수정하지 않았다.
- **`SKILL.md`「실행 방식 절대 지침」에 Bash 집계 예외 추가**: 스크립트 금지 원칙이 "Bash를
  절대 쓰지 말라"는 뜻으로 과잉 적용되어, 큰 응답을 모델이 손으로 옮겨 적거나 머릿속으로
  합산하게 만드는 문제(위 `creative-summary` 사례)를 막기 위해, `group_by`가 `ad`/`campaign`/
  `ad-set`인 섹션에서는 **파일로 남기지 않는 1회성 Bash 명령**(grep/awk/jq 등)으로 매체
  필터링·캠페인별 합산·정렬을 수행한 뒤 그 결과 소표만 컨텍스트에 남기도록 명시적으로
  허용했다. 재사용 가능한 파이프라인 스크립트 파일을 만드는 것과는 구분되며, 근사치로
  채우는 것은 여전히 금지한다.
- **영향받은 파일**: `mtd-detailed-section-7-campaign-performance.md`, `SKILL.md`.

## 2026-08-09

### 1. `media` 파라미터 생략으로 다중 호출 → 단일 호출 통합

`get_ad_performance_daily_table`/`get_ad_performance_monthly_table`이 `media`만 바꿔 반복
호출되던 지점을 전부 `media` 생략 1회 호출로 통합했다. `laighthouse-prism`의
`src/repositories/v2_ad_performance.py`(`query_daily`/`query_monthly`)를 직접 확인한 결과,
`media`가 `None`이면 `if media in (None, "google")` 형태로 모든 `DataSource`를 순회해 합치는
구조이며, 이 분기는 `group_by` 값(`"media"`든 `"campaign"`이든)과 무관하게 동일하게 동작한다 —
즉 브랜드나 `group_by`에 상관없이 안전한 최적화다.

- **section-1(목표 달성 현황)**: `get_ad_performance_monthly_table`을 매출 실적용 1회
  (`media="airbridge"`, `group_by:"media"`) + no-budget fallback용 최대 3회
  (`media`=해당 매체, `group_by:"total"`)로 최대 4회 부르던 것을 **`media` 생략 1회 호출**로
  통합. 이 호출 하나가 google/meta/naver의 소진액과 airbridge의 매출 실적을 전부 반환하므로,
  목표 판정(no-budget 여부) 결과를 기다렸다가 조건부로 fallback을 추가 호출할 필요 자체가
  없어졌다.
- **section-3(월별 광고 성과)**: `get_ad_performance_monthly_table` 4회(google/meta/naver
  `group_by:"total"` + airbridge `group_by:"media"`, 동일 `start_month`/`end_month`/
  `day_offset`)를 **`media` 생략 1회 호출**로 통합.
- **section-2(Executive Summary)의 신규 호출**: 당월/전월 동기 누적치를 구하는
  `get_ad_performance_monthly_table` 4회(google/meta/naver `group_by:"total"` + airbridge
  `group_by:"media"`, 동일 `start_month`=전월/`end_month`=당월/`day_offset`)를 **`media` 생략
  1회 호출**로 통합.
- **section-7(캠페인별 성과)**: `get_ad_performance_daily_table` 4회(google/meta/naver/
  airbridge, 모두 `group_by:"campaign"`, 동일 날짜 범위)를 **`media` 생략 1회 호출**로 통합.
- **section-6(광고 매체별 현황)**: 원래 section-1과 별도로 매출 실적 호출(1회) + 자체 fallback
  호출(최대 3회)을 부르되 "섹션 1이 이미 호출했으면 재사용"하는 조건부 로직이었다. section-1이
  이제 위 방식으로 항상 1회만 호출하므로, section-6은 **그 호출을 무조건 재사용**하도록 단순화
  했다 — 별도 호출 로직 자체가 없어졌다.
- **section-4(일일 매출 현황)**: 원래도 `get_ad_performance_daily_table` 1회(media="airbridge",
  group_by="media")만 호출하고 있어 media별 반복 호출이 아니었다 — **변경 없음**. section-7과
  날짜 범위는 같지만 `group_by`가 다르므로(`media` vs `campaign`) 두 섹션의 호출을 서로
  합칠 수는 없다(합치면 어느 한쪽이 원치 않는 그룹핑 결과를 받게 된다).
- **결과**: 이 스킬의 데이터 호출이 (target_progress 3회 고정 제외) 최대 약 18회 이상
  (section-1 최대4 + section-2 4 + section-3 4 + section-4 1 + section-6 최대4 + section-7 4)
  에서 **최대 9회**(target_progress 3 + section-1 1 + section-2 1 + section-3 1 + section-4
  1(+list_promotions 1) + section-6 0(재사용) + section-7 1)로 줄었다.
- **영향받은 파일**: `mtd-detailed-section-1-target-achievement.md`,
  `mtd-detailed-section-2-executive-summary.md`,
  `mtd-detailed-section-3-monthly-ad-performance.md`,
  `mtd-detailed-section-6-channel-budget.md`,
  `mtd-detailed-section-7-campaign-performance.md`, `SKILL.md`.
- **출력값 불변 보장**: `group_by:"media"`(또는 `"campaign"`)로 `media`를 생략해 받은 응답에서
  해당 매체 행만 골라 쓰는 것은, 그 매체만 지정해서 별도로 호출했을 때와 **동일한 값**을
  반환한다(위 리포지토리 코드 확인 — 매체별 쿼리 함수를 그대로 실행해 합치는 구조이므로 매체
  간 간섭이 없다). `daily-summary`에서 이미 값 일치를 실측 확인했고(같은 저장소, 같은 도구),
  구조가 동일하므로 재검증 없이 안전하게 적용했다.

### 2. `get_target_progress_v2` — 변경 없음 (의도적으로 그대로 둠)

`daily-summary/CLAUDE.md`에서 이미 조사했듯, 이 도구는 `media`를 필수 enum으로 요구해 생략이
불가능하다. 백엔드 스키마 변경이 필요하고 매체별 메시지 포맷 차이로 로직이 복잡해질 수 있어
별도 검토 없이는 손대지 않았다 — `mtd-detailed`의 section-1/6이 공유하는 3회 호출은 그대로 둔다.

### 3. `list_promotions` — 이미 최적화되어 있어 변경 없음

`mtd-detailed`는 애초에 `list_promotions`를 section-4(일일 매출 현황)에서 **1회만** 호출하고
section-2(Executive Summary)/section-5(캠페인 분석)가 그 응답을 그대로 재사용하는 구조였다.
겹치는 여러 호출을 하나로 합칠 필요 자체가 없어 이 항목은 손대지 않았다.

### 4. `chart.umd.min.js`(약 208KB) 인라인 방식 변경

`daily-summary`와 동일한 문제였다 — 기존에는 매 리포트마다 이 파일 전체를 응답 텍스트로
재생성해 `{CHART_JS_INLINE}`에 넣고 있었다. `daily-summary`와 같은 방식으로 변경:
- 로컬 파일 저장본은 `chart.umd.min.js`가 저장 폴더에 이미 있는지 확인 후, 없을 때만 파일
  그대로 복사(또는 일반 파일 쓰기 도구로 1회 생성)해두고 `<script src="chart.umd.min.js">`
  상대 경로로 참조한다.
- `mtd-detailed`는 `daily-summary`와 달리 **항상 Artifact(채팅 내부 표시)와 파일 저장을 둘 다
  낸다**는 기존 구조를 그대로 유지했다 — 이 구조 자체는 이번 작업 범위가 아니므로 손대지 않고,
  Artifact 쪽만 "CSP로 상대 경로가 막히므로 인라인 경로를 쓴다"고 명시했다.
- **영향받은 파일**: `SKILL.md` (6/7단계, 보고서 골격의 `<head>` 부분).

### 5. 병렬 호출 지침 + 스크래치패드 금지 규칙 추가

`mtd-detailed`에는 원래 이 두 지침이 없었다(daily-summary는 실측 이후 추가됐지만 mtd-detailed는
애초에 작성 시점이 달라 누락돼 있었다). `daily-summary`에서 정립된 정확한 프레이밍
("배치는 턴 오버헤드 제거 효과일 뿐 네트워크 동시 실행 보장은 아니다 — 진짜 개선은 호출 총
개수를 줄이는 것")을 처음부터 정확하게 반영해 `SKILL.md`에 「병렬 호출 지침」 섹션과
스크래치패드/임시 파일 금지 규칙을 신규 추가했다.
- **영향받은 파일**: `SKILL.md`.

## 적용하지 않은 항목과 이유

- **`get_target_progress_v2` 통합** — 위 2번 참고 (도구 스키마 제약, 별도 검토 필요).
- **section-4의 `get_ad_performance_daily_table` 호출을 section-7과 병합** — 두 섹션의 날짜
  범위(월초~target_date)는 같지만 `group_by`가 다르다(section-4는 `"media"`, section-7은
  `"campaign"`). 하나의 응답으로 두 그룹핑을 동시에 만족시킬 수 없으므로 병합하지 않았다.
- **`list_promotions` dedup** — 위 3번 참고. 이미 1회 호출 구조였다.
