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

## 2026-08-09 (추가) — 3번 항목 되돌림: chart.umd.min.js 항상 인라인으로 복귀

- **무엇**: 위 3번에서 도입한 "이미 존재하면 건너뛴다 → 없을 때만 폴더에 1회 복사 →
  `<script src="chart.umd.min.js">`(상대 경로) 참조" 방식을 **전부 되돌렸다**. SKILL.md
  6단계와 보고서 골격의 `<head>`를 다시 "항상 `{CHART_JS_INLINE}` 자리에 파일 전체 내용을
  인라인"하는 원래 방식으로 복원했다. CDN `<script src>`를 쓰지 않는다는 경고(항상 옳았고 이
  변경과 무관)는 그대로 유지했다.
- **왜**: 실사용에서 실패가 실측 확인됐다 — 같은 날(2026-08-09) sibling 스킬
  `creative-detailed`의 실제 실행에서, 리포트가 샌드박스 출력 디렉터리(`/mnt/user-data/
  outputs/`)에 저장됐고, 플랫폼 프리뷰가 리포트 HTML과 `chart.umd.min.js`를 **서로 다른 두
  개의 다운로드 가능 아티팩트**로 분리해서 보여줬다. 그 결과 상대 경로 `<script src="chart.
  umd.min.js">`가 로드되지 않아 **모든 차트가 깨지거나 빈 화면**으로 나왔다. 3번 항목이
  근거로 든 "classic `<script src>`는 `file://`에서 CORS 제약 없이 정상 동작한다"는 로컬
  브라우저에서 HTML 파일을 직접 여는 경우엔 맞지만, 이 샌드박스/호스팅 프리뷰 메커니즘에는
  적용되지 않는다는 것이 이번에 밝혀졌다. 토큰/시간 절감보다 차트가 실제로 렌더링되는 것이
  우선이므로("깨진 보고서" > "느린 보고서"), 호스트를 가리지 않고 항상 인라인하는 쪽으로
  되돌린다.
- **검증**: `creative-detailed`의 2026-08-09 실제 실행에서 차트가 깨지는 것을 직접 관찰함.
- **영향받은 파일**: `SKILL.md` (6단계, 보고서 골격의 `<head>` 부분 및 그 위의 CDN 경고
  콜아웃).
- **비용은 수용**: 리포트당 ~5만 토큰(208KB) 인라인 비용은 현재 그대로 감수한다. 미래에
  호스트 능력을 감지해서 분기하는 방식이나 더 작은 차팅 라이브러리로 교체하는 방향을 검토할
  수는 있지만, **둘 다 아직 구현되지 않았다** — 지금은 항상 인라인이 유일한 동작이다.

## 2026-08-11 — daily-detailed의 세 가지 개선 검토 후 적용 가능한 것만 이식

`daily-detailed`에서 최근 적용한 세 가지 성능/신뢰성 개선(중간 파일 금지의 조합 단계 확장,
스켈레톤 선(先) 게시의 필수 체크포인트 승격, group_by=campaign/ad 조인 비교표의 asset 스크립트
이관)을 `monthly-summary`에도 그대로 복사하지 않고, 이 스킬의 실제 구조를 먼저 확인한 뒤
해당되는 것만 적용했다.

### 1. 중간 파일 생성 금지를 "섹션 HTML 조합 단계"까지 명시적으로 확장

- **무엇**: § 실행 방식 절대 지침의 스크립트 파일 생성 금지 문구를 daily-detailed와 동일한
  형식으로 확장했다 — "이 금지는 데이터 집계 단계에만 적용되는 게 아니라 섹션 HTML을 조합하는
  단계에도 동일하게 적용된다"는 문장과, 금지 대상의 구체적 예시(`section2.html`,
  `section4_rows.json`, `final_report.html` 같은 섹션별 조각/중간 스테이징 파일)를 추가했다.
  "최종 저장 시점에 딱 한 번만 Write한다"는 문장도 명시했다.
- **왜**: 기존 문구는 "별도 스크립트·노트북 파일을 생성하지 않는다"만 명시하고 있어, 실제
  실행에서 이를 "데이터 집계"에만 적용되는 것으로 좁게 해석하고 섹션 HTML 조합 단계에서
  중간 파일을 만드는 위반이 daily-detailed에서 실측 관찰됐다(`gen_section4.py`류 스크립트를
  만들고 실행·수정·재실행). monthly-summary는 daily-detailed와 동일하게 서브에이전트 없이
  오케스트레이터가 직접 MCP를 호출하고 HTML을 조합하는 구조라 같은 위반 경로가 구조적으로
  동일하게 존재한다 — 스킬 고유의 예외적 사정이 없어 그대로 적용 가능하다고 판단했다.
- **검증**: daily-detailed에서 실측된 실패 사례를 근거로 인용. monthly-summary 자체에서 이
  위반이 재현되는지 별도 실측(라이브 실행)은 하지 않았다 — 문구 추가는 코드 실행이 아니므로
  `py_compile` 등 기계적 검증 대상이 아니다.
- **영향받은 파일**: `SKILL.md` (§ 실행 방식 절대 지침).

### 2. 스켈레톤 선(先) 게시를 "권장 안내문"에서 "번호 붙은 필수 체크포인트"로 승격

- **무엇**: 기존 § 실행 방식 절대 지침 아래 별도 안내문("⏱ 긴 대기 없이 스켈레톤을 먼저
  보여준다")으로만 존재하던 문구를 삭제하고, § 실행 순서의 2단계(target/achievement 호출)
  직후에 번호 붙은 3단계로 재삽입했다("⏱ 필수 체크포인트 — ..."). 이후 이어지는 단계
  번호를 전부 다시 매겼다(옛 3→4, 4→5, 5→6, 6→7, 7→8, 8→9). 이 번호 변경에 맞춰
  `SKILL.md` 안의 다른 단계 참조("3단계 호출", "7단계", "6단계" 등)와
  `monthly-summary-section-4-revenue-trend.md`/`monthly-summary-section-5-channel-
  performance.md`의 "3단계에서 1회 호출한" 참조도 전부 새 번호로 갱신했다.
- **왜**: daily-detailed와 동일한 구조적 문제 — 안내문 형태로만 존재하면 번호 붙은 § 실행
  순서 목록을 따라가는 실행 흐름에서 완전히 생략되기 쉽다. daily-detailed에서 실제로 이게
  생략된 채 전체 보고서를 다 만든 뒤 한 번에 저장/게시하려다 툴호출 예산이 바닥나 사용자에게
  아무 결과도 못 보여준 사고가 실측 관찰됐다. monthly-summary도 서브에이전트 없이 5개 섹션을
  순차로 채우는 동일한 실행 패턴이라 같은 사고가 구조적으로 가능하다.
- **검증**: daily-detailed의 실측 사고 사례를 근거로 인용. 번호 재정렬 후 `SKILL.md` 전체를
  다시 grep해 `\d단계` 패턴의 모든 참조가 새 번호와 일치하는지, 그리고 § 실행 순서의
  번호 목록이 1~9로 끊김 없이 이어지는지 확인했다.
- **영향받은 파일**: `SKILL.md` (§ 실행 방식 절대 지침, § 실행 순서 전체),
  `monthly-summary-section-4-revenue-trend.md`, `monthly-summary-section-5-channel-
  performance.md`.

### 3. group_by=campaign/ad 조인 비교표의 asset 스크립트 이관 — 적용하지 않음

- **무엇**: 적용하지 않음.
- **왜**: `monthly-summary`의 모든 섹션을 조사한 결과, `get_ad_performance_monthly_table`
  호출은 전부 `group_by:"media"`(section-1/3, section-4/5는 section-3 응답 재사용)만 쓴다 —
  `group_by`가 `campaign`/`ad`/`ad-set`인 호출이 이 스킬에는 **전혀 없다**. daily-detailed의
  section-4/5가 쓰는 "D-1 vs D-0 조인 + 파생지표(CTR/CPA/ROAS) + 변화율 + 화살표 + 색상 +
  ₩10,000 필터 + 정렬 + `<tr>` HTML 생성" 패턴 자체가 monthly-summary에는 대응하는 섹션이
  없다 — section-5(매체 성과 비교)는 매체 5개 고정 행(Naver/Google/Meta/Organic/Others)
  비교이지 캠페인/광고 단위 조인 비교표가 아니다. "summary 계열은 detailed 계열보다 단순해서
  이런 세부 조인 비교표가 없을 수 있다"는 사전 가설이 실제로 맞았다. 새 asset 스크립트를
  만들 근거 자체가 없어 건너뛴다.
- **검증**: `SKILL.md`와 `monthly-summary-section-{1,3,4,5}.md`(section-2는 generic 도구를
  쓰지 않음) 전체에서 `group_by` 문자열을 grep해 전부 `"media"`뿐임을 직접 확인했다.

### 4. group_by가 campaign/ad인 응답의 media 생략/분리 재검토 — 적용하지 않음

- **무엇**: 적용하지 않음.
- **왜**: 3번과 동일한 이유 — 이 스킬에 `group_by`가 `campaign`/`ad`/`ad-set`인 호출이
  존재하지 않으므로, "카디널리티에 따라 media를 생략할지 매체별로 나눠 받을지"를 재검토할
  대상 자체가 없다. `monthly-summary`가 쓰는 유일한 `group_by` 값인 `"media"`는 매체
  개수만큼만 행이 늘어나는 가장 낮은 카디널리티라, 2026-08-09에 이미 실측 근거를 바탕으로
  `media` 생략 1회 호출(section-1: 1회, section-3/4/5 공유: 1회)로 통합이 완료되어 있고
  (위 2026-08-09 항목 참고), 이번에 다시 손댈 부분이 없었다.
- **검증**: 3번과 동일한 grep 결과로 확인.

## 적용하지 않은 항목 (검토했으나 구조적으로 부적합하거나 이미 최적)

- `get_target_progress_v2` 3회(media=google/meta/naver) 통합 — `daily-summary`와 동일한 이유로
  보류. 도구 스키마가 `media`를 필수 enum으로 요구해 생략 불가.
- naver 전용 도구(`get_naver_*`) — 이 스킬은 애초에 브리즘(airbridge 기반) 전용이라 naver 전용
  도구를 전혀 쓰지 않는다. "Google/Meta vs naver 분기" 자체가 이 스킬에는 없다 — SKILL.md에
  이미 naver 전용 도구를 쓰지 않는다고 명시돼 있다.
