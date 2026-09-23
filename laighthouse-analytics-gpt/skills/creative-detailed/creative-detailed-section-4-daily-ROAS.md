# Creative Section 4: 최근 7일 일별 ROAS — 매출 없음: 일별 클릭 — (광고비 상위 5개 소재)

**report_type:** `creative-detailed` (항상 포함). **`chosen_media` 하나만 대상**(SKILL.md 매체
선택). **section-3과 동일한 상위 5개 소재**(7일 합산 cost 키 기준)의 일별 ROAS(매출 없음 모드:
**일별 클릭**)를 라인 차트로 보여준다.

> ℹ️ 차트 HTML/Script는 템플릿+빌더가 처리한다(색상·범례 순서는 section-3과 동일 —
> `names`를 빌더가 `s3`에서 공유, 모드별 제목·단위(% / 클릭 수)도 빌더가 정한다).

## MCP 도구 호출: 신규 호출 없음 — section-3의 공유 응답을 재사용

**section-3이 이미 받아둔 `get_ad_performance`(`time_grain:"day"`,
`filters:{"media":["<chosen_media>"]}`, 소재 단위) 응답**을 쓴다 — 매출(revenue 키, 있을 때)이
같은 행에 지표로 들어있어 별도 응답이 없다. 소재 선정·표시 이름은 section-3에서 정한 것을 그대로
쓴다.

## 일별 시리즈: section-3이 실행한 `assets/creative_daily_series.py`의 같은 출력 파일

- 이 섹션에서 스크립트를 다시 호출하지 않는다 — section-3의 한 번 호출 출력
  (`series_file`)에 `top5.roas_series`(매출 있음)와 `top5.click_series`가 함께 들어 있고, 어느
  쪽을 쓸지는 빌더가 `metric_keys`로 정한다.
- 스크립트가 구현한 계산(참고용 스펙): `campaign_name`+`ad_group_name`+`ad_name` 세 필드 정확
  일치로 그 날짜 행을 찾아 ROAS = revenue 키 ÷ cost 키 × 100(서버 비율 지표를 합산하지 않음),
  클릭 = click 키 값. 행 자체가 없거나(ROAS는 cost 0/없음도) 그 날짜는 **`0`으로 채운다** —
  section-3의 `null`과 달리 끊긴 구간으로 남기지 않는다(Y축 `min:0`은 템플릿에 있음). 빌더도
  null이 오면 0으로 보정한다.

## 빌더 `s4` 필드

```json
"s4": {}
```

- `s4` 키를 존재시키기만 하면 된다 — 시리즈는 최상위 `series_file`, `names`/라벨은 `s3`와
  공유한다(그래서 `s3` 없이 `s4`만 넣으면 placeholder가 된다). 데이터가 비어있으면 `s4` 키를
  뺀다 → "데이터 준비 중" 카드.
