# Breezm Executive Creative Section 1: 최우수 소재 (ROAS / CTR, 최근 7일 기준)

**report_type:** `creative-summary` — **브리즘(airbridge 기반) 전용** (항상 포함).
**메타(Meta Ads)만 대상**이다. 기준일 포함 **최근 7일을 통째로 합산**한 소재(개별 광고) 단위
**ROAS 1·2위**와 **CTR 1·2위**를 카드로 보여준다 (`creative-detailed` section-1과 동일 내용).

> ℹ️ 카드 HTML(3행 표 구조, 이미지 onerror 폴백, 각주)은 전부 `assets/report-template.html` +
> `assets/build_report.py`가 처리한다 — 모델은 아래 규칙으로 랭킹만 정해서 빌더 입력 JSON의
> `s1`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (`time_grain:"total"`, 소재 단위, 최근 7일)

```json
{ "brand_name": "breezm", "media": "Meta", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "time_grain": "total", "group_by": ["campaign_name", "ad_group_name", "ad_name"] }
```

- 이 호출은 구간 전체를 **소재당 1행으로 서버가 이미 합산**해 돌려준다 — 응답(JSON 봉투,
  `rows` 배열)이 그 자체로 최종 데이터라 별도 집계가 필요 없다(정렬만 하면 랭킹이 나온다).
- ⚠️ **`media`를 생략하지 않는다** — 소재 단위에서 생략하면 다른 매체 행까지 섞여 온다.
- 각 행: 소재(`campaign_name`+`ad_group_name`+`ad_name`)별 7일 합산
  `광고비`/`노출`/`클릭`/`매출_AB`/`예약완료_AB` + 7일 합산 기준으로 이미 계산된 비율 지표
  `CTR`/`ROAS_AB`(% 값) — 매출 조인이 필요 없다.
- 이 응답은 section-3/4/5와 공유되지 않는다(그쪽은 날짜별 day grain 응답이 별도로 필요).
  단, **section-4의 "광고비 상위 5개" 선정은 이 응답의 7일 합산 `광고비`를 그대로 쓴다**
  (재집계 불필요 — section-4 파일 참고).

## MCP 도구 호출: `get_ad_creative_info` (최종 선정된 소재만, 최대 4회)

```json
{ "brand_name": "breezm", "source": "meta_ads", "name_query": "{선정된 ad_name}" }
```

- 아래 선정 로직으로 ROAS 1·2위 + CTR 1·2위를 먼저 정한 뒤, 그 소재들(최대 4개, 중복은
  유니크하게) 각각에 대해 `name_query`로 호출한다 — 전체 소재를 조회하지 않는다
  (`source` ∈ google_ads|meta_ads|naver_search_ads|tiktok_ads, 이 스킬은 항상 `meta_ads`).
- 응답 `{"source": "elt", "items": [...]}`의 `items[]`에서 소재 이름이 정확히 일치하는 항목의
  `image_url`을 쓴다. ⚠️ 이미지 URL은 IP 화이트리스트 뒤에 있어 허용되지 않은 네트워크에서는
  안 뜰 수 있다 — 이미지 로드 실패 폴백은 빌더/템플릿이 처리한다.

## 선정 로직

- 매출/예약이 행에 이미 들어있으므로 **조인이 없다** — total 응답의 행만으로 랭킹을 정한다.
- `CTR`/`ROAS`는 행의 서버 계산 지표 `CTR`/`ROAS_AB`(이미 % 값 — ×100 금지)를 그대로 쓴다.
  노출 0(CTR null/0)이면 CTR 랭킹 제외, 광고비 0(ROAS null)이면 ROAS 랭킹 제외.
- ROAS/CTR 각각 내림차순 1·2위 — 두 랭킹은 독립(같은 소재가 양쪽 1위여도 그대로 둔다).
- 유효 후보가 2개 미만이면 2위 항목을 빼면 된다 — `-` 표시·이미지 미표시는 빌더가 처리한다.

## 빌더 `s1` 필드

```json
"s1": {
  "roas": [ {"name": "소재명", "value": 388.05, "thumbnail_url": "https://..."}, {...2위...} ],
  "ctr":  [ {"name": "소재명", "value": 2.41, "thumbnail_url": null} ]
}
```

- `value`는 숫자 원본 그대로(% 소수 1자리 포맷은 빌더가 한다). `name`은 소재(광고) 이름만 —
  캠페인/광고그룹명을 덧붙이지 않는다.
- `thumbnail_url`은 `get_ad_creative_info` 항목의 `image_url` — 없으면 `null`(이미지 셀
  비움). 각 배열은 1·2위 순서, 2위 없으면 1개만.
- 데이터가 비어있으면 `s1` 자체를 빼면 "데이터 준비 중" 카드로 렌더링된다 — 임의로 채우지
  않는다.
