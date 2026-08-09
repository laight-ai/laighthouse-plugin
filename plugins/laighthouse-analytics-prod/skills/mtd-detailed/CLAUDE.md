# mtd-detailed 성능 최적화 변경 이력

`daily-summary`에서 검증된 최적화(`daily-summary/CLAUDE.md` 참고)를 `mtd-detailed`에 구조적으로
적용 가능한 범위 내에서 이식한 작업 기록.

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
