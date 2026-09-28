# Creative Section 3: 최근 7일 일별 CTR (광고비 상위 5개 소재)

> 🧩 ChatGPT/Codex: 캡처 훅이 없는 환경에서는 응답이 원본 JSON 봉투로 온다 — `json`에 그대로
> 넘긴다(`shared/references/gpt-large-response-guardrail.md`).

**report_type:** `creative-detailed` (항상 포함). **`chosen_media` 하나만 대상**(SKILL.md 매체
선택). 기준일 포함 최근 7일 동안 **광고비(cost 키, 7일 합산) 상위 5개 소재**의 일별 CTR을
라인 차트로 보여준다.

> ℹ️ 차트 HTML/Script(색상 palette, spanGaps 등)는 전부 템플릿+빌더가 처리하고, 7일치 시리즈는
> `assets/creative_daily_series.py`가 계산한다 — 모델은 소재 5개 선정과 표시 이름만 정한다.

## MCP 도구 호출: `get_ad_performance` × 1 (`time_grain:"day"`, 소재 단위, 최근 7일) — section-3이 신규 호출

```json
{ "brand_name": "<brand>", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "time_grain": "day", "group_by": ["campaign_name", "ad_group_name", "ad_name"], "filters": {"media": ["<chosen_media>"]} }
```

- section-1의 total 응답(소재당 7일 합산 한 행)과는 **grain이 다르다** — section-3/4는
  **날짜별 값**(일별 트렌드, 행마다 `date` 키)이 필요해 total로는 만들 수 없다. **section-4가
  이 응답을 그대로 재사용**한다. 이 호출은 section-1의 total 1회와 함께 한 메시지에 병렬
  발사한다. 매출(revenue 키, 있을 때)이 각 행에 지표로 들어있어 별도 매출 호출이 없다.
- ⚠️ **`filters`를 생략해서 한 번에 받지 않는다** — 소재 단위는 고카디널리티라(마크다운 시절
  단일 매체 7일 응답 실측 13만 자+, 생략 시 76만 자+) 통합은 금지된 회귀다(실제 근사치 사고
  원인). 값은 디스커버리 응답의 `media` 문자열 그대로(정확 일치).

## 소재 선정: `assets/rank_creatives.py` 출력 재사용 (손정렬 금지)

1. SKILL.md 5단계에서 실행한 `rank_creatives.py`의 출력 파일(`/tmp/creative_rank.json`)에
   section-1 total 응답 기준 **광고비(7일 합산 cost 키) 내림차순 상위 5개** 키(`top5_keys`)와
   표시 이름(`top5_names`)이 이미 들어 있다 — 모델이 다시 정렬하지 않는다. 이 5개 키·순서는
   section-4와 공유한다(두 차트의 색상·범례 순서 일치). 상위 5개에는 최소 표본 기준(section-1)을
   적용하지 않는다.
2. **표시 이름 규칙**(스크립트가 적용): `ad_name`이 비었거나 `"-"`이면 `"<ad_group_name> (소재명
   없음)"`, 5개 중 표시 이름이 겹치면 그 소재들만 `" (<ad_group_name>)"`(그래도 겹치면
   `" (<campaign_name>)"`)을 덧붙인다.

## 일별 시리즈 계산: `assets/creative_daily_series.py` (필수 — 손계산·즉석 Bash·새 스크립트 금지)

위 day 응답에서 **5개 키 × 7일**을 exact-match로 뽑는 작업은 이 스크립트가 한다(`creative-summary`
와 같은 파일). section-4 시리즈도 **같은 호출 한 번**으로 함께 나온다 — section-4에서 다시
호출하지 않는다. 응답이 `[laighthouse-capture-hook] ... 저장됨: <경로>` 스텁으로 오면(캡처 훅
동작 호스트) 그 경로를 `json_files`에, 원본 JSON 봉투가 그대로 오면 `json`에 문자열 통째로
넣는다(손 전사·행 선별 금지, 스텁이 가리키는 파일을 Read로 열지 않는다):

```bash
python3 assets/creative_daily_series.py <<'PYEOF' > /tmp/creative_series.json
{"json_files": ["<day 응답 스텁 경로>"],
 "dates": ["기준일 6일 전", "...", "target_date"],
 "metric_keys": <discover.py 출력의 metric_keys 그대로 — revenue가 없으면 없는 채로>,
 "rank_file": "/tmp/creative_rank.json"}
PYEOF
```

- `dates`는 기준일 포함 7일 전체를 명시한다(행이 없는 날짜도 결측으로 정확히 채워진다).
- 스크립트가 구현한 계산(참고용 스펙): `campaign_name`+`ad_group_name`+`ad_name` 세 필드 정확
  일치(정규화/부분일치 없음)로 그 날짜 행을 찾아 날짜별 `CTR` = click 키÷impression 키×100.
  노출 0인 날, 행 자체가 없는 날(미게재)은 **`null`** — 0으로 채우지 않는다(차트에서 끊긴 구간,
  `spanGaps:false`는 템플릿에 있음). 출력 `top5.ctr_series`가 이 섹션용이다. `media: null` 행은
  무시한다.
- 출력 파일 경로는 빌더 입력 최상위 `series_file`에 넣는다(section-4와 공유). 시리즈 스크립트와
  빌더를 한 번의 Bash 호출에 이어서 실행해도 된다.

> 🚫 응답이 커도 선택지는 (1) 원본 전부를 스크립트에 넘기거나 (2) `s3`를 빼서 "데이터 준비
> 중"으로 표시하는 것 둘뿐 — 부분 전사·근사치·타 섹션 값 재사용 금지.

## 빌더 `s3` 필드

```json
"series_file": "/tmp/creative_series.json",   // 최상위 — s3/s4가 공유
"rank_file": "/tmp/creative_rank.json",       // 최상위 — s1/s3/s4/s5가 공유
"s3": {}
```

- `s3`는 빈 객체로 둔다 — 빌더가 `rank_file`의 `top5_names`를 범례 이름으로, `series_file`의
  `top5.ctr_series`를 시리즈로 쓰고, 라벨(`M/D` 7개)은 `dates`로 만든다. Y축은 0부터, 눈금은
  반올림(소수 최대 2자리), 툴팁 CTR은 소수 2자리, X축 제목 없음(템플릿 고정).
- 유효한 소재가 하나도 없으면 `s3` 키를 뺀다 → "데이터 준비 중" 카드. 범례 이름은 section-4
  차트도 공유한다 — `s3` 없이 `s4`만 넣으면 s4도 placeholder가 된다.
