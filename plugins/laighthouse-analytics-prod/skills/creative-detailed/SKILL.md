---
name: creative-detailed
description: >
  브랜드 비종속 소재 보고서 생성 스킬. "소재 보고서", "소재 분석 보고서", "creative report" 요청 시 사용.
  소재(개별 광고 크리에이티브) 단위로 ROAS/CTR을 분석하는 보고서 — 캠페인/매체 실적 중심이
  아니라 최우수 소재 카드·소재별 라인차트 등으로 구성된다(매출 지표가 없는 브랜드는 클릭·CTR·CPC 기준). 사용자가 말한 브랜드의 매체·지표를
  응답에서 알아내고, 소재 데이터가 있는 매체 하나를 골라 분석한다.
metadata:
  version: "3.1.0"
---

> ⚡ thinking은 짧게. MCP 1라운드 → `prepare.py` → 썸네일 조회 → 문장 작성 + `build_report.py` → 게시, 이 순서로만 진행한다.

## 역할

사용자가 말한 브랜드의 **소재 보고서**(HTML, 5섹션: 최우수 소재 · Executive Summary · 일별 CTR · 일별 ROAS(매출 없음: 클릭) · 소재 단위 누적 성과 표)를 만든다. 최근 7일(T-6일 ~ T), **매체 하나**
(`chosen_media`)의 소재(개별 광고)를 분석한다. 브랜드명은 모든 호출의 `brand_name`과 제목·파일명에 **그대로** 쓴다.

계산·렌더링은 전부 미리 검증된 스크립트가 한다. 모델이 할 일은 (1) MCP 호출, (2) 스크립트 실행, (3) Executive
Summary(`s2`) 작성뿐이다. **MCP 응답 원문을 읽거나 옮겨 적거나 파일로 저장하지 않는다** — 플러그인 저장 훅이 응답
원본을 파일로 남기고 `prepare.py`가 매체 선택·랭킹·일별 시리즈까지 만든다. 스크립트 파일을 새로 만들거나 HTML을
직접 쓰지 않는다. `references/`의 섹션 문서는 아래에서 지정한 것 말고는 읽지 않는다.

## 실행 순서 (T = 기준일)

스크립트 경로 `assets/…`는 **이 SKILL.md가 있는 폴더** 기준이다 — 그 폴더로 `cd`한 뒤 실행하거나 절대 경로로
실행한다. MCP 응답 뒤에 붙는 캡처 훅 안내문(`[laighthouse-capture-hook] … 저장됨`)은 무시한다.

1. **MCP 3개를 한 메시지에서 동시에 호출한다** (아래 표, 인자는 표 그대로). 응답은 훑어보지도 않는다.
2. `python3 assets/prepare.py --brand <브랜드> --target-date <T>` (사용자가 매체를 말했으면 `--media <매체>`도)
   → 출력 JSON의 `base`(경로)·`facts`·`lookups`.
   - `ask_user.choose_media`가 있으면 소재명이 있는 매체가 여럿이다 — 후보(소재명 수 `named_ad_count`)를 보여 주고 어느 매체를 볼지 한 번 묻는다(`excluded`는 소재명이 없어 빠진 매체).
     답을 받으면 **MCP를 다시 부르지 않고** `--media <답>`으로 prepare.py만 재실행한다.
   - `stop`이 있으면 소재 단위 데이터가 있는 매체가 없다 — 그 사실을 알리고 끝낸다.
   - `missing`이 있으면 그 호출만 다시 보내고 재실행한다. 소재 단위 호출이 `over 50,000 rows`로 거절됐으면 같은
     인자에 `filters: {"media": ["<매체>"]}`를 붙여 매체마다 다시 부르고 재실행한다(prepare.py가 합친다).
   - `ask_user.missing`/`ambiguous`(필수 지표 키 미해결)면 한 번에 묻고 `--metric-keys '{"cost":"…"}'`로 재실행한다.
     매출 지표가 없는 것은 질문 사유가 아니다(매출 없음 모드 — 빌더가 ROAS 자리를 클릭으로 바꾼다).
   - `note`(저장된 응답 없음)가 나오면 저장 훅이 없는 호스트다 → `references/legacy-flow.md` 절차로 진행한다.
3. **썸네일 조회**: `lookups`(최대 4개)마다 `get_ad_creative_info`를 `{"brand_name": "<브랜드>", "name_query":
   "<lookups[i].ad_name>"}`로 한 메시지에서 동시에 부른다(**`source`는 넣지 않는다**). 응답 `items` 중 `ad_name`이
   정확히 같고, 항목에 `adgroup_name`/`campaign_name`이 있으면 그것도 lookup의 `ad_group_name`/`campaign_name`과 정확히
   같은 첫 항목의 `image_url`을 `thumbnails[lookups[i].id]`에 넣는다. 에러·빈 결과·불일치는 `null`(재시도 없음).
4. `references/creative-detailed-section-2-executive-summary.md`에서 **작성 원칙·모드별 기준·문장 형식**만 따른다. 그 파일의
   데이터 수집 설명(캡처 파일·`discover.py`·스크립트 출력 언급)은 무시한다 — 전부 facts로 대체됐다, `facts`만 근거로 `s2`를 쓴 뒤 빌더를 1회 호출한다:
   ```
   python3 assets/build_report.py <<'PYEOF'
   {"base": "<prepare가 준 base 경로>", "thumbnails": {"L1": "<url>", "L2": null}, "s2": {"executive_summary": "줄1\n줄2\n…"}}
   PYEOF
   ```
   → `~/Downloads/laighthouse-reports/{브랜드}_creative-detailed_{T}.html`에 저장된다(출력 `out`). 사용자가 다른 위치를
   말했으면 입력에 `"out": "<경로>"`를 함께 넣는다.
5. 그 HTML을 Artifact(또는 `mcp__visualize__show_widget`)로 게시한다. 둘 다 없는 호스트면 저장 경로만 안내한다.
6. 완료 메시지는 아래 형식 그대로.

| # | 도구 | 기간 | grain | 나머지 인자 |
|---|---|---|---|---|
| 1 | `get_ad_performance` | T-6일 ~ T | `total` | `group_by:["media"]` |
| 2 | `get_ad_performance` | T-6일 ~ T | `total` | `group_by:["media","campaign_name","ad_group_name","ad_name"]` |
| 3 | `get_ad_performance` | T-6일 ~ T | `day` | `group_by:["media","campaign_name","ad_group_name","ad_name"]` |

`get_ad_performance`는 전부 `metrics`·`filters`를 생략한다. 브랜드명이 서버에 없다고 거절되면 그때만
`get_brand_list`로 정확한 이름을 확인한다. 이미지 URL은 IP 화이트리스트 뒤에 있어 허용되지 않은 네트워크에서는 안
뜰 수 있다(폴백은 빌더가 처리한다).

## `facts` 읽는 법

`mode` · `chosen_media`·`candidates` · `media_totals`(매체 7일 합과 CTR·ROAS — 매출 없음: CPC) · `eligibility`(최소 표본
기준과 충족 소재 수) · `best`(최우수 소재 1·2위) · `top_by_cost`(광고비 상위 10개 소재의 7일 누적 지표·표시 이름) ·
`top5`(광고비 상위 5개 소재의 7일 누적 + 일별 CTR·ROAS(매출 없음: 클릭) 시리즈, `dates` 순서, `trend`=앞 3일 vs 뒤 4일 평균) · `overall_daily`(매체
전체 일별 CTR·ROAS/클릭) · `overall_trend`(같은 앞·뒤 평균). 비율은 이미 계산돼 있다. 추이 분석은 `top5` 소재로만 한다(다른 소재는 일별 값이 없다).
소재는 표시 이름 그대로 쓰고, 프로모션은 언급하지 않는다. **facts에 없는 수치는 쓰지 않는다** — facts 수치끼리의 단순 비교(배수·차이·%p)는 써도 된다. 숫자 표기: 금액·개수는 천 단위
쉼표, 비율은 소수 1자리(CTR은 2자리), 금액에는 `mode.currency`.

## 완료 메시지 형식

렌더링이 끝나면 아래 고정 템플릿으로만 응답한다 (기술적 디테일 언급 금지):

```
{브랜드명} 소재 보고서({기준_일자}, {chosen_media}) 생성 완료.
가장 인상적인 부분: {한 문장 하이라이트}.
— by LaightAI
```

- `{한 문장 하이라이트}`: 렌더링된 수치 중 가장 눈에 띄는 지표 하나만 (여러 개 나열 금지).
