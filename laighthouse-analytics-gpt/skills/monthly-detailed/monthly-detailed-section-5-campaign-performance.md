# Monthly Section 5: 캠페인 성과 비교 (M-1 vs M0)

**report_type:** `monthly-detailed` (항상 포함). 매체-캠페인 단위로 **전월(M-1)과 당월(M0)**을
비교한다 — `daily-detailed`의 section-4를 캠페인 단위로 유지한 채 시점만 하루→한 달로 바꾼
버전.

> ℹ️ 표 HTML/검색/페이지네이션 렌더링은 템플릿+빌더가, 파생지표·변화율·`(-)` 규칙·
> `threshold` 필터·정렬·`<tr>` 생성은 `assets/monthly_campaign_rows.py`가 한다 — 모델의 역할은
> 아래 MCP 1회 호출과 스크립트 실행뿐이다.

## MCP 도구 호출: `get_ad_performance` × 1 (전월~당월, 캠페인 단위, `filters` 생략)

```json
{ "brand_name": "<brand>", "start_date": "전월 YYYY-MM-01", "end_date": "target_date", "time_grain": "month", "group_by": ["media", "campaign_id", "campaign_name"], "day_offset": <target_date.day (정수)> }
```

- **`filters`는 생략한다** — 캠페인 단위는 광고 단위보다 카디널리티가 낮다. 각 행에 `month`/
  `media`/`campaign_id`/`campaign_name` 차원과 cost/impression/click/revenue(/conversion) 역할
  키 지표가 함께 들어있다(매출 조인 없음). 매체 라벨은 행의 `media` 값 그대로(`null`은
  "Organic" — 광고비가 없어 `threshold` 필터에서 자연히 빠진다).
  ⚠️ 캠페인 수가 크게 늘어 응답이 비대해지면 `media_list`를 순회하며 `filters:{"media":[<값>]}`
  매체별 호출로 재분리한다(응답들은 스크립트에 한 번에 넘긴다).
- **`day_offset: target_date.day` 필수** — 전월을 당월과 같은 일자까지 자른 동일 기간으로
  비교하기 위함. 이 1회 호출에서 M-1·M0 값을 동시에 받는다.
- ⚠️ **실측 데이터 특성**: 전월에 개별 캠페인 행이 없는 경우가 흔하다 — 비교 불가 캠페인은
  스크립트가 `(-)` 규칙으로 처리한다.
- section-3/4의 `group_by:["media"]` 응답과는 granularity가 달라 공유하지 않는다.

## 계산·행 생성: `assets/monthly_campaign_rows.py` (필수 절차 — 손계산·새 스크립트 금지)

응답(원본 JSON 봉투 문자열)을 `json`에 그대로 넘긴다(손 전사·행 선별 절대 금지 — threshold
초과 행이 조용히 누락될 위험). 이 환경에는 캡처 훅이 없으므로 `json_files` 입력은 쓰지 않는다
— 대용량 대응 원칙은 `shared/references/gpt-large-response-guardrail.md` 참고. 디스커버리로
정한 `metric_keys`와 `currency`/`threshold`를 빌더와 같은 값으로 함께 넘기고, 출력은 빌더가
읽을 파일로 저장한다:

```bash
python3 assets/monthly_campaign_rows.py <<'PYEOF' > /tmp/s5_rows.json
{"m1_month":"2026-06","m0_month":"2026-07",
 "metric_keys":{"cost":"<cost 키>","impression":"<impression 키>","click":"<click 키>","revenue":"<revenue 키>","conversion":"<conversion 키 — 있을 때만>"},
 "currency":"₩","threshold":300000,
 "json":["<원본 JSON 봉투 문자열>"]}
PYEOF
```

⚠️ **응답을 먼저 파일로 저장했다가 별도 호출로 다시 읽어서 실행하는 2단계 금지** — 따옴표
있는 heredoc(`<<'PYEOF'`)은 셸이 본문을 해석하지 않으므로 크고 특수문자 많은 원본에도
안전하다. 응답을 받은 바로 그 Bash 호출 안에서 한 번에 끝낸다.

스크립트가 JSON 봉투 파싱, media별 자동 분리, M-1/M0 비교(media+campaign_name 정확 일치 —
부분일치/정규화 금지. 매출/전환은 같은 행의 역할 키라 조인이 없다), 지표 컬럼(cost/CTR/
[conversion/CPA]/revenue/ROAS — `metric_keys`에 conversion이 없으면 전환·CPA 생략)과 변화율·
화살표·색상, **비교 불가 시 `(-)` 회색 표시**(daily의 "변화량 생략"과 다른 이 섹션만의 규칙),
M0 광고비 `threshold` 이하 필터(기본 300000), M0 광고비 내림차순 정렬, `<tr>` HTML 생성까지
전부 처리한다. `metric_keys`를 생략하면 봉투 `metrics`에서 패턴 후보로 자동 해석하지만 빌더의
`<th>`와 어긋날 수 있으므로 **항상 명시**한다. 출력 파일 경로를 빌더 입력 JSON의
`s5.rows_file`에 넣으면 끝.

> 🚫 **응답이 크다고 느껴져도 선택지는 둘뿐이다**: (1) 원본을 가공 없이 전부 스크립트에 넘기거나
> (2) 정말 불가능하면 `s5`를 빌더 입력에서 빼서 "데이터 준비 중"으로 표시한다. 다른 섹션 값
> 재사용·근사치·추정 수치 대체는 그 숫자가 진짜 쿼리 결과라도 **전부 금지**다 — 자매 스킬에서
> 이 규칙 위반(출처 불명 수치 삽입, 타 섹션 값 바꿔치기) 사고가 실제로 두 차례 있었다. 이미
> 정상적으로 받은 응답은 그 세분화 단위 그대로 쓴다 — "받았지만 크다"며 대체하는 경우는
> 존재하지 않는다.
