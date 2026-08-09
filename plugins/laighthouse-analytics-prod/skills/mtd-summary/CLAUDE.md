# mtd-summary 성능 최적화 변경 이력

`daily-summary`(같은 플러그인, 형제 스킬)에 이미 적용·검증된 최적화를 `mtd-summary`에
구조적으로 맞는 부분만 이식한 기록. `daily-summary/CLAUDE.md`의 2026-08-09 항목을 참고해
작업했다. 새로운 최적화를 적용할 때마다 이 파일에 **날짜 + 무엇을 + 왜 + 검증 방법**을
추가한다.

## 2026-08-09

### 1. `media` 파라미터 생략으로 다중 호출 → 단일 호출 통합

- **무엇**:
  - section-1의 매출 실적(`get_ad_performance_monthly_table`, 당월 1개월, media="airbridge")
    호출과 no-budget fallback 소진액(media별 최대 3회 조건부 호출, `group_by:"total"`)을
    **`media` 생략 1회 호출**(`group_by:"media"`, 당월 1개월)로 통합.
  - section-3의 매체별 4회 호출(google/meta/naver `group_by:"total"` + airbridge
    `group_by:"media"`, 6개월 span)을 **`media` 생략 1회 호출**(`group_by:"media"`, 6개월
    span)로 통합.
  - section-4는 이제 별도 호출을 하지 않고 section-3의 공유 응답(6개월, airbridge 행)을
    그대로 재사용한다 — 예전 section-4의 단독 호출과 파라미터·범위가 완전히 동일했으므로
    그냥 중복 호출을 제거한 것이다.
  - section-5(전월~당월 2개월)도 이제 별도 호출을 하지 않고 section-3의 6개월 공유 응답에서
    마지막 2개월(M-1, M0)만 골라 쓴다 — section-5가 필요로 하는 범위가 section-3의 범위 안에
    완전히 포함되고, 두 섹션 모두 같은 `day_offset`(target_date.day)을 쓰므로 same-day MTD
    cut 전제도 동일하게 유지된다.
- **왜**: `daily-summary/CLAUDE.md`에서 이미 확인했듯, MCP 호출을 배치(한 메시지)로 묶어도
  실제로는 순차 처리되는 것으로 보이므로, 턴을 줄이는 것보다 **호출 총 개수를 줄이는 것**이
  실제 속도에 더 직접적으로 기여한다. 이 스킬의 데이터 호출은 최악의 경우(모든 매체가
  no-budget일 때) `get_target_progress_v2` 3회 + 매출실적 1회 + fallback 3회 + section-3
  4회 + section-4 1회 + section-5 4회 + `list_promotions` 1회 = **17회**였으나, 이제
  `get_target_progress_v2` 3회 + section-1용 1회 + section-3/4/5 공유 1회 +
  `list_promotions` 1회 = **6회**로 줄었다.
- **검증**: `media` 생략 시 도구가 등록된 모든 매체를 한 응답에 반환한다는 동작은
  `daily-summary`에서 로컬 prism-local MCP 서버에 대해 실측 검증됐고(2026-07-23~29 범위,
  2026-07-29 단일 날짜, 2026-07 월간 데이터 모두 분리 호출/통합 호출 값 완전 일치), 이 동작은
  `v2_ad_performance.py`가 `media` 미지정 시 `DataSource` 전체를 순회하는 일반 구현이라
  브랜드·report_type에 의존하지 않는다(작업 지시서 근거). `mtd-summary`가 쓰는
  `group_by:"media"` 케이스는 `daily-summary` section-1/3이 쓰던 것과 동일한 조합이므로 별도
  브랜드 특화 검증 없이 안전하게 이식 가능하다고 판단했다.
  - section-4/5의 "공유 응답 재사용이 기존 단독 호출과 동일한 결과를 낸다"는 주장은 파라미터
    비교로 검증했다: section-4의 기존 단독 호출은 `media="airbridge"`, `group_by:"media"`,
    `start_month`=5개월 전, `end_month`=당월, `day_offset`=target_date.day였고, 이는 section-3의
    새 통합 호출(media 생략, 나머지 파라미터 동일)이 반환하는 airbridge 행과 **글자 그대로
    동일한 요청 파라미터**다(media 생략은 필터를 제거할 뿐, airbridge 행 자체의 계산 로직을
    바꾸지 않는다). section-5도 마찬가지로, 기존 4회 호출(2개월 span)의 각 매체 파라미터가
    section-3의 6개월 호출과 `media`를 제외한 모든 파라미터(같은 `day_offset`)가 동일하고,
    2개월 범위가 6개월 범위의 부분집합이므로 필터링만으로 동일한 결과를 얻는다.
- **영향받은 파일**: `mtd-summary-section-1-target-achievement.md`,
  `mtd-summary-section-3-monthly-ad-performance.md`,
  `mtd-summary-section-4-revenue-trend.md`, `mtd-summary-section-5-channel-comparison.md`,
  `SKILL.md`.

### 2. `list_promotions` 중복 호출 없음 — 적용 대상 아님

`mtd-summary`는 `list_promotions`를 section-2(Executive Summary)에서 **단 한 번**만
호출한다(30일 룩백). 다른 섹션은 이 도구를 쓰지 않으므로 `daily-summary`에서 한 "3회→1회
공유 호출" 통합은 애초에 적용할 대상이 없다.

### 3. `chart.umd.min.js`(약 208KB) 인라인 방식 변경

- **무엇**: `daily-summary/CLAUDE.md` 6번 항목과 완전히 동일한 방식으로 변경 — SKILL.md의
  6단계를 "이미 있으면 건너뛴다 → 없을 때만, 전용 파일 복사 도구가 있으면 그걸로, 없으면
  일반 파일 쓰기 도구로라도 1회 생성한다"로 재작성하고, 저장 파일의 `<head>`는
  `<script src="chart.umd.min.js"></script>` 상대 경로를 기본으로 쓰도록 바꿨다. CSP로 상대
  경로 로드가 막힌 호스트(Artifact 등)에서만 `{CHART_JS_INLINE}` 치환을 최후 수단으로
  유지한다. 7/8단계도 `daily-summary`처럼 "Artifact/`show_widget` 있는 호스트에서만 채팅 내부
  표시, 파일 저장은 모든 호스트에서 항상"으로 분리했다.
- **왜**: `daily-summary`에서 이미 이 부분이 "보고서가 느린 가장 유력한 원인 중 하나"로
  지목되어 수정됐고, classic `<script src>`가 `file://`에서 CORS 제약 없이 동작한다는 근거도
  이미 조사·확인됐다(브랜드/report_type에 의존하지 않는 브라우저 표준 동작). `mtd-summary`도
  같은 Chart.js UMD 빌드를 같은 방식(정적 HTML, 로컬 파일 저장)으로 쓰므로 동일한 최적화가
  그대로 적용된다.
- **적용하지 않은 것**: `assets/report-scaffold.html`(스킬 폴더의 실제 자산 파일) 자체는
  수정하지 않았다 — `daily-summary`의 동일 파일도 이번 최적화에서 건드리지 않은 채
  `{CHART_JS_INLINE}` 플레이스홀더를 그대로 유지하고 있다(SKILL.md에 임베드된 골격만 실제
  렌더링 시 쓰이는 것으로 보이며, `report-scaffold.html`은 SKILL.md 어디에서도 참조되지 않는
  것을 확인했다). 형제 스킬과 동일하게 다루기 위해 이 파일은 그대로 뒀다 — 필요하다면 별도
  작업으로 정리한다.

### 4. MCP 응답을 스크래치패드 JSON에 저장했다가 다시 읽는 패턴 금지

- **무엇**: `mtd-summary`에는 이 규칙이 없었다(실행 방식 절대 지침에 "별도 스크립트/노트북
  생성 금지"는 있었지만 "응답을 파일로 저장 후 재-Read 금지"는 명시돼 있지 않았음). 새로
  추가된 "병렬 호출 지침" 섹션 마지막에 `daily-summary`와 동일한 문구로 추가했다.
- **왜**: `daily-summary`에서 실제 실행 관찰로 확인된 시간/토큰 낭비 패턴이며, `mtd-summary`도
  서브에이전트를 쓰지 않는 동일 구조(오케스트레이터가 MCP를 직접 호출)이므로 같은 이유가
  그대로 적용된다.

### 5. 병렬 호출 지침 섹션 신설

- **무엇**: `mtd-summary`에는 "병렬 호출 지침" 섹션 자체가 없었다(실행 순서 다음에 바로
  완료 메시지 형식으로 넘어갔음). `daily-summary`의 병렬 호출 지침을 이식해 새 섹션으로
  추가했다 — "배치는 턴 오버헤드 제거 효과만 있고 네트워크 동시 실행이 보장되지 않는다"는
  2026-08-09 실측 정정 내용을 처음부터 정확하게 반영했다(사실이 아닌 것으로 이미 밝혀진
  "진짜 병렬 실행"이라는 표현은 쓰지 않았다).
- **section-1의 1개월 호출을 section-3의 6개월 호출에 합치지 않은 이유(의도적 비적용)**:
  이론적으로는 section-1이 필요로 하는 당월 데이터가 section-3의 6개월 응답에도 포함돼
  있어 하나로 합칠 수 있어 보이지만, 그렇게 하면 section-1(목표 달성 현황, 첫 스켈레톤
  렌더링에 필요)이 더 무거운 6개월 조회가 끝날 때까지 기다려야 해서 "실행 방식 절대 지침"의
  "2단계 응답을 받는 즉시 스켈레톤을 먼저 보여준다" 목표와 어긋난다. 따라서 두 호출을
  의도적으로 분리된 채 유지했다 — SKILL.md의 병렬 호출 지침 섹션에 이 트레이드오프를 명시해
  뒀다.

## 2026-08-09 (2)

### 6. `chart.umd.min.js` 상대 경로 `<script src>` 최적화를 인라인으로 롤백

- **무엇**: 위 3번 항목에서 도입한 "파일로 한 번 복사해두고 `<script src="chart.umd.min.js">`
  상대 경로로 참조" 방식을 완전히 되돌렸다. `SKILL.md`의 6단계(실행 순서)와 보고서 골격
  `<head>`의 CDN 경고 콜아웃을 모두 "항상 `{CHART_JS_INLINE}`에 파일 전체 내용을 인라인한다"로
  재작성했다 — "이미 존재하는지 확인 후 건너뛴다/없을 때만 1회 복사한다"는 분기 절차 자체를
  제거했다. 외부 CDN `<script src>`를 쓰지 않는다는 경고(항상 맞았고 이번 롤백과 무관)는 그대로
  유지했다.
- **왜**: 2026-08-09 실측으로 형제 스킬 `creative-detailed`를 실제로 돌려본 결과, 리포트가
  sandboxed `/mnt/user-data/outputs/` 프리뷰 환경에 저장됐을 때 플랫폼이 저장된 HTML과
  `chart.umd.min.js`를 **서로 다른 두 개의 다운로드 가능한 파일 아티팩트**로 취급했고, 상대
  경로 `<script src="chart.umd.min.js">`가 그 프리뷰 컨텍스트에서 sibling `.js` 파일을 정상
  로드하지 못해 **모든 차트가 깨진 채(빈 캔버스) 렌더링**됐다. "classic `<script src>`는
  `file://`에서 CORS 없이 정상 동작한다"는 기존 근거는 로컬 브라우저가 파일을 직접 여는
  경우에는 여전히 맞지만, 이 sandboxed/hosted 프리뷰 메커니즘은 sibling 상대 경로 파일을 같은
  방식으로 서빙/해석하지 않는 것으로 확인됐다 — 즉 host-conditional 분기의 전제 자체가
  이 호스트 유형에서 깨졌다. **차트가 실제로 렌더링되는 정확성이 토큰/속도 절감보다 항상
  우선한다** — 느리더라도 깨지지 않는 인라인 방식을 다시 기본값으로 삼는다. 토큰 비용
  (리포트 1건당 약 5만 토큰)은 현재로선 그냥 감수한다 — 아직 구현되지 않은 향후 개선 후보로
  host-capability 감지(호스트별로 상대 경로가 실제로 동작하는지 확인하는 방법이 생긴다면)나
  더 작은 차팅 라이브러리로 교체하는 방향이 있지만, 둘 다 지금은 구현되어 있지 않다.
- **영향받은 파일**: `SKILL.md` (실행 순서 6단계, 보고서 골격의 CDN 경고 콜아웃 + `<head>`
  스캐폴드).

## 적용하지 않은 항목 (그대로 유지)

- **`get_target_progress_v2` 3회 → 1회 통합**: `daily-summary/CLAUDE.md`의 "아직 적용 안 한
  후보"와 동일한 이유(도구 스키마가 `media`를 필수 enum으로 요구해 생략 불가, 백엔드 스키마
  변경 필요)로 이번에도 건드리지 않았다.
- **`get_naver_*` 전용 도구**: `mtd-summary`는 브리즘(airbridge 기반) 전용 스킬이라 애초에
  naver 전용 도구를 쓰지 않는다 — 적용 대상이 아니다.
