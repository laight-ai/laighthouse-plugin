---
name: mtd-summary
description: >
  브랜드 비종속 Executive MTD 보고서 생성 스킬. "Executive MTD 보고서", "임원용 MTD 보고서", "executive mtd" 요청 시 사용.
  `mtd-detailed`(상세 MTD 보고서)를 임원이 딥다이브 없이 훑어볼 수 있도록 5개 섹션으로 재구성한 보고서. 사용자가 말한
  브랜드의 매체·지표를 응답에서 알아내 어떤 브랜드에도 같은 방식으로 동작한다.
metadata:
  version: "3.1.0"
---

> ⚡ thinking은 짧게. MCP 1라운드 → `prepare.py` → 문장 작성 + `build_report.py` → 게시, 이 순서로만 진행한다.

## 역할

사용자가 말한 브랜드의 **Executive MTD 보고서**(HTML, 5섹션: 목표 달성 현황 · Executive Summary · 월별 광고 성과 · 매체별 성과 추이 · 매체 성과 비교(전월 동기 vs 당월))를 만든다. 다른 보고서는 자매 스킬이다.
브랜드명은 모든 호출의 `brand_name`과 제목·파일명에 **그대로** 쓴다.

계산·렌더링은 전부 미리 검증된 스크립트가 한다. 모델이 할 일은 (1) MCP 호출, (2) 스크립트 실행, (3) Executive
Summary(`s2`) 작성뿐이다. **MCP 응답 원문을 읽거나 옮겨 적거나 파일로 저장하지 않는다** — 플러그인 저장 훅이 응답
원본을 파일로 남기고 `prepare.py`가 그것을 읽는다. 스크립트 파일을 새로 만들거나 HTML을 직접 쓰지 않는다.
`references/`의 섹션 문서는 아래에서 지정한 것 말고는 읽지 않는다.

## 실행 순서 (T = 기준일, M = T의 `YYYY-MM`)

스크립트 경로 `assets/…`는 **이 SKILL.md가 있는 폴더** 기준이다 — 그 폴더로 `cd`한 뒤 실행하거나 절대 경로로
실행한다. MCP 응답 뒤에 붙는 캡처 훅 안내문(`[laighthouse-capture-hook] … 저장됨`)은 무시한다.

1. **MCP 3개를 한 메시지에서 동시에 호출한다** (아래 표). 인자는 표 그대로 — `prepare.py`가 (도구 + 인자)로
   응답을 고르므로 날짜·grain·`day_offset`이 다르면 그 응답은 `missing`이 된다. 응답은 훑어보지도 않는다.
2. `python3 assets/prepare.py --brand <브랜드> --target-date <T>` → 출력 JSON의 `base`(경로)·`facts`.
   - `missing`이 있으면 그 호출만 다시 보내고 prepare.py를 재실행한다.
   - `errors`는 그 섹션이 "데이터 준비 중"으로 나간다는 뜻이다. 계층 표 레벨이 `over 50,000 rows`로 거절됐으면 그
     레벨만 매체마다 `filters: {"media": ["<매체>"]}`로 다시 부르고 재실행한다(prepare.py가 합친다).
   - `ask_user`가 있으면 필수 지표(광고비·노출·클릭) 키를 못 정한 것이다 — 후보를 보여 주고 한 번에 묻고, 답을
     `--metric-keys '{"cost":"…"}'`로 넘겨 재실행한다. 매출 지표가 없는 것은 질문 사유가 아니다(매출 없음 모드).
   - `note`(저장된 응답 없음)가 나오면 저장 훅이 없는 호스트다 → `references/legacy-flow.md` 절차로 진행한다.
3. `references/mtd-summary-section-2-executive-summary.md`에서 **작성 원칙·모드별 기준·문장 형식**만 따른다. 그 파일의 MCP 호출·데이터 수집
   설명(다른 섹션 응답·캡처 파일·`discover.py`·스크립트 출력 언급)은 무시한다 — 전부 facts로 대체됐다, `facts`만 근거로 `s2`를 쓴 뒤 빌더를 1회 호출한다:
   ```
   python3 assets/build_report.py <<'PYEOF'
   {"base": "<prepare가 준 base 경로>", "s2": {"bullets": [{"text": "…", "tone": "green|red|neutral"}, …]}}
   PYEOF
   ```
   → `~/Downloads/laighthouse-reports/{브랜드}_mtd-summary_{T}.html`에 저장된다(출력 `out`). 사용자가 다른 위치를
   말했으면 입력에 `"out": "<경로>"`를 함께 넣는다.
4. 그 HTML을 Artifact(또는 `mcp__visualize__show_widget`)로 게시한다. 둘 다 없는 호스트면 저장 경로만 안내한다.
5. 완료 메시지는 아래 형식 그대로.

| # | 도구 | 기간 | grain | 나머지 인자 |
|---|---|---|---|---|
| 1 | `get_ad_performance` | 5개월 전 1일 ~ T | `month` | `group_by:["media"]`, `day_offset`: T의 일(정수) |
| 2 | `get_target_progress_v2` | `month`: M, `as_of_date`: T | — | `media` 생략 |
| 3 | `list_promotions` | 당월 1일의 30일 전 ~ T | — | — |

`get_ad_performance`는 전부 `metrics`·`filters`를 생략한다(전체 지표·전체 매체). 브랜드명이 서버에 없다고
거절되면 그때만 `get_brand_list`로 정확한 이름을 확인한다.

## `facts` 읽는 법

`mode` · `pacing`(목표 예산·매출·ROAS, 소진률·달성률) · `total`(MTD vs 전월 동기, `change_pct`) · `by_media`(매체별 같은 비교) · `monthly_trend`(최근 6개월 각 월 1일~T일 동기간 합계) · `organic`(Organic 있을 때만: Organic·광고 매출과 Organic 비중) · `promotions`(MTD와 겹치거나 직전 30일 안에 끝난 것). 비율은 이미 계산돼 있다(ROAS·CTR %, CPC·CPA 통화, `change_pct`는 증감률 %). 섹션 문서가 "다른 섹션
응답에서 가져온다"고 한 수치는 전부 facts의 위 키에 있다. **facts에 없는 수치는 쓰지 않는다** — facts 수치끼리의 단순 비교(배수·차이·%p)는 써도 된다. 숫자 표기: 금액·개수는 천 단위
쉼표, 비율은 소수 1자리(CTR은 2자리), 금액에는 `mode.currency`. 매체명은 facts 값
그대로, 금액에는 `mode.currency`를 붙이고, `mode.has_revenue`가 false면 매출·ROAS를, `mode.has_organic`이 false면
Organic을 언급하지 않는다.

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (기술적 디테일 언급 금지):

```
{브랜드명} Executive MTD 보고서({기준_일자}) 생성 완료.
가장 인상적인 부분: {한 문장 하이라이트}.
— by LaightAI
```

- `{한 문장 하이라이트}`: 렌더링된 수치 중 가장 눈에 띄는 지표 하나만 (여러 개 나열 금지).
