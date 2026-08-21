# Breezm Executive Creative Section 3: 최근 7일 전체 소재 CTR 및 ROAS

**report_type:** `creative-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
**메타(Meta Ads)만 대상.** section-4/5(상위 5개 소재)와 달리 **모든 소재를 날짜별로 합산**해
전체 CTR·전체 ROAS의 7일 추이를 보여준다. CTR 카드와 ROAS 카드 2개로 분리 렌더링(듀얼 Y축
합침 금지 — 스케일 착시)·최소 Y축 폭·`M/D(요일)` 라벨·각주는 전부 템플릿+빌더에 고정돼 있다.

## MCP 도구 호출: 신규 호출 없음 — section-3/4/5 공유 day grain 응답 재사용

SKILL.md 실행 순서 2-b에서 호출한 `get_ad_performance`(`time_grain:"day"`, `media:"Meta"`,
소재 단위, 최근 7일) 응답을 그대로 쓴다 — 이 섹션에서 다시 호출하지 않는다. section-1의
total 응답은 날짜가 무너져 있어 이 섹션의 "날짜별 추이"에 쓸 수 없다.

## 계산: `assets/creative_daily_series.py` (필수 — 손계산·새 스크립트 금지)

응답이 `[laighthouse-capture-hook] ... 저장됨: <경로>` 스텁으로 오면(캡처 훅 동작 호스트) 그
경로를 `json_files`에, 원본 JSON 봉투가 그대로 오면 `json`에 문자열 통째로(혼용 가능, 손
전사·행 선별 절대 금지). 스텁이 가리키는 캡처 파일을 Read로 열지 않는다(경로만 넘긴다).
section-4/5용 `top5_keys`까지 같이 넘겨 **한 번의 호출**로 끝내고, 출력은 빌더가 읽을 파일로
저장한다:

```bash
python3 assets/creative_daily_series.py <<'PYEOF' > /tmp/creative_series.json
{"json_files": ["<day 응답 스텁 경로>"],
 "dates": ["기준일 6일 전", "...", "target_date"],
 "top5_keys": [ {"campaign_name": "...", "ad_group_name": "...", "ad_name": "..."}, ... ]}
PYEOF
```

- `dates`는 기준일 포함 7일 전체를 명시한다(행이 전혀 없는 날짜도 결측으로 정확히 채워진다).
- 응답을 먼저 파일로 저장했다가 별도 호출로 다시 읽지 않는다 — 따옴표 있는
  heredoc(`<<'PYEOF'`) 하나로 한 번에 끝낸다(`echo '...'`는 이스케이프가 깨지기 쉬워 금지).
- 스크립트가 구현한 계산(참고용 스펙): 날짜별로 모든 행의 `광고비`/`노출`/`클릭`/`매출_AB`
  합 → `전체 CTR` = 클릭 합÷노출 합×100(노출 0이면 null), `전체 ROAS` = 매출 합÷광고비
  합×100(광고비 0이면 null). 매출(`매출_AB`)이 각 행에 지표로 들어있어 조인이 없다. CTR/ROAS는
  행의 서버 계산 비율 지표를 합산하지 않고 항상 원자 지표 합으로 직접 계산한다(행 단위 비율은
  합칠 수 없다). 지표 키는 브리즘 기본값이 내장돼 있고 응답 `metrics`와 대조·검증된다.

> 🚫 **응답이 크다고 느껴져도 선택지는 둘뿐이다**: (1) 원본을 가공 없이 전부 스크립트에
> 넘기거나 (2) 정말 불가능하면 `s3`를 빌더 입력에서 빼서 "데이터 준비 중"으로 표시한다.
> 부분 전사·근사치·다른 섹션 값 재사용은 그 숫자가 진짜 쿼리 결과라도 전부 금지다.

## 빌더 `s3` 필드

```json
"series_file": "/tmp/creative_series.json",   // 최상위 — s3/s4/s5가 공유
"s3": {}
```

- 위 스크립트 출력 파일 경로를 빌더 입력 **최상위** `series_file`에 넣고, `s3` 키를
  존재시키기만 하면 된다(빌더가 `overall.ctr_series`/`overall.roas_series`와 `dates` 기반
  라벨을 알아서 쓴다). 데이터가 비어있으면 `s3` 키를 빼면 "데이터 준비 중" 카드가 된다.
