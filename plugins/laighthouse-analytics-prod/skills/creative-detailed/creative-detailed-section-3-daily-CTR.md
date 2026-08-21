# Breezm Creative Section 3: 최근 7일 일별 CTR (광고비 상위 5개 소재)

**report_type:** `creative-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). **메타
(Meta Ads)만 대상.** 기준일 포함 최근 7일 동안 **광고비(7일 합산) 상위 5개 소재**의 일별
CTR을 라인 차트로 보여준다.

> ℹ️ 차트 HTML/Script(색상 palette, spanGaps 등)는 전부 템플릿+빌더가 처리한다 — 모델은 아래
> 규칙으로 소재 5개 선정과 7일치 시리즈만 산출해 빌더 입력 JSON의 `s3`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (`time_grain:"day"`, 소재 단위, 최근 7일) — section-3이 신규 호출

```json
{ "brand_name": "breezm", "media": "Meta", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "time_grain": "day", "group_by": ["campaign_name", "ad_group_name", "ad_name"] }
```

- section-1의 total 응답(소재당 7일 합산 한 행)과는 **grain이 다르다** — section-3/4는
  **날짜별 값**(일별 트렌드, 행마다 `date` 키)이 필요해 total로는 만들 수 없다. **section-4가
  이 응답을 그대로 재사용**한다. 이 호출은 section-1의 total 1회와 함께 한 메시지에 병렬
  발사한다. 매출(`매출_AB`)이 각 행에 지표로 들어있어 별도 매출 호출이 없다.
- ⚠️ **`media`를 생략해서 한 번에 받지 않는다** — 소재 단위는 고카디널리티라(마크다운 시절
  meta 단독 7일 응답 실측 13만 자+, 생략 시 76만 자+) 통합은 금지된 회귀다(실제 근사치 사고
  원인).

## 소재 선정 (section-1의 total 응답 재사용 — 신규 계산 없음)

1. section-1의 total 응답(소재당 7일 합산 `광고비`)을 내림차순 정렬해 **상위 5개 소재의
   키(`campaign_name`+`ad_group_name`+`ad_name`)**를 뽑는다 — 응답이 이미 작아 사소한 정렬이다.
   이 5개 키·순서는 section-4와 공유한다(두 차트의 색상·범례 순서 일치).
2. **표시 이름**: 5개 중 `ad_name`이 중복되면 그 소재들만 `{ad_name} ({ad_group_name})`으로
   구분하고, 유일하면 `ad_name`만 쓴다(불필요하게 전부 괄호를 붙이지 않는다).

## 일별 시리즈 추출 (이미 알고 있는 5개 키만, exact-match — bounded 작업)

- 위 day 응답에서 **5개 키 × 7일만** exact-match로 걸러낸다 — 전체 소재 집계·랭킹이
  아니다. 그래도 **필수 절차이며 전부 정확하게** 수행한다(일부만 훑고 추정 금지).
- **응답이 `[laighthouse-capture-hook] ... 저장됨: <경로>` 스텁으로 오면**(캡처 훅 동작 호스트)
  그 저장 파일(JSON 봉투)을 입력으로 즉석 Bash(python) 1회로 5개 키 행만 추출한다 —
  원본을 Read로 통째로 열거나 컨텍스트에 재타이핑하지 않는다. 원본이 그대로 오면 컨텍스트에서
  바로 걸러낸다(별도 파일/스크립트 불필요).
- 날짜별 `CTR` = 그 날짜 행의 서버 계산 `CTR` 지표(이미 % 값 — ×100 금지. 행 하나가 곧
  소재×날짜 단위라 그대로 쓸 수 있다) 또는 `클릭`÷`노출`×100 — 같은 값이다.
- 노출 0인 날, 행 자체가 없는 날(미게재)은 **`null`**로 둔다 — 0으로 채우지 않는다
  (차트에서 끊긴 구간, `spanGaps:false`는 템플릿에 있음).

## 빌더 `s3` 필드

```json
"s3": {
  "names": ["표시이름1", ...5개, 광고비 내림차순...],
  "ctr_series": [[7개 값, 없는 날은 null], ...names와 같은 순서...],
  "labels": 생략 (빌더가 target_date 기준 "M/D" 7개 자동 생성)
}
```

- 유효한 소재가 하나도 없으면 `s3` 키를 뺀다 → "데이터 준비 중" 카드. `s3`의 `names`는
  section-4 차트도 공유한다 — `s3` 없이 `s4`만 넣으면 s4도 placeholder가 된다.
