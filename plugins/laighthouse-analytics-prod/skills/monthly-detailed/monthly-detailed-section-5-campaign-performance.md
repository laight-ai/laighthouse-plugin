# Breezm Monthly Section 5: 캠페인 성과 비교 (M-1 vs M0)

**report_type:** `monthly-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 매체-캠페인
단위로 **전월(M-1)과 당월(M0)**을 비교한다 — `daily-detailed`의 section-4를 캠페인 단위로
유지한 채 시점만 하루→한 달로 바꾼 버전.

> ℹ️ 표 HTML/검색/페이지네이션 렌더링은 템플릿+빌더가, 조인·파생지표·변화율·`(-)` 규칙·
> ₩300,000 필터·정렬·`<tr>` 생성은 `assets/monthly_campaign_rows.py`가 한다 — 모델의 역할은
> 아래 MCP 4회 호출과 스크립트 실행뿐이다.

## MCP 도구 호출: `get_ad_performance_monthly_table` × 4 (전월~당월, 매체별 각각)

```json
{ "brand_name": "breezm", "media": "google", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "group_by": "campaign", "day_offset": "target_date.day" }
{ "brand_name": "breezm", "media": "meta", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "group_by": "campaign", "day_offset": "target_date.day" }
{ "brand_name": "breezm", "media": "naver", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "group_by": "campaign", "day_offset": "target_date.day" }
{ "brand_name": "breezm", "media": "airbridge", "start_month": "전월 YYYY-MM", "end_month": "당월 YYYY-MM", "group_by": "campaign", "day_offset": "target_date.day" }
```

- **매체별로 4번 나눠 부른다** (`media` 생략 금지) — `group_by:"campaign"` 응답은 매체를
  합치면 행 수가 매체 수만큼 불어나고, `monthly-detailed`는 월 단위 span이라 daily 계열보다
  위험이 더 크다 (같은 도구 계열 `group_by:"ad"`에서 media-omit 766,576자 실측 사고 있음).
  네 호출은 의존성이 없으므로 한 메시지에서 병렬 발사.
- **`day_offset: target_date.day` 필수** — 전월을 당월과 같은 일자까지 자른 동일 기간으로
  비교하기 위함. 각 호출에서 M-1·M0 값을 동시에 받는다.
- ⚠️ **실측 데이터 특성**: airbridge(매출/예약)는 전월에 개별 캠페인 행이 없는 경우가 흔하다 —
  같은 캠페인이라도 지표별로 독립적으로 M-1 유무가 갈릴 수 있다(하나 없다고 나머지도 없다고
  가정하지 않는다). 스크립트가 이를 `(-)` 규칙으로 처리한다.
- ⚠️ `campaign-type` 금지, `group_by`는 문자열 `"campaign"` 그대로.
- section-3/4의 `group_by:"media"` 응답과는 granularity가 달라 공유하지 않는다.

## 계산·행 생성: `assets/monthly_campaign_rows.py` (필수 절차 — 손계산·새 스크립트 금지)

응답이 `[laighthouse-capture-hook] ... 저장됨: <경로>` 스텁으로 오면(캡처 훅 동작 호스트)
그 경로를 `markdown_files`로, 원본 마크다운이 그대로 오면 `markdown`에 원본 문자열 통째로
(혼용 가능. 손 전사·행 선별 절대 금지 — ₩300,000 초과 행이 조용히 누락될 위험). 스텁이
가리키는 캡처 파일을 Read로 열어 내용을 컨텍스트로 가져오지 않는다(경로만 넘긴다). 4개 응답
전부를 한 번에 넘기고, 출력은 빌더가 읽을 파일로 저장한다:

```bash
python3 assets/monthly_campaign_rows.py <<'PYEOF' > /tmp/s5_rows.json
{"m1_month":"2026-06","m0_month":"2026-07","markdown":["<google 응답 원본>","<meta 응답 원본>","<naver 응답 원본>","<airbridge 응답 원본>"]}
PYEOF
```

⚠️ **응답을 먼저 파일로 저장했다가 별도 호출로 다시 읽어서 실행하는 2단계 금지** — 따옴표
있는 heredoc(`<<'PYEOF'`)은 셸이 본문을 해석하지 않으므로 크고 특수문자 많은 마크다운에도
안전하다. 응답을 받은 바로 그 Bash 호출 안에서 한 번에 끝낸다.

스크립트가 마크다운 파싱, media별 자동 분리(ga4 등 제외), M-1/M0 독립 조인(campaign_name
정확 일치, airbridge 매출/예약 귀속 — 부분일치/정규화 조인 금지), 6개 지표(광고비/CTR/예약
완료/예약 완료 CPA/매출/ROAS)와 변화율·화살표·색상, **비교 불가 시 `(-)` 회색 표시**(daily의
"변화량 생략"과 다른 이 섹션만의 규칙), M0 광고비 ₩300,000 이하 필터, M0 광고비 내림차순
정렬, `<tr>` HTML 생성까지 전부 처리한다. airbridge 쪽에만 있는(매체 미매칭) 캠페인은 표에
포함되지 않는다(고정 각주로 갈음). 출력 파일 경로를 빌더 입력 JSON의 `s5.rows_file`에 넣으면
끝.

> 🚫 **응답이 크다고 느껴져도 선택지는 둘뿐이다**: (1) 원본을 가공 없이 전부 스크립트에 넘기거나
> (2) 정말 불가능하면 `s5`를 빌더 입력에서 빼서 "데이터 준비 중"으로 표시한다. 다른 섹션 값
> 재사용·근사치·추정 수치 대체는 그 숫자가 진짜 쿼리 결과라도 **전부 금지**다 — 자매 스킬에서
> 이 규칙 위반(출처 불명 수치 삽입, 타 섹션 값 바꿔치기) 사고가 실제로 두 차례 있었다. 이미
> 정상적으로 받은 응답은 그 세분화 단위 그대로 쓴다 — "받았지만 크다"며 대체하는 경우는
> 존재하지 않는다.
