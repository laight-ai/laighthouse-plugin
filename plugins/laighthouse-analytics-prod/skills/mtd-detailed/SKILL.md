---
name: mtd-detailed
description: >
  브랜드 비종속 상세 MTD 보고서 생성 스킬. "MTD 보고서", "mtd 보고서" 요청 시 사용.
  목표 대비 진행·월별 추이·매체별 일별 추이·매체별 예산·계층 표(매체·캠페인·광고그룹·광고, 전월 동기
  vs 당월)까지 보여주는 7섹션 MTD 보고서. 사용자가 말한 브랜드의 매체·지표를 응답에서 알아내
  어떤 브랜드에도 같은 방식으로 동작한다.
metadata:
  version: "3.1.0"
---

> ⚡ thinking은 짧게. MCP 1라운드 → `prepare.py` → 문장 작성 + `build_report.py` → 게시, 이 순서로만 진행한다.

## 역할

사용자가 말한 브랜드의 **MTD 보고서**(HTML, 7섹션 고정)를 만든다. weekly는 지원하지 않는다. 다른 보고서는
자매 스킬(`mtd-summary`/`daily-*`/`monthly-*`/`creative-*`)이다. 브랜드명은 모든 호출의 `brand_name`과
제목·파일명에 **그대로** 쓴다.

계산·렌더링은 전부 미리 검증된 스크립트가 한다. 모델이 할 일은 (1) MCP 호출, (2) 스크립트 실행, (3) 요약
문장 두 개(`s2`·`s5`) 작성뿐이다. **MCP 응답 원문을 읽거나 옮겨 적거나 파일로 저장하지 않는다** — 플러그인
저장 훅이 응답 원본을 파일로 남기고 `prepare.py`가 그것을 읽는다. 스크립트 파일을 새로 만들거나 HTML을
직접 쓰지 않는다. 섹션별 설명 문서(`references/`)는 **읽지 않는다**.

## 실행 순서 (T = 기준일, M = T의 `YYYY-MM`)

스크립트 경로 `assets/…`는 **이 SKILL.md가 있는 폴더** 기준이다 — 그 폴더로 `cd`한 뒤 실행하거나 절대 경로로
실행한다. MCP 응답 뒤에 붙는 캡처 훅 안내문(`[laighthouse-capture-hook] … 저장됨`)은 무시한다 — 이 스킬은
`json_files`를 쓰지 않는다.

1. **MCP 7개를 한 메시지에서 동시에 호출한다** (아래 표). 인자는 표 그대로 — `prepare.py`가 (도구 + 인자)로
   응답을 고르므로 날짜·grain·`day_offset`이 다르면 그 응답은 `missing`이 된다. 응답은 훑어보지도 않는다.
2. `python3 assets/prepare.py --brand <브랜드> --target-date <T>` → 출력 JSON의 `base`(경로)·`facts`.
   - `missing`이 있으면 그 호출만 다시 보내고 prepare.py를 재실행한다.
   - `errors`는 그 섹션이 "데이터 준비 중"으로 나간다는 뜻이다. 한 레벨이 `over 50,000 rows`로 거절됐으면
     그 레벨만 매체마다 `filters: {"media": ["<매체>"]}`로 다시 부르고 재실행한다(prepare.py가 합친다).
   - `ask_user`가 있으면 필수 지표(광고비·노출·클릭) 키를 못 정한 것이다 — 후보를 보여 주고 사용자에게 한 번에
     묻고, 답을 `--metric-keys '{"cost":"…"}'`로 넘겨 재실행한다. 매출 지표가 없는 것은 질문 사유가 아니다(매출
     없음 모드 — 빌더가 알아서 노출·클릭·CTR·CPC로 바꾼다).
   - `note`(저장된 응답 없음)가 나오면 저장 훅이 없는 호스트다 → `references/legacy-flow.md` 절차로 진행한다.
3. `facts`만 근거로 `s2`·`s5` 문장을 쓰고(아래 규칙), 빌더를 1회 호출한다:
   ```
   python3 assets/build_report.py <<'PYEOF'
   {"base": "<prepare가 준 base 경로>", "s2": {"executive_summary": "…"}, "s5": {"campaign_analysis": "…"}}
   PYEOF
   ```
   → `~/Downloads/laighthouse-reports/{브랜드}_mtd-detailed_{T}.html`에 저장된다(출력 `out`). 사용자가 다른
   위치를 말했으면 입력에 `"out": "<경로>"`를 함께 넣는다.
4. 그 HTML을 Artifact(또는 `mcp__visualize__show_widget`)로 게시한다. 둘 다 없는 호스트면 저장 경로만 안내한다.
5. 완료 메시지는 아래 형식 그대로.

| # | 도구 | 기간 | grain | 나머지 인자 |
|---|---|---|---|---|
| 1 | `get_ad_performance` | 5개월 전 1일 ~ T | `month` | `group_by:["media"]`, `day_offset`: T의 일(정수) |
| 2 | `get_ad_performance` | 당월 1일 ~ T | `day` | `group_by:["media"]` |
| 3 | `get_ad_performance` | 전월 1일 ~ T | `month` | `group_by:["media","campaign_name"]`, `day_offset` |
| 4 | `get_ad_performance` | 전월 1일 ~ T | `month` | `group_by:["media","campaign_name","ad_group_name"]`, `day_offset` |
| 5 | `get_ad_performance` | 전월 1일 ~ T | `month` | `group_by:["media","campaign_name","ad_group_name","ad_name"]`, `day_offset` |
| 6 | `get_target_progress_v2` | `month`: M, `as_of_date`: T | — | `media` 생략 (매체별 목표는 응답의 두 번째 표) |
| 7 | `list_promotions` | 당월 1일 ~ T | — | — |

`get_ad_performance`는 전부 `metrics`·`filters`를 생략한다(전체 지표·전체 매체). 브랜드명이 서버에 없다고
거절되면 그때만 `get_brand_list`로 정확한 이름을 확인한다.

## `facts` 읽는 법

`mode`(매출 있음/없음·Organic·전환 여부·통화) · `pacing`(월 진행률 vs 예산 소진률, 목표 예산·매출·ROAS) ·
`total`(MTD vs 전월 동기, 증감률 %) · `by_media`(매체별 예산·소진률·실적·전월 동기 대비) · `promotions`(MTD와
겹치거나 직전 7일 안에 끝난 프로모션) ·
`campaigns_top_by_cost`(당월 광고비 상위 12개, `eff_shift`=효율 ±20% 이상 변화, `pick_score`=광고비×변화 폭) ·
`campaigns_efficiency_shift`(상위 밖 효율 급변) · `top_campaign_ad_groups`(상위 6개 캠페인의 광고그룹 당월·전월 동기,
`new`=전월 동기에 없던 그룹) ·
`daily_dips_total`(광고 매체 합계가 일 중앙값의 50% 미만인 날) · `daily_dips_by_media`(매체별 같은 기준) ·
`organic_revenue`(Organic 있을 때만) · `target_media_unmatched`(목표 매체명이 응답과 안 맞음). 비율은 이미
계산돼 있다(ROAS·CTR %, CPC·CPA 통화). **facts에 없는 수치는 쓰지 않는다** — facts 수치끼리의 단순 비교(배수·차이·%p)는 써도 된다. 숫자 표기: 금액·개수는 천 단위
쉼표, 비율은 소수 1자리(CTR은 2자리), 금액에는 `mode.currency`.

## `s2.executive_summary` — 정확히 4줄, 이 순서, 줄마다 한 문장 (`\n` 구분)

1. **효율 vs 목표**: 매출 있음 → 실제 ROAS vs 목표 ROAS(상회/근접/하회). 목표 ROAS가 없으면 전월 동기 ROAS와
   비교. 매출 없음 → CTR·CPC를 전월 동기와 비교.
2. **페이싱**: 목표 예산이 있으면 예산 소진률 vs 월 진행률 — 차이가 ±10%p 이내면 정상, 그 밖이면 빠름/느림이고
   줄 앞에 `⚠`. 목표 예산이 없을 때만 전월 동기 누적 광고비와 비교. 원인 추측 금지.
3. **매체 특이사항**: `by_media`에서 가장 눈에 띄는 것 하나(매체명은 값 그대로).
4. **규모 특이사항**: 광고 매출(매출 없음: 클릭)의 전월 동기 대비 변화, 또는 `daily_dips_total`의 급감 구간 중
   더 두드러진 하나(한 문장에 둘을 이어 써도 된다). "전 매체"처럼 범위를 말할 때는 facts가 보여 주는 범위만 쓴다.
   겹치는 프로모션이 있으면 이름과 기간을 함께 쓴다(효과가 뚜렷하지 않으면 그대로). 원인은 추측하지 않는다.

목표 미등록·소진 속도 비정상·`target_media_unmatched` 같은 주의 항목은 줄 맨 앞에 `⚠`. Organic은 `mode.has_organic`
일 때만 언급한다. 강조 수치에 `<strong>` 사용 가능.

## `s5.campaign_analysis` — 캠페인 2~4개 서술

- 형식: `\n\n`으로 블록 구분. 첫 블록은 인트로 한두 문장, 이후 블록은 첫 줄 `<캠페인명> (<매체>)`, 다음 줄부터 본문.
- 광고비 큰 캠페인을 우선 보되 나열하지 않는다 — 전월 동기 대비 또는 같은 매체 안에서 효율이 확연히 다른
  것(`eff_shift`인 것)만, `pick_score`가 큰 순으로 고른다. 특이사항이 없으면 억지로 채우지 않는다.
- 특이사항마다 근거 수치 + 짧은 원인 가설 + 해결 방향. 가설은 facts의 수치(광고그룹 당월·전월 동기 변화, 신규
  광고그룹, 겹치는 프로모션 이름·기간)로 뒷받침되는 것만 쓰고, 근거가 없으면 "확인이 필요하다"까지만 쓴다.
- CTR·CPC는 **같은 매체 안에서만** 비교한다(ROAS·CPA·전환은 매체 간 비교 가능). 매출 없음 모드면 매출·ROAS·
  객단가를 언급하지 않는다. 금액에는 `mode.currency`를 붙인다.

## 완료 메시지 형식 (기술적 디테일 언급 금지)

```
{브랜드명} MTD 보고서({기준_일자}) 생성 완료.
가장 인상적인 부분: {렌더링된 수치 중 가장 눈에 띄는 지표 하나를 한 문장으로}.
— by LaightAI
```
