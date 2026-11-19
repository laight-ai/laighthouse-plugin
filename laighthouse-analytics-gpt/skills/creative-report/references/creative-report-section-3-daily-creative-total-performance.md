# Creative Section 3: 최근 7일 매체 전체 CTR 및 ROAS (매출 없음: CTR 및 클릭)

**report_type:** `creative-report` (항상 포함). **`chosen_media` 하나만 대상.**
section-4/5(상위 5개 소재)와 달리 **분석 매체 전체**(소재 단위로 측정하지 않는 캠페인 포함)의 날짜별 CTR과
ROAS(매출 없음 모드: **클릭**) 7일 추이를 보여준다. 두 지표는 카드 2개로 분리 렌더링(듀얼 Y축 합침
금지 — 스케일 착시)·최소 Y축 폭·`M/D(요일)` 라벨·각주·모드별 제목은 전부 템플릿+빌더에 고정돼
있다.

## MCP 도구 호출: 매체 일별 1회 (legacy-flow 6-a)

`get_ad_performance`(`time_grain:"day"`, `group_by:["media"]`, `filters:{"media":["<chosen_media>"]}`, 최근 7일,
`metrics` 생략) — 행이 7개뿐이다. 소재 단위 일별 응답(6-b)은 상위 5개 소재만 받으므로 이 섹션에 쓰지 않는다.
저장 훅이 있는 호스트에서는 prepare.py가 라운드 A 매체 일별 응답으로 이 섹션을 만든다.

## 계산: `assets/creative_daily_series.py` (필수 — 손계산·새 스크립트 금지)

응답이 캡처 훅 스텁으로 오면 경로를 `json_files`에, 원본 JSON 봉투면 `json`에 문자열 통째로 넘긴다.
**`rank_file` 없이** 호출해 전체 일별만 계산하고, 상위 5개용 시리즈 파일과 따로 저장한다:

```bash
python3 assets/creative_daily_series.py <<'PYEOF' > /tmp/creative_series_overall.json
{"json_files": ["<매체 일별 응답 스텁 경로>"],
 "dates": ["기준일 6일 전", "...", "target_date"],
 "metric_keys": <discover.py 출력의 metric_keys 그대로 — revenue가 없으면 없는 채로>}
PYEOF
```

- `dates`는 기준일 포함 7일 전체를 명시한다(행이 전혀 없는 날짜도 결측으로 정확히 채워진다).
- 응답을 먼저 파일로 저장했다가 별도 호출로 다시 읽지 않는다 — 따옴표 있는
  heredoc(`<<'PYEOF'`) 하나로 한 번에 끝낸다(`echo '...'`는 이스케이프가 깨지기 쉬워 금지).
- 스크립트가 구현한 계산(참고용 스펙): 날짜별로 매체 행의 cost/impression/click(/revenue) 키
  합 → `전체 CTR` = 클릭 합÷노출 합×100(노출 0이면 null), `전체 클릭` = 클릭 합(행 없으면 0),
  `전체 ROAS` = 매출 합÷광고비 합×100(광고비 0이면 null — **매출 있음 모드만**, 매출 없음이면
  ROAS 계열을 생략하고 멈추지 않는다). 매출이 각 행에 지표로 들어있어 조인이 없다. 비율은 행의
  서버 계산 비율 지표를 합산하지 않고 항상 원자 지표 합으로 직접 계산한다. `media: null` 행은
  무시한다. 매출 `null` 행은 합계에서 0으로 취급한다. `metric_keys`를 생략하면 스크립트가 공용 킷(`report_kit.resolve_roles`) 규칙으로
  응답 `metrics`에서 해석하고, 필수 역할을 못 정하면 명확한 에러를 낸다.

> 🚫 **응답이 크다고 느껴져도 선택지는 둘뿐이다**: (1) 원본을 가공 없이 전부 스크립트에
> 넘기거나 (2) 정말 불가능하면 `s3`를 빌더 입력에서 빼서 "데이터 준비 중"으로 표시한다.
> 부분 전사·근사치·다른 섹션 값 재사용은 그 숫자가 진짜 쿼리 결과라도 전부 금지다.

## 빌더 `s3` 필드

```json
"series_file": "/tmp/creative_series.json",                   // 최상위 — s4/s5(상위 5개)
"s3": {"series_file": "/tmp/creative_series_overall.json"}    // 이 섹션만 매체 일별로 만든 시리즈
```

- 빌더가 `overall.ctr_series`와 `overall.roas_series`(매출 없음: `overall.click_series`), `dates` 기반 라벨을 쓴다.
  CTR Y축은 0 아래로 내려가지 않고, 눈금은 소수 최대 2자리, CTR 툴팁은 소수 2자리다(템플릿 고정).
  데이터가 비어 있으면 `s3` 키를 빼면 "데이터 준비 중" 카드가 된다.
