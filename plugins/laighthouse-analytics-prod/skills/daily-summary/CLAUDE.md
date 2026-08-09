# daily-summary 성능 최적화 변경 이력

`daily-summary` 리포트 생성 시간을 8분대 → 3분대(Claude Desktop 채팅 기준)로 줄이기 위한
작업 기록. 새로운 최적화를 적용할 때마다 이 파일에 **날짜 + 무엇을 + 왜 + 검증 방법**을
추가한다 — 나중에 회귀가 생기면 어떤 변경이 원인인지 추적하기 위함.

## 2026-08-09

### 1. brand-access 캐싱 (laighthouse-prism 백엔드)
- **무엇**: `resolve_brand_access`(MCP 도구 호출마다 auth-service에 HTTP 2회 왕복)에 30초
  TTL 캐시 추가 (`(token, brand_name)` 키). 실패 응답은 캐싱 안 함.
- **왜**: 리포트 1건당 13회 이상 같은 브랜드에 대해 반복 호출되는데, 매번 왕복 2회씩 나가고
  있었음 (~26회 왕복).
- **검증**: laighthouse-prism `tests/mcp_server/test_permissions.py` — 캐시 히트/토큰 격리/
  실패 미캐싱/TTL 만료 테스트. 커밋 `c196a78`.

### 2. SKILL.md 병렬 호출 지시 추가 → 이후 실측으로 정정
- **무엇**: 독립적인 MCP 호출을 한 메시지에서 동시에 발사하도록 지시 추가.
- **왜**: 순차 호출 시 턴마다 모델 사고 시간 + 브랜드 권한 확인 왕복이 누적됨.
- **⚠️ 같은 날 실측으로 밝혀진 사실**: 배치해도 MCP 호출 자체가 네트워크 레벨에서 진짜
  동시 실행되는 게 아니라는 근거를 확인함 — 배치 5회 호출(8.65초) vs 완전 순차 5회
  호출(각각 별도 턴, 14.06초) 비교 결과, 5배가 아니라 "턴당 모델 지연(약 1초/호출)"만큼만
  줄었다. Anthropic 공식 문서도 "API가 실행 순서(동시/순차)를 강제하지 않으며 클라이언트
  구현에 달려 있다"고 명시 — 이 환경은 사실상 순차 처리로 보인다. **결론**: 배치는 "턴 오버헤드
  제거" 효과만 있고 공짜 이득이라 유지하지만, 실제 속도 개선의 핵심은 호출 총 개수를 줄이는
  것(아래 3번)이다.

### 3. `media` 파라미터 생략으로 다중 호출 → 단일 호출 통합
- **무엇**:
  - section-1의 매출 실적(`get_ad_performance_monthly_table`, media=airbridge)과 no-budget
    fallback 소진액(media별 3회 조건부 호출)을 **`media` 생략 1회 호출**로 통합 — 이 호출
    하나가 google/meta/naver/airbridge 행을 전부 반환한다는 것을 실측 확인.
  - section-3의 매체별 4회 호출(google/meta/naver `group_by:"total"` + airbridge
    `group_by:"media"`)을 **`media` 생략 1회 호출**로 통합.
  - section-4/5는 이제 별도 호출을 하지 않고 section-3의 공유 응답을 재사용(section-4는
    airbridge 행 전체, section-5는 마지막 이틀만).
- **왜**: 배치를 해도 호출 자체는 순차 처리되므로(위 2번), 턴을 줄이는 것보다 **호출 총
  개수를 줄이는 것**이 실제 속도에 더 직접적으로 기여한다. 데이터 호출이 17회 이상 →
  6회(모두 한 배치)로 줄었다. 목표 판정(no-budget) 여부를 기다리는 조건부 2차 라운드도
  완전히 제거됨 — 이제 항상 6개를 한 번에 낸다.
- **검증**: 로컬 prism-local MCP 서버에 대해 `media` 생략 응답과 기존 매체별 분리 호출
  응답의 값을 직접 대조 — 2026-07-23~29 전체 범위, 2026-07-29 단일 날짜, 2026-07 월간 데이터
  모두 완전히 동일한 수치 확인 (예: 2026-07-23 google cost=92,333, meta cost=5,132,393,
  naver cost=156,158 — 분리 호출/통합 호출 양쪽 동일). 결과값이 바뀌지 않는다는 사용자
  전제조건 충족.
- **영향받은 파일**: `daily-summary-section-1-target-achievement.md`,
  `daily-summary-section-3-daily-performance-7days.md`,
  `daily-summary-section-4-daily-revenue-7days.md`,
  `daily-summary-section-5-channel-performance.md`, `SKILL.md`.

### 4. `list_promotions` 3회 → 1회 공유 호출
- **무엇**: section-2(7일 룩백)/section-3(6일 룩백)/section-4(6일 룩백)가 각자 부르던
  `list_promotions`를, 가장 넓은 범위(7일 룩백)로 통일해 section-2가 1회만 호출하고
  section-3/4가 재사용하도록 변경.
- **왜**: section-3/4가 필요로 하는 범위는 section-2의 7일 범위 안에 완전히 포함되고, 각
  섹션의 인덱스 clamp 로직이 범위 밖 항목을 자동으로 걸러내므로 결과에 영향이 없다.
- **영향받은 파일**: 위 3번과 동일한 3개 섹션 파일.

### 5. MCP 응답을 스크래치패드 JSON에 저장했다가 다시 읽는 패턴 금지
- **무엇**: SKILL.md에 "MCP 응답을 파일로 저장했다가 다시 Read하지 않는다 — 그 턴의
  컨텍스트에서 바로 참조해서 쓴다"는 지침 추가.
- **왜**: 사용자가 실제 실행에서 이 패턴이 시간/토큰을 낭비하는 것을 관찰함. `render-report-docx`의
  서브에이전트+`map_section.py` 패턴과 달리, `daily-summary`는 서브에이전트를 쓰지 않으므로
  중간 파일 자체가 불필요하다.

### 6. `chart.umd.min.js`(208KB) 인라인 방식 변경 — 가장 유력한 숨은 병목
- **무엇**: 기존에는 매 리포트마다 모델이 이 파일을 Read해서 그 내용 전체(약 5만 토큰)를
  자기 응답/tool call 인자에 그대로 옮겨 적어야 했다. 이제:
  - 로컬 파일 저장본은 `chart.umd.min.js`를 저장 폴더에 **파일 그대로 한 번만 복사**해두고
    `<script src="chart.umd.min.js">`(상대 경로)로 참조 — 모델이 바이트를 다시 타이핑하지
    않는다.
  - Artifact처럼 CSP로 상대 경로 로드가 막힌 호스트에서만, 그리고 텍스트 재생성이 아닌
    도구(파일 복사/치환)가 없을 때만 최후 수단으로 기존 인라인 방식을 쓴다.
  - Artifact도 `show_widget`도 없는 호스트(Claude Desktop 채팅 자체)는 인라인이 필요한
    "채팅 내부 표시" 사본 자체를 만들지 않는다 — 저장 파일 하나면 충분.
- **왜**: 208KB ≈ 5만 토큰을 매 리포트마다 출력 토큰으로 새로 생성하는 것은 (Claude Desktop
  채팅 기준) 전체 소요 시간의 상당 부분을 차지할 것으로 추정됨 — 아직 실측 완료 전이지만,
  가장 유력한 단일 병목으로 지목되어 우선 수정함.
- **✅ 상대 경로 로딩 자체의 안전성은 조사로 확인함(2026-08-09)**: classic `<script src="...">`
  (Chart.js UMD 빌드가 정확히 이 방식 — `type="module"`이 아님)는 `file://`로 연 로컬 HTML에서도
  CORS 없이 정상 동작한다 — CORS null-origin 차단은 ES 모듈/`fetch`/`XHR`에만 적용되고
  classic script 태그의 로컬 상대경로 로딩은 브라우저가 오래전부터 지원하는 표준 동작이다.
  따라서 이 부분은 추측이 아니라 근거 있는 변경이다.
- **⚠️ 그래도 실측 필요한 부분(Desktop 전용, Claude Code에서는 검증 불가)**: (1) Claude
  Desktop에 연결된 MCP 서버가 실제로 "파일을 그대로 복사"하는 동작을 지원하는지(지원 안
  하면 SKILL.md의 fallback인 기존 인라인 방식으로 빠짐 — 이 경우 이번 수정의 효과가 없음),
  (2) 저장된 HTML을 실제로 열었을 때 차트가 정상 렌더링되는지, (3) 실제 리포트 생성
  총 소요 시간이 목표(3분) 안에 들어오는지. 이 세 가지는 Desktop에서 직접 실행해봐야만 알 수
  있다 — Claude Code 세션에서는 Desktop을 구동/측정할 방법이 없다.
- **영향받은 파일**: `SKILL.md` (6/7단계, 보고서 골격의 `<head>` 부분).

## 아직 적용 안 한 후보 (추가 조사/논의 필요)

- `get_target_progress_v2` 3회(media=google/meta/naver) 호출을 1회로 합치는 것 — 현재 도구
  스키마가 `media`를 필수 enum으로 요구해 `media` 생략이 불가능함. 백엔드 스키마 변경이
  필요하며, 매체별로 메시지 포맷이 달라 로직이 복잡해질 수 있어 별도 검토 필요.
- 스킬을 자연어 지시 대신 스크립트(코드 실행)로 전환하는 방식 — Claude Code 문서에서
  권장하는 일반적 기법이나, Claude Desktop이 코드 실행/파일 복사 도구를 지원하는지 확인
  안 됨. 지원 확인되면 MCP 호출 결과 가공 + HTML 템플릿 조립을 스크립트로 옮겨 모델이
  대용량 텍스트를 직접 생성하는 지점을 추가로 줄일 수 있음.
