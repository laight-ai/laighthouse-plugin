# render-report: mtd 병렬 서브에이전트 + 매핑 스크립트화 설계

**날짜:** 2026-07-24
**대상:** `plugins/laighthouse-analytics-prod/skills/render-report/` (mtd 우선, 검증 후 daily/monthly/executive-mtd 이식)

## 배경

`render-report` 스킬(v0.9.1)은 MCP 도구 호출 결과를 오케스트레이터(단일 대화 컨텍스트)가 순차적으로
받아, 섹션마다 LLM이 직접 docx 섹션 JSON을 작성한 뒤 `build.py`로 렌더링한다. mtd(11개 섹션) 기준
문제점:

1. **순차 처리** — 섹션마다 MCP 호출 → JSON 작성이 하나씩 이어져 벽시계 시간이 섹션 수에 비례해 늘어난다.
2. **컨텍스트 누적** — 이전 섹션들의 raw MCP 응답 + 생성된 JSON이 계속 컨텍스트에 남아, 뒤 섹션으로
   갈수록 한 스텝의 처리 시간과 토큰이 함께 늘어난다 (특히 키워드별 성과처럼 행이 많은 표).
3. **반복적 기계 변환** — 8개 DATA 섹션(1,2,4,6,7,9,10,11)의 "MCP 필드 → docx JSON 필드" 매핑은
   각 섹션 `.md` 파일에 값 하나하나 명시돼 있는 순수 기계적 작업인데도, 매번 LLM이 다시 판단해서
   포맷팅(천단위 콤마, ×100, diff 문자열 결합)을 반복한다.

목표: **시간/토큰 절약**, 단 **산출물(.docx 최종 렌더링 결과)은 현재와 동일해야 한다** — 이 스킬의
`데이터 처리 원칙`(MCP 데이터 그대로 렌더링, 임의 가공/재계산 금지)은 그대로 유지된다.

## 1. 섹션 그룹 분리 (mtd, 7개 그룹)

의존관계 기준으로 11개 섹션을 7개 독립 그룹으로 나눈다. ANALYSIS 섹션(3/5/8)은 텍스트 생성이 필요해
스크립트화 대상이 아니므로 그룹에서 제외하고, 대신 관련 그룹의 **digest**를 소비한다.

| 그룹 | 담당 섹션 (DATA) | MCP 호출 | digest 소비처 |
|---|---|---|---|
| A | 1+2 (월 목표 카드 + 목표 달성 현황, 항상 쌍) | `get_naver_target_progress` | 섹션3 |
| B | 4 (월별 광고 성과 차트) | `get_naver_monthly_ad_performance` | (없음) |
| C | 6 (일일 카테고리별 매출) + 6.1(참조용, 비노출) | `get_naver_item_sales_daily`, `get_naver_category_sales` | 섹션3, 섹션5 |
| D | 7 (매체별 예산 소진 현황) | `get_naver_channel_budget_progress` | 섹션3 |
| E | 9 (캠페인별 성과) | `get_naver_campaign_performance` | 섹션8 |
| F | 10 (광고그룹별 성과) | `get_naver_group_performance` | (없음) |
| G | 11 (키워드별 성과) | `get_naver_keyword_performance` | (없음) |

## 2. 병렬 디스패치 메커니즘

오케스트레이터(메인 대화)는 7개 그룹을 **Agent 도구로 한 메시지 안에서 동시에** 호출한다
(`general-purpose` 서브에이전트 — MCP 도구와 Bash 접근이 모두 필요하므로). 각 서브에이전트는:

1. 그룹에 필요한 MCP 도구를 호출한다 (그룹 내 여러 도구면 순서대로, 그룹 자체는 병렬).
2. raw 응답을 스크래치패드 임시 파일에 그대로 저장한다 (가공 없이).
3. `python map_section.py --report-type mtd --group <A..G> --data <임시.json> --out <out.json>`을
   실행한다 — 이 스크립트가 섹션 JSON(+digest)을 만든다.
4. `out.json`의 내용을 **자신의 최종 응답 텍스트로 그대로 반환**한다 (raw 데이터를 다시 풀어 설명하지
   않는다 — 오케스트레이터가 볼 것은 이 압축된 결과뿐).

오케스트레이터는 7개 결과가 모두 돌아오면:
- 각 그룹의 `sections[]`를 문서 순서(1,2,4,6,7,9,10,11)대로 정렬해 이어붙인다.
- digest를 모아 텍스트 섹션 3/5/8을 직접 작성한다 (기존 섹션 파일의 분석 항목 지침 그대로 따름).
- 최종 `{title, period, sections}` JSON을 조립해 지금과 동일하게 `build.py`를 호출한다.

이 구조로 순차 처리(문제 1)와 컨텍스트 누적(문제 2)이 동시에 해소된다 — raw 테이블은 각 서브에이전트
컨텍스트 안에서만 존재하고 소멸하며, 오케스트레이터는 압축된 결과만 누적한다.

## 3. 매핑 스크립트 (`map_section.py` + `section_mapping.py`)

`assets/docx_report/`에 `build.py`와 동일한 위상의 **고정 재사용 스크립트**로 추가한다 (스킬의
"실행 방식 절대 지침"에 이 스크립트도 예외로 등록).

- `section_mapping.py` — report_type/group별 순수 함수 (`map_mtd_group_a(data) -> {"sections":[...], "digest": {...}}` 등). 각 함수는 해당 섹션 `.md` 파일에 문서화된 필드 매핑을 그대로 코드로 옮긴 것이며,
  **매핑 규칙 자체를 스크립트 안에서 임의로 바꾸지 않는다** — `.md` 파일이 규칙의 단일 출처(source of
  truth)이고, 스크립트는 그 규칙의 실행기일 뿐이다.
- `map_section.py` — CLI 진입점. `--report-type`, `--group`, `--data`(raw MCP 응답 JSON), `--out`
  인자를 받아 `section_mapping.py`의 해당 함수를 호출하고 결과를 `--out`에 쓴다.
- 포맷팅 규칙(천단위 콤마, 비율 ×100, diff 문자열 조합)은 각 섹션 `.md`에 이미 명시된 그대로
  구현한다 — 새로운 반올림/재계산 규칙을 추가하지 않는다.
- **digest 스키마**: 그룹별로 다르지만, 공통적으로 "그 그룹의 표/차트에서 가장 눈에 띄는 값 1~3개"를
  숫자 그대로(포맷팅 전) 담는다. 예) 그룹 A digest: `{roas_actual_pct, roas_goal_pct, revenue_achievement_rate, budget_spent_rate}`. 텍스트 작성은 여전히 LLM(오케스트레이터)이 하므로, digest는
  "재료"만 제공하고 문장은 만들지 않는다.

## 4. 에러 처리

- 특정 그룹의 서브에이전트가 실패하거나 MCP가 빈 응답/에러를 반환하면, 그 그룹의 섹션은 기존 규칙대로
  `{ "type": "text", "heading": "...", "body": "데이터 준비 중" }`으로 대체한다 — 다른 그룹의 성공
  여부와 무관하게 항상 11개 섹션 전부가 자리한다.
- digest가 없으면(그룹 실패) 해당 항목은 텍스트 섹션 작성 시 건너뛴다 (임의로 지어내지 않는다 — 기존
  "데이터 부족 시" 원칙 유지).

## 5. 검증 방법 (산출물 불변 확인)

1. **단위 테스트**: 각 섹션 `.md` 파일에 이미 있는 리터럴 예시 응답을 golden fixture로 사용해
   `section_mapping.py`의 각 함수가 `.md`의 `## DOCX 섹션` 예시와 동일한 구조의 JSON을 만드는지
   `pytest`로 검증한다. `build.py`/`sections.py`/`charts.py`는 이번 변경에서 손대지 않으므로, 매핑
   결과 JSON이 기존과 동일하면 최종 docx도 동일하다.
2. **회귀 테스트**: 기존 `tests/test_build.py`/`test_sections.py`/`test_charts.py`가 그대로 통과하는지
   확인한다.
3. **실제 사용 검증**: mtd 실제 브랜드로 스킬을 한 번 실행해 병렬 디스패치가 정상 동작하고 문서가
   깨지지 않는지 확인한다 (이 단계는 사용자 환경의 MCP 인증에 의존하므로, 스크립트 레벨 검증을 먼저
   완료한 뒤 진행한다).

## 6. 범위 및 롤아웃

이번 작업은 **mtd만** 구현하고 검증한다. 통과하면 동일 패턴(그룹 분리 → 매핑 함수 → 병렬 디스패치 →
digest 기반 텍스트 작성)을 daily/monthly/executive-mtd에 순서대로 이식한다 — report_type마다 섹션
구성과 텍스트 섹션 개수가 다르므로 그룹 분리표는 report_type별로 새로 만든다.
