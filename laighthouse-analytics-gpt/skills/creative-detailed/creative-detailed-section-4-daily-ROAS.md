# Creative Section 4: 최근 7일 일별 ROAS (광고비 상위 5개 소재)

**report_type:** `creative-detailed` (항상 포함). **`chosen_media` 하나만 대상**(SKILL.md 매체
선택). **section-3과 동일한 상위 5개 소재**(7일 합산 cost 키 기준)의 일별 ROAS를 라인
차트로 보여준다.

> ℹ️ 차트 HTML/Script는 템플릿+빌더가 처리한다(색상·범례 순서는 section-3과 동일 —
> `names`/`labels`를 빌더가 `s3`에서 공유). 모델은 ROAS 시리즈만 산출해 `s4`에 넣는다.

## MCP 도구 호출: 신규 호출 없음 — section-3의 공유 응답을 재사용

**section-3이 이미 받아둔 `get_ad_performance`(`time_grain:"day"`,
`filters:{"media":["<chosen_media>"]}`, 소재 단위) 응답**을 쓴다 — 매출(revenue 키)이 같은
행에 지표로 들어있어 별도 응답이 없다. section-3이
이미 가공한 결과(5개 소재 키·표시 이름)를 그대로 재사용한다 — 소재 선정·표시 이름을 다시
판단하지 않는다. section-3과 같은 방식(원본 JSON 봉투 문자열 대상 exact-match)으로 5개 키
행만 추출한다 — 이 환경에는 캡처 훅이 없다(`shared/references/gpt-large-response-guardrail.md`
참고).

## 일별 시리즈 (5개 키 × 7일 exact-match — bounded 작업, 전부 정확하게)

- **조인 없음**: `campaign_name`+`ad_group_name`+`ad_name` 세 필드 정확 일치(정규화/부분일치
  금지)로 그 날짜 행을 찾으면 revenue 키/cost 키 값이 그 행에 함께 있다.
- 날짜별 `ROAS` = revenue 키 ÷ cost 키 × 100. 행 하나가 곧 소재×날짜 단위라 응답에 서버 계산
  ROAS류 지표가 있으면 같은 값이다(이미 % 값 — ×100 금지).
- 그 날짜 cost가 0/없음이거나 행 자체가 없으면 그 날짜는 **`0`으로 채운다** — section-3의
  `null`과 달리 끊긴 구간으로 남기지 않는다(선이 0%까지 내려갔다 이어지는 형태 — Y축 `min:0`은
  템플릿에 있음). 빌더도 null이 오면 0으로 보정하지만, 모델이 처음부터 0으로 넣는다.

## 빌더 `s4` 필드

```json
"s4": { "roas_series": [[7개 값] ...s3.names와 같은 순서 5개...] }
```

- `names`/`labels`는 넣지 않는다 — 빌더가 `s3`에서 공유한다(그래서 `s3` 없이 `s4`만 넣으면
  placeholder가 된다). 데이터가 비어있으면 `s4` 키를 뺀다 → "데이터 준비 중" 카드.
