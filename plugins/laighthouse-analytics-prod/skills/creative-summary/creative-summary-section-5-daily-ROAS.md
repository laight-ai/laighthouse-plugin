# Breezm Executive Creative Section 5: 최근 7일 일별 ROAS (광고비 상위 5개 소재)

**report_type:** `creative-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
**메타(Meta Ads)만 대상.** **section-4와 동일한 상위 5개 소재**의 일별 ROAS 라인 차트
(`creative-detailed` section-4와 동일 내용, 번호만 4→5). 색상·범례 순서는 section-4와 동일
(같은 색 = 같은 소재), Y축 `min:0` 고정 — 전부 템플릿에 고정돼 있다.

## MCP 도구 호출: 신규 호출 없음

SKILL.md 2-b의 daily_table 응답(`media="airbridge"` 포함, section-3/4와 공유)을 재사용한다 —
다시 호출하지 않는다. airbridge 행에는 날짜별·소재별 `airbridge_revenue`가 들어있다(소재 단위
매출 귀속 정상 확인, 2026-08-03).

## 소재 선정·계산: section-4의 것을 그대로 재사용

- 상위 5개 소재·순서·표시 이름 전부 section-4에서 정한 것을 그대로 쓴다 — 다시 판단하지
  않는다.
- 일별 ROAS 시리즈는 section-4가 이미 호출한 `assets/creative_daily_series.py`의 **같은 출력
  파일**의 `top5.roas_series`다 — 이 섹션에서 스크립트를 다시 호출하지 않는다.
- 스크립트가 구현한 계산(참고용 스펙): `campaign_name`+`asset_group`+`ad_name` 세 필드 정확
  일치 조인으로 그 날짜 `airbridge_revenue`÷그 날짜 `cost`×100. 매체 쪽 cost가 0/없거나 조인
  실패면 그 날짜는 **`0`으로 채운다**(끊긴 구간으로 남기지 않는다 — section-5 고유 스펙,
  section-4의 CTR null 처리와 다르다).

> 🚫 응답이 커도 선택지는 (1) 원본 전부를 스크립트에 넘기거나 (2) `s5`를 빼서 "데이터 준비
> 중"으로 표시하는 것 둘뿐 — 부분 전사·근사치·타 섹션 값 재사용 금지.

## 빌더 `s5` 필드

```json
"s5": {}
```

- `s5` 키를 존재시키기만 하면 된다 — 시리즈는 최상위 `series_file`의 `top5.roas_series`,
  표시 이름은 `s4.names`를 빌더가 공유한다. 데이터가 비어있으면 `s5` 키를 뺀다.
