# monthly-summary 성능 최적화 변경 이력

`daily-summary`에서 검증된 최적화를 `monthly-summary`에 구조적으로 적용 가능한 범위에서
그대로 이식한 작업 기록. `daily-summary/CLAUDE.md`와 동일한 형식 — 새 최적화를 적용할 때마다
**날짜 + 무엇을 + 왜 + 검증 방법**을 추가한다.

## 2026-08-09

### 1. `media` 파라미터 생략으로 다중 호출 → 단일 호출 통합

- **무엇**:
  - section-1의 매출 실적(`get_ad_performance_monthly_table`, media=airbridge, 당월 1개월)과
    no-budget fallback 소진액(media별 3회 조건부 호출, `group_by:"total"`)을 **`media` 생략
    1회 호출**(`group_by:"media"`)로 통합 — daily-summary의 section-1과 완전히 동일한 패턴.
  - section-3의 매체별 4회 호출(google/meta/naver `group_by:"total"` + airbridge
    `group_by:"media"`, 5개월 전~당월)을 **`media` 생략 1회 호출**(`group_by:"media"`)로 통합.
  - section-4는 이제 별도 호출을 하지 않고 section-3의 공유 응답(airbridge 행 전체)을 재사용.
  - section-5(전월 vs 당월 매체 비교, 4회 호출)도 이제 별도 호출을 하지 않고 section-3의 공유
    응답을 재사용 — section-5가 필요로 하는 범위("전월~당월", 2개월)가 section-3의 범위
    ("5개월 전~당월", 6개월) 안에 항상 완전히 포함되므로, 그 응답에서 M-1/M0 두 달치 행만
    골라 쓴다.
- **왜**: daily-summary에서 이미 실측 검증된 사실 — `media`를 생략하면 `get_ad_performance_
  monthly_table`이 google/meta/naver/airbridge 등 등록된 모든 매체를 한 응답에 함께 반환한다
  (laighthouse-prism `v2_ad_performance.py`가 `media` 미지정 시 내부적으로 모든 `DataSource`를
  순회하는 구조 — 브랜드/기간에 의존하지 않는 일반 동작이므로 monthly-summary에도 동일하게
  적용 가능). daily-summary와 달리 `daily-summary`는 `get_ad_performance_daily_table`을 쓰고
  `monthly-summary`는 `get_ad_performance_monthly_table`을 쓰지만, 두 도구 모두 같은
  `v2_ad_performance.py` 로직을 공유하므로 `media` 생략 시의 "전체 매체 반환" 동작이 동일하게
  성립한다.
- **검증**: 별도 재실측(라이브 MCP 호출)은 하지 않았다 — daily-summary에서 이미 같은 도구
  계열(`get_ad_performance_*_table`)에 대해 `media` 생략 응답과 매체별 분리 호출 응답의 값이
  완전히 동일함을 직접 대조 확인했고(2026-07-23~29, 2026-07-29, 2026-07 각각), 그 검증이
  성립하는 근거(`v2_ad_performance.py`의 `media` 미지정 시 동작)가 daily/monthly 테이블
  공통이므로 동일 결론이 적용된다고 판단함. **다만 실제 프로덕션 데이터로 재확인은 권장** —
  특히 6개월 범위처럼 여러 달에 걸친 `group_by:"media"` 응답이 daily-summary가 확인한 "매체당
  이미 합산된 한 줄"이 "매체당 월별로 합산된 여러 줄"로 정확히 확장되는지는 구조적 추론이며
  라이브 호출로 직접 재현하지는 않았다.
- **영향받은 파일**: `monthly-summary-section-1-target-achievement.md`,
  `monthly-summary-section-3-monthly-ad-performance.md`,
  `monthly-summary-section-4-revenue-trend.md`,
  `monthly-summary-section-5-channel-performance.md`, `SKILL.md`.
- **결과**: 데이터 호출이 `get_target_progress_v2` 3회(불변) + `get_ad_performance_monthly_table`
  2회(둘 다 media 생략: section-1용 1회 + section-3/4/5 공유 1회) + `list_promotions` 1회 =
  총 **6회**로 줄었다 (예전에는 section-1 조건부 fallback 최대 3회 + section-3 4회 +
  section-4 1회 + section-5 4회까지 포함해 최대 17회 이상).

### 2. `list_promotions` 호출 개수 — 변경 없음

- **무엇**: 적용하지 않음.
- **왜**: `daily-summary`는 section-2/3/4가 각각 `list_promotions`를 호출해 중복이 있었지만,
  `monthly-summary`는 section-2 한 곳에서만(30일 룩백) `list_promotions`를 호출한다 —
  공유하거나 중복 제거할 다른 호출이 애초에 없다. 조사 결과 손댈 것이 없다는 결론.

### 3. `chart.umd.min.js`(약 208KB) 인라인 방식 변경

- **무엇**: `daily-summary`와 동일하게, SKILL.md 6/7단계와 보고서 골격의 `<head>`를 "이미
  존재하면 건너뛴다 → 없을 때만 폴더에 1회 복사 → `<script src="chart.umd.min.js">`(상대
  경로) 참조"로 재작성했다. CSP로 상대 경로 로드가 막힌 호스트(Artifact 등)에서만
  `{CHART_JS_INLINE}` 치환을 최후 수단으로 남겼다. Artifact도 `show_widget`도 없는 호스트는
  "채팅 내부 표시" 사본 자체를 만들지 않는다.
- **왜**: 기존 `monthly-summary` SKILL.md는 매 리포트마다 208KB(약 5만 토큰)를 `{CHART_JS_
  INLINE}`에 그대로 삽입하는 방식이었다 — `daily-summary`가 최적화 전에 가졌던 것과 동일한
  구조였다. `daily-summary`에서 이미 "상대 경로 `<script src>` 로딩이 `file://`에서 CORS 없이
  정상 동작한다"는 근거를 확인했고(classic script tag는 ES 모듈/fetch와 달리 CORS 제약이
  없음), "전용 파일 복사 도구가 없어도 일반 파일 쓰기로 생애 첫 리포트 1회만 비용을 치르면
  이후 상각된다"는 설계도 검증됐다 — 이 두 근거 모두 `monthly-summary`에도 그대로 적용된다
  (`monthly-summary` 전용 가정이 아니라 호스트/파일시스템 레벨의 일반 사실이므로).
- **검증**: `daily-summary`에서 확인된 근거를 그대로 원용. `monthly-summary` 자체에 대한
  별도 실측(Desktop에서 실제 렌더링/시간 측정)은 daily-summary와 마찬가지로 Claude Code
  세션에서는 수행 불가 — 실제 Desktop 사용자가 확인해야 한다.
- **영향받은 파일**: `SKILL.md` (6/7/8단계, 보고서 골격의 `<head>` 부분).

### 4. MCP 응답을 스크래치패드 JSON에 저장했다가 다시 읽는 패턴 금지

- **무엇**: SKILL.md에 "MCP 응답을 파일로 저장했다가 다시 Read하지 않는다" 지침을 신규
  추가(기존에는 없었음).
- **왜**: `daily-summary`와 동일한 이유 — 이 스킬도 서브에이전트를 쓰지 않으므로 중간 파일
  저장 자체가 불필요하다.

### 5. 병렬 호출 지침 신규 추가

- **무엇**: SKILL.md에 "서로 의존하지 않는 MCP 호출은 한 메시지에서 동시에 발사한다" +
  "배치의 실제 효과는 턴 오버헤드 제거이지 네트워크 동시 실행이 아니다"라는 정정된(실측
  근거 있는) 프레이밍을 **처음부터** 정확하게 추가했다(기존에는 이 섹션 자체가 없었다).
- **왜**: `daily-summary`가 겪은 "먼저 낙관적으로 5배 효과를 주장했다가 실측으로 정정"하는
  과정을 반복할 필요가 없다 — 이미 daily-summary에서 실측 확인된 결론(배치 5회 8.65초 vs
  순차 5회 14.06초, 차이는 턴당 모델 지연분 정도)을 그대로 인용해 monthly-summary는 처음부터
  정확한 설명으로 시작한다.

## 적용하지 않은 항목 (검토했으나 구조적으로 부적합하거나 이미 최적)

- `get_target_progress_v2` 3회(media=google/meta/naver) 통합 — `daily-summary`와 동일한 이유로
  보류. 도구 스키마가 `media`를 필수 enum으로 요구해 생략 불가.
- naver 전용 도구(`get_naver_*`) — 이 스킬은 애초에 브리즘(airbridge 기반) 전용이라 naver 전용
  도구를 전혀 쓰지 않는다. "Google/Meta vs naver 분기" 자체가 이 스킬에는 없다 — SKILL.md에
  이미 naver 전용 도구를 쓰지 않는다고 명시돼 있다.
