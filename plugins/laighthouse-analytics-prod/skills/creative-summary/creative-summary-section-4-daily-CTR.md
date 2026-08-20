# Breezm Executive Creative Section 4: 최근 7일 일별 CTR (광고비 상위 5개 소재)

**report_type:** `creative-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
**메타(Meta Ads)만 대상.** 최근 7일 동안 **광고비(7일 합산)가 가장 큰 소재 5개**의 일별 CTR
라인 차트 (`creative-detailed` section-3과 동일 내용, 번호만 3→4). 라인 색상 팔레트·하단
범례·`M/D` 라벨·`spanGaps:false`(결측 미연결)는 템플릿에 고정돼 있다.

## MCP 도구 호출: 신규 호출 없음 — 두 응답 재사용

1. **소재 선정용**: section-1이 호출한 `get_ad_performance` total 응답
   (`time_grain:"total"`, `media:"Meta"`, 최근 7일 — 소재당 1행, 7일 합산 `광고비` 포함).
2. **일별 시리즈용**: SKILL.md 2-b의 `get_ad_performance` day 응답
   (`time_grain:"day"`, `media:"Meta"`, 같은 7일 — section-3/5와 공유).

## 소재 선정 (단순 정렬 — 스크립트 불필요)

1. section-1의 total 응답에서 소재별 7일 합산 `광고비`를 그대로 읽는다 — day
   응답에서 다시 합산하지 않는다.
2. `광고비` 내림차순 상위 5개를 뽑는다. **이 5개 목록·순서는 section-5도 동일하게 재사용한다**
   (두 차트의 라인 색상·범례 순서 일치).
3. **표시 이름**: 5개 중 `ad_name`이 중복되면 그 소재들만 `{ad_name} ({ad_group_name})`으로
   구분하고, 유일하면 `ad_name`만 쓴다(불필요하게 전부 괄호를 붙이지 않는다).

## 계산: `assets/creative_daily_series.py` (필수) — section-3 파일의 호출 절 참고

section-3 파일에 적힌 **한 번의 heredoc 호출**에 위 5개 키(`campaign_name`/`ad_group_name`/
`ad_name`)를 `top5_keys`로(위 선정 순서 그대로) 넣으면, 출력 `top5.ctr_series`(이 섹션용)와
`top5.roas_series`(section-5용)가 함께 나온다 — 이 섹션에서 스크립트를 다시 호출하지 않는다.
CTR은 스크립트가 항상 클릭÷노출×100으로 직접 계산한다. 노출 0이거나 그 날짜 행이 없으면
이미 `null`로 채워져 있다 — 추가 가공 불필요.

> 🚫 응답이 커도 선택지는 (1) 원본 전부를 스크립트에 넘기거나 (2) `s4`를 빼서 "데이터 준비
> 중"으로 표시하는 것 둘뿐 — 부분 전사·근사치·타 섹션 값 재사용 금지.

## 빌더 `s4` 필드

```json
"s4": { "names": ["표시이름1", "표시이름2", "표시이름3", "표시이름4", "표시이름5"] }
```

- `names`는 위 3에서 정한 표시 이름을 광고비 내림차순 그대로. 시리즈는 최상위 `series_file`
  (section-3 파일 참고)의 `top5.ctr_series`에서 빌더가 읽는다. 데이터가 비어있으면 `s4` 키를
  뺀다.
