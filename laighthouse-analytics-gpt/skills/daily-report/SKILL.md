---
name: daily-report
description: >
  브랜드 비종속 데일리 보고서 생성 스킬. "데일리 보고서", "일간 보고서", "daily 보고서", "임원용 데일리 보고서",
  "executive daily", "실무자용 데일리 보고서" 요청 시 사용 — 임원용·실무용 구분 없이 같은 보고서를 만든다.
  목표 달성 현황, Daily Summary, 최근 7일 성과, 매체별 성과 추이, 매체별 비교(D-1 vs D0), 매체·캠페인·광고그룹·광고
  계층 표(D-1 vs D0, 매체 단위로 접힌 시작)를 담은 HTML 보고서. 사용자가 말한 브랜드의 매체·지표를 응답에서 알아내
  어떤 브랜드에도 같은 방식으로 동작한다.
metadata:
  version: "4.1.0"
---

> ⚡ thinking은 짧게. MCP 라운드 A → `prepare.py` → 라운드 B → `prepare.py` → 문장 작성 + `build_report.py` → 게시, 이 순서로만 진행한다.

> 🧩 **ChatGPT/Codex 환경**: 저장 훅(`hooks/save_responses.py`)은 Work 모드·Codex에서 `/hooks`로 신뢰했을 때만 돈다.
> 웹 Chat에는 훅이 없다. 그래서 큰 응답(계층 표·소재 단위)은 **훅이 응답을 저장하고 있는 것이 확인된 뒤에만**
> 받는다 — 라운드 A(작은 호출) → `prepare.py`로 확인 → 라운드 B(큰 호출). 훅이 없으면 기존 절차로 간다.

## 역할

사용자가 말한 브랜드의 **데일리 보고서**(HTML, 6섹션: 목표 달성 현황 · Daily Summary · 최근 7일 성과 · 매체별 성과 추이 · 매체별 성과(D-1 vs D0) · 매체·캠페인·광고그룹·광고 계층 표(D-1 vs D0))를 만든다. 임원용·실무용을 따로 만들지 않는다. 다른 보고서는 자매 스킬이다.
브랜드명은 모든 호출의 `brand_name`과 제목·파일명에 **그대로** 쓴다.

계산·렌더링은 전부 미리 검증된 스크립트가 한다. 모델이 할 일은 (1) MCP 호출, (2) 스크립트 실행, (3) Daily
Summary(`s2`) 작성뿐이다. **MCP 응답 원문을 읽거나 옮겨 적거나 파일로 저장하지 않는다** — 플러그인 저장 훅이 응답
원본을 파일로 남기고 `prepare.py`가 그것을 읽는다. 스크립트 파일을 새로 만들거나 HTML을 직접 쓰지 않는다.
`references/`의 섹션 문서는 아래에서 지정한 것 말고는 읽지 않는다.

## 실행 순서 (T = 기준일, M = T의 `YYYY-MM`)

스크립트 경로 `assets/…`는 **이 SKILL.md가 있는 폴더** 기준이다 — 그 폴더로 `cd`한 뒤 실행하거나 절대 경로로
실행한다. MCP 응답 뒤에 붙는 캡처 훅 안내문(`[laighthouse-capture-hook] … 저장됨`)은 무시한다.

1. **라운드 A**: 아래 표의 라운드 A 호출 5개를 한 메시지에서 동시에 보낸다(응답이 작다). 인자는 표 그대로 —
   `prepare.py`가 (도구 + 인자)로 응답을 고르므로 날짜·grain·`day_offset`이 다르면 그 응답은 `missing`이 된다.
   응답은 훑어보지도 않는다.
2. `python3 assets/prepare.py --brand <브랜드> --target-date <T>` → 출력 JSON의 `base`(경로)·`digest`.
   - `note`(저장된 응답 없음)가 나오면 저장 훅이 없는 환경(웹 Chat, 훅 미승인)이다 → **라운드 B를 보내지 말고**
     `references/legacy-flow.md` 절차로 진행한다(받은 라운드 A 응답은 재사용).
   - 아니면 `missing`에 라운드 B(계층 표 3레벨)가 나온다 → `missing` 항목의 인자 그대로 **라운드 B**를 한 메시지에서
     보내고 prepare.py를 재실행한다.
   - `missing`이 있으면 그 호출만 다시 보내고 prepare.py를 재실행한다.
   - `errors`는 그 섹션이 "데이터 준비 중"으로 나간다는 뜻이다. 계층 표 레벨이 `over 50,000 rows`로 거절됐으면 그
     레벨만 매체마다 `filters: {"media": ["<매체>"]}`로 다시 부르고 재실행한다(prepare.py가 합친다).
   - `ask_user`가 있으면 필수 지표(광고비·노출·클릭) 키를 못 정한 것이다 — 후보를 보여 주고 한 번에 묻고, 답을
     `--metric-keys '{"cost":"…"}'`로 넘겨 재실행한다. 매출 지표가 없는 것은 질문 사유가 아니다(매출 없음 모드).
3. **Daily Summary(`s2`)**: `guides/daily-summary.md`(무엇을 어떻게 쓸지)와
   `references/daily-report-section-2-executive-summary.md`(근거·이 플러그인에서 달라지는 점·빌더 입력)를 따라
   prepare 출력의 **`digest`만** 근거로 불릿 3~6개를 쓴 뒤 빌더를 1회 호출한다:
   ```
   python3 assets/build_report.py <<'PYEOF'
   {"base": "<prepare가 준 base 경로>", "s2": {"bullets": [{"head": "전체", "text": "…", "tone": "neutral"}, {"head": "<매체> / <캠페인>", "text": "…", "tone": "red|yellow|green"}, …]}}
   PYEOF
   ```
   → `~/Downloads/laighthouse-reports/{브랜드}_daily-report_{T}.html`에 저장된다(출력 `out`). 사용자가 다른 위치를
   말했으면 입력에 `"out": "<경로>"`를 함께 넣는다.
4. 그 HTML을 Artifact(또는 `mcp__visualize__show_widget`)로 게시한다. 둘 다 없는 호스트면 저장 경로만 안내한다.
5. 완료 메시지는 아래 형식 그대로.

| # | 라운드 | 도구 | 기간 | grain | 나머지 인자 |
|---|---|---|---|---|---|
| 1 | A | `get_ad_performance` | 당월 1일 ~ T | `month` | `group_by:["media"]` (`day_offset` 없음) |
| 2 | A | `get_ad_performance` | T-6일 ~ T | `day` | `group_by:["media"]` |
| 3 | A | `get_ad_performance` | T-6일 ~ T | `total` | `group_by:["media"]` |
| 4 | A | `get_target_progress_v2` | `month`: M, `as_of_date`: T | — | `media` 생략 |
| 5 | A | `list_promotions` | T-7일 ~ T | — | — |
| 6 | B | `get_ad_performance` | T-1일 ~ T | `day` | `group_by:["media","campaign_name"]` |
| 7 | B | `get_ad_performance` | T-1일 ~ T | `day` | `group_by:["media","campaign_name","ad_group_name"]` |
| 8 | B | `get_ad_performance` | T-1일 ~ T | `day` | `group_by:["media","campaign_name","ad_group_name","ad_name"]` |

`get_ad_performance`는 전부 `metrics`·`filters`를 생략한다(전체 지표·전체 매체). 라운드 B가 `over 50,000 rows`로
거절되면 그 레벨만 매체마다 `filters: {"media": ["<매체>"]}`로 다시 부르고 재실행한다(prepare.py가 합친다). 브랜드명이 서버에 없다고
거절되면 그때만 `get_brand_list`로 가장 비슷한 이름을 찾아 맞는지 사용자에게 묻는다(`shared/references/mcp-tools.md` 공통 규칙). 확인받은 이름은 이후 모든 호출의 `brand_name`과 `prepare.py --brand`, 제목·파일명에 쓴다.

## `digest` 읽는 법

`기준일`·`전일` · `지표`(이 브랜드에 있는 지표 라벨) · `전체`·`매체`(기준일·전일 값과 `전일 대비`) ·
`매체-캠페인`·`매체-캠페인-광고그룹`·`매체-캠페인-광고그룹-광고`(기준일 광고비 상위 + 광고비 변동 상위 행) ·
`구분`(신규 집행·집행 중단·광고비 급등·광고비 급락·효율 급변 — 미리 판정됨). 값은 화면에 쓸 문자열로 이미
만들어져 있다(금액 `₩`·천 단위 쉼표, 변화율 소수 1자리, % 지표는 %p). **digest 값을 그대로 옮기고 다시 계산하지
않는다. digest에 없는 수치는 쓰지 않는다.** 값 `-`는 그날 집행이 없었다는 뜻이다. `지표`에 매출·ROAS가 없으면
매출·ROAS를, 조회수·CPV가 없으면 조회수·CPV를 언급하지 않는다. 출력의 `facts`는 s2 작성에 쓰지 않는다.

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (기술적 디테일 언급 금지):

```
{브랜드명} 데일리 보고서({기준_일자}) 생성 완료.
가장 인상적인 부분: {한 문장 하이라이트}.
— by LaightAI
```

- `{한 문장 하이라이트}`: 렌더링된 수치 중 가장 눈에 띄는 지표 하나만 (여러 개 나열 금지).
