# Executive Creative Section 1: 최우수 소재 (ROAS / CTR, 최근 7일 기준)

**report_type:** `creative-summary` (항상 포함). **`chosen_media` 하나만 대상**이다(SKILL.md
매체 선택). 기준일 포함 **최근 7일을 통째로 합산**한 소재(개별 광고) 단위 **ROAS 1·2위**와
**CTR 1·2위**를 카드로 보여준다 (`creative-detailed` section-1과 동일 내용).

> ℹ️ 카드 HTML(3행 표 구조, 이미지 onerror 폴백, 각주)은 전부 `assets/report-template.html` +
> `assets/build_report.py`가 처리한다 — 모델은 아래 규칙으로 랭킹만 정해서 빌더 입력 JSON의
> `s1`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (`time_grain:"total"`, 소재 단위, 최근 7일)

```json
{ "brand_name": "<brand>", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "time_grain": "total", "group_by": ["campaign_name", "ad_group_name", "ad_name"], "filters": {"media": ["<chosen_media>"]} }
```

- 이 호출은 구간 전체를 **소재당 1행으로 서버가 이미 합산**해 돌려준다 — 응답(JSON 봉투,
  `rows` 배열)이 그 자체로 최종 데이터라 별도 집계가 필요 없다(정렬만 하면 랭킹이 나온다).
- ⚠️ **`filters`를 생략하지 않는다** — 소재 단위에서 생략하면 다른 매체 행까지 섞여 온다.
  값은 디스커버리 응답의 `media` 문자열 그대로(정확 일치).
- 각 행: 소재(`campaign_name`+`ad_group_name`+`ad_name`)별 7일 합산 cost/impression/click/
  revenue 키 값 + 7일 합산 기준으로 이미 계산된 서버 비율 지표(% 값, 이름은 `metric_names`
  참고 — 예: `CTR`, `ROAS*`) — 매출 조인이 필요 없다.
- `rows`가 비어있으면 이 매체에 소재 단위 데이터가 없다 — 사용자에게 알리고 다른 매체를
  고르게 한다(SKILL.md 3-a).
- 이 응답은 section-3/4/5와 공유되지 않는다(그쪽은 날짜별 day grain 응답이 별도로 필요).
  단, **section-4의 "광고비 상위 5개" 선정은 이 응답의 7일 합산 cost 키를 그대로 쓴다**
  (재집계 불필요 — section-4 파일 참고).

## MCP 도구 호출: `get_ad_creative_info` (최종 선정된 소재만, 소재당 소스 수만큼)

```json
{ "brand_name": "<brand>", "source": "<sources_of[chosen_media] 값>", "name_query": "{선정된 ad_name}" }
```

- 아래 선정 로직으로 ROAS 1·2위 + CTR 1·2위를 먼저 정한 뒤, 그 소재들(최대 4개, 중복은
  유니크하게) 각각에 대해 `name_query`로 호출한다 — 전체 소재를 조회하지 않는다.
- `source`는 디스커버리 행에서 `chosen_media`와 짝지어진 `source` 값이다(`sources_of`).
  여럿이면 소스마다 1회씩. 서버가 그 값을 거절하면(지원 소스 아님) 썸네일은 `null`로 둔다.
- 응답 `{"source": "elt", "items": [...]}`의 `items[]`에서 소재 이름이 정확히 일치하는 항목의
  `image_url`을 쓴다. ⚠️ 이미지 URL은 IP 화이트리스트 뒤에 있어 허용되지 않은 네트워크에서는
  안 뜰 수 있다 — 이미지 로드 실패 폴백은 빌더/템플릿이 처리한다.

## 선정 로직

- 매출이 행에 이미 들어있으므로 **조인이 없다** — total 응답의 행만으로 랭킹을 정한다.
- CTR = click 키 ÷ impression 키 × 100, ROAS = revenue 키 ÷ cost 키 × 100 (소재당 1행이라
  행의 서버 계산 비율 지표와 같은 값 — 있으면 그대로 써도 된다, ×100 금지).
  impression 0(CTR null/0)이면 CTR 랭킹 제외, cost 0(ROAS null)이면 ROAS 랭킹 제외.
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
