# daily-detailed 성능 최적화 변경 이력

`daily-summary`에 적용한 최적화(`daily-summary/CLAUDE.md` 참고)를 `daily-detailed`에도 구조가
맞는 범위에서 적용한 작업 기록. 새로운 최적화를 적용할 때마다 이 파일에 **날짜 + 무엇을 + 왜 +
검증 방법**을 추가한다 — 나중에 회귀가 생기면 어떤 변경이 원인인지 추적하기 위함.

## 2026-08-09

### 1. `media` 파라미터 생략으로 다중 호출 → 단일(또는 최소) 호출 통합

- **section-1(목표 달성 현황)**: 매출 실적 호출(`get_ad_performance_monthly_table`,
  `media="airbridge"`)과 no-budget fallback 소진액(media별 3회 조건부 호출)을 **`media` 생략
  1회 호출**로 통합 — `daily-summary-section-1`에 이미 적용된 것과 완전히 동일한 패턴(이
  스킬의 section-1은 원래 `daily-summary`의 최적화 이전 section-1과 문구까지 거의 동일했다).
  목표 판정 결과를 기다리는 조건부 2차 라운드가 완전히 제거되어, `get_target_progress_v2` ×3과
  같은 배치에서 항상 함께 발사한다.
- **section-3(최근 7일 성과)**: 매체별 4회 호출(google/meta/naver `group_by:"total"` +
  airbridge `group_by:"media"`)을 **`media` 생략 1회 호출**(`group_by:"media"`)로 통합 —
  `daily-summary-section-3`와 동일한 패턴.
- **section-4(캠페인 성과, D-1 vs D-0)**: 매체별 4회 호출(google/meta/naver/airbridge 전부
  `group_by:"campaign"`)을 **`media` 생략 1회 호출**로 완전히 통합 — 네 매체 모두 `group_by`가
  동일해서 daily-summary의 패턴을 그대로 적용할 수 있었다.
- **section-5(광고그룹 및 광고 성과, D-1 vs D-0)**: 4회 호출 중 google/meta/naver
  (`group_by:"ad"`)만 **`media` 생략 1회 호출**로 통합했다. airbridge는 `group_by:"campaign"`
  으로 **다른 group_by**가 필요해서 이 통합 호출에 함께 넣을 수 없다 — `media`를 생략하면
  google/meta/naver/airbridge 전부가 **같은 group_by**로 반환되므로, airbridge까지 포함하려면
  이 섹션에 필요 없는 `group_by:"ad"`(캠페인/광고그룹/광고 단위)로 airbridge를 받게 되어
  캠페인 단위 집계가 깨진다. 따라서 이 섹션만 **2회 호출**(media 생략+`group_by:"ad"` 1회 +
  `media:"airbridge"`+`group_by:"campaign"` 1회)로 남았다 — 4회보다는 줄었지만 daily-summary
  수준의 완전 통합은 구조적으로 불가능하다.
- **왜**: `daily-summary/CLAUDE.md`에서 이미 실측 확인한 대로, `media` 생략 시 백엔드
  (`v2_ad_performance.py`)가 내부적으로 모든 `DataSource`를 순회해 매체별 분리 호출과 동일한
  행을 반환한다 — 이 동작은 브랜드나 report_type에 종속되지 않는 범용 도구 동작이므로
  `daily-detailed`에도 동일하게 적용 가능하다고 판단했다. 결과값이 바뀌지 않는다는 사용자
  전제조건은, `media`가 같은 `group_by`로 통합되는 호출에 한해서만 성립한다는 점을
  section-5에서 확인하고 그 경계를 지켰다.
- **영향받은 파일**: `daily-detailed-section-1-target-achievement.md`,
  `daily-detailed-section-3-daily-performance-7days.md`,
  `daily-detailed-section-4-campaign-performance.md`,
  `daily-detailed-section-5-ad-performance.md`, `SKILL.md`.

### 2. section-3 응답을 section-4/5가 재사용하는 것은 **적용하지 않음** (구조적으로 불가능)

`daily-summary`에서는 section-3의 `media` 생략 응답(7일 범위, `group_by:"media"`)을 section-4/5가
그대로 재사용했지만, `daily-detailed`에서는 이 재사용이 성립하지 않는다:
- section-3은 7일 범위지만 section-4/5는 D-1~D0 이틀 범위다 (날짜 범위는 부분집합 관계가
  맞다).
- 하지만 **`group_by` 단위 자체가 다르다** — section-3은 `group_by:"media"`(매체당 합산 한
  줄)인데, section-4는 `group_by:"campaign"`(캠페인별 행), section-5는 `group_by:"ad"`(광고
  단위 행)가 필요하다. `group_by:"media"` 응답에는 캠페인/광고그룹/광고 차원 자체가 없으므로,
  날짜 범위가 부분집합이어도 section-4/5가 필요로 하는 세부 단위를 section-3 응답에서 뽑아낼
  방법이 없다. 따라서 각 섹션이 독립적으로 호출을 유지한다.

### 3. `list_promotions` 중복 호출 — **적용 대상 없음**

이 스킬은 원래부터 `list_promotions`를 **section-3에서 딱 1회만** 호출하고, section-2
(Executive Summary)는 새 호출 없이 그 응답을 재사용한다. section-4/5는 `list_promotions`를
아예 쓰지 않는다. 즉 통합할 중복 호출이 처음부터 없었다 — `daily-summary`처럼 3회→1회로 줄일
대상이 없다.

### 4. `chart.umd.min.js`(약 208KB) 인라인 방식 변경

`daily-summary`와 동일한 이유·동일한 방식으로 변경했다 — 매 리포트마다 모델이 208KB를
자기 출력 텍스트로 재생성하는 대신, 저장 폴더에 이미 파일이 있으면 건너뛰고 없을 때만 1회
복사한 뒤 `<script src="chart.umd.min.js"></script>` 상대 경로로 참조한다. CSP로 상대 경로
로드가 막힌 호스트(Artifact 등)에서만 `{CHART_JS_INLINE}` 인라인을 최후 수단으로 쓴다.
자세한 안전성 근거(classic `<script src>`의 `file://` CORS 미적용 등)는 `daily-summary/
CLAUDE.md`의 해당 항목을 그대로 따른다 — 이 스킬 전용으로 새로 조사한 내용은 없다.
**영향받은 파일**: `SKILL.md`(6/7단계, 보고서 골격의 `<head>` 부분). 이 스킬은 이미
`assets/chart.umd.min.js`를 갖고 있었으므로 새로 자산을 추가할 필요는 없었다.

### 5. MCP 응답을 스크래치패드 JSON에 저장했다가 다시 읽는 패턴 금지

`daily-summary`와 동일한 지침을 SKILL.md에 추가했다 — 이 스킬도 서브에이전트를 쓰지 않으므로
중간 파일 저장이 애초에 불필요하다.

### 6. 병렬 호출 지침 추가 (정확한 프레이밍으로 처음부터 작성)

이 스킬에는 원래 "병렬 호출 지침" 섹션 자체가 없었다(daily-summary는 있었지만 한 번 잘못된
주장을 했다가 같은 날 실측으로 정정한 이력이 있다). 처음부터 `daily-summary`의 **정정된**
프레이밍을 그대로 가져와 작성했다 — 배치는 "턴 오버헤드 제거" 효과만 있고 네트워크 레벨 진짜
동시 실행이 보장되지 않는다는 점을 명시했다. 진짜 속도 개선은 위 1번(호출 총 개수 축소)에서
나온다는 점도 동일하게 서술한다.

## 아직 적용 안 한 후보 (추가 조사/논의 필요)

- `get_target_progress_v2` 3회(media=google/meta/naver) 호출을 1회로 합치는 것 — `daily-summary`
  와 동일한 이유로 보류한다(도구 스키마가 `media`를 필수 enum으로 요구해 생략 불가능, 백엔드
  스키마 변경 필요, 매체별 메시지 포맷 차이로 로직 복잡화 우려). 자세한 내용은
  `daily-summary/CLAUDE.md`의 해당 항목 참고.
- section-5의 google/meta/naver 통합 호출과 airbridge 호출을 더 줄이는 방법 — 현재 구조상
  `group_by`가 다르면 하나로 합칠 수 없다는 것이 확인된 한계다. 백엔드가 `group_by`를
  매체별로 다르게 지정할 수 있는 새로운 파라미터 형태를 지원하지 않는 한 추가 축소는 어렵다.
