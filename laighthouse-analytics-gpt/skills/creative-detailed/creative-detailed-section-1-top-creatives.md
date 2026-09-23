# Creative Section 1: 최우수 소재 (ROAS 또는 클릭 / CTR, 최근 7일 기준)

**report_type:** `creative-detailed` (항상 포함). **`chosen_media` 하나만 대상**(SKILL.md 매체
선택). 기준일 포함 **최근 7일을 통째로 합산**해 소재(개별 광고) 단위 **ROAS 1·2위**(매출 없음 모드:
**클릭 1·2위**)와 **CTR 1·2위**를 카드로 보여준다 — 날짜별 비교가 아니라 7일 누적 값 기준이다.
카드 제목·각주·값 라벨은 빌더가 `metric_keys`로 모드를 판정해 바꾼다.

> ℹ️ 카드 HTML(3행 구조, 이미지→링크 fallback, 각주)은 전부 `assets/report-template.html` +
> `assets/build_report.py`가 처리한다 — 모델은 아래 규칙으로 랭킹만 정해 빌더 입력 JSON의
> `s1`에 넣는다.

## MCP 도구 호출: `get_ad_performance` × 1 (`time_grain:"total"`, 소재 단위, 최근 7일)

```json
{ "brand_name": "<brand>", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "time_grain": "total", "group_by": ["campaign_name", "ad_group_name", "ad_name"], "filters": {"media": ["<chosen_media>"]} }
```

- 응답은 JSON 봉투(`rows` 배열)이며, 날짜별 행이 아니라 **소재(`campaign_name`+
  `ad_group_name`+`ad_name`)당 7일 전체를 서버가 이미 합산한 한 행**이다. 각 행에
  cost/impression/click(+revenue/conversion — 있을 때) 키 값과 7일 합산 기준으로 이미 계산된 서버 비율
  지표(% 값)가 함께 들어있다 — 매출 조인이 필요 없다. **이 응답은 section-5가 그대로
  재사용한다** — section-5는 다시 호출하지 않는다. section-3의 상위 5개 소재 선정도 이
  응답을 정렬해서 한다.
- ⚠️ **`filters`는 반드시 명시한다 — 생략 금지**(불필요한 매체 행으로 응답만 커진다). 값은
  디스커버리 응답의 `media` 문자열 그대로(정확 일치). 이 호출은 section-3의 day 1회와 함께
  한 메시지에 병렬 발사한다.
- `rows`가 비어있으면 이 매체에 소재 단위 데이터가 없다 — 사용자에게 알리고 다른 매체를
  고르게 한다(SKILL.md 4단계).
- ✅ **이 응답은 이미 작다(소재당 한 행) — 받은 그 자리에서 바로 정렬 결과를 낸다.**
  Bash도 스크립트도 스크래치 파일(`meta.tsv` 등)도 만들지 않고, 각 행을 자연어로 하나씩
  서술하지도 않는다(§ SKILL.md 실행 방식 절대 지침 — 실제 사고로 확정된 규칙).

## MCP 도구 호출: `get_ad_creative_info` (최종 선정 소재만, 랭킹 확정 후 순차 호출)

```json
{ "brand_name": "<brand>", "source": "<sources_of[chosen_media] 값>", "name_query": "{선정된 ad_name}" }
```

- ROAS(매출 없음: 클릭) 1·2위 + CTR 1·2위 소재(최대 4개, 중복은 유니크로) 각각에 대해
  `name_query`로 호출한다 — 전체 소재를 조회하지 않는다. `source`는 디스커버리 행에서
  `chosen_media`와 짝지어진 `source` 값(`sources_of`, SKILL.md 매체 선택 1)이다 — 여럿이면
  **전부** 소스마다 1회씩(골라내거나 제외하지 않는다). 소재 메타데이터가 없는 소스는 에러 없이
  `items: []`를 돌려주므로 빈 결과는 건너뛴다. 어느 소스에서도 못 찾으면 썸네일은 `null`. 응답은 `{"source": "elt", "items": [...]}` — `items[]`에서
  소재 이름이 정확히 일치하는 항목을 고른다.
- 항목의 `image_url`(서버 계산 이미지 URL)을 쓴다. ⚠️ 이미지 URL은 IP 화이트리스트 뒤에
  있어 허용되지 않은 네트워크에서는 안 뜰 수 있다 — 이미지 로드 실패 폴백은 템플릿이
  처리하므로 URL이 있으면 그대로 넣는다.

## 계산·선정 규칙

- 매출이 행에 이미 들어있으므로 **조인이 없다** — total 응답의 행만으로 랭킹을 정한다.
- 왼쪽 카드는 모드에 따라 다르다(SKILL.md **모드**):
  - **매출 있음**: ROAS = revenue 키 ÷ cost 키 × 100 내림차순 1·2위 (cost 0이면 제외).
  - **매출 없음**: click 키 값(7일 합) 내림차순 1·2위 — ROAS 대신 **클릭 1·2위**.
- 오른쪽 카드(두 모드 공통): CTR = click 키 ÷ impression 키 × 100 내림차순 1·2위
  (impression 0이면 제외). 소재당 1행이라 행의 서버 계산 비율 지표와 같은 값 — 있으면 그대로
  써도 된다(×100 금지).
- 각 랭킹 내림차순 1·2위. 두 랭킹은 독립(같은 소재가 양쪽 1위여도 그대로). 유효 후보가 2개
  미만이면 그 배열에 1개만 넣는다 — 2위 칸 `-`/이미지 생략은 빌더가 처리한다.

## 빌더 `s1` 필드

```json
"s1": {
  "roas": [ {"name": "{소재(광고) 이름만 — 캠페인/광고그룹명 붙이지 않음}", "value": 812.3, "thumbnail_url": "https://..."}, {...2위...} ],
  "ctr":  [ {"name": "...", "value": 4.9, "thumbnail_url": null}, ... ]
}
```
매출 없음 모드에서는 `roas` 대신 `"click": [ {"name": "<ad_name>", "value": 5321, "thumbnail_url": ...}, ... ]`
(value = 7일 합 클릭 수, 콤마 정수 포맷은 빌더가 한다). 빌더 입력 최상위의 `metric_keys`로
모드가 판정된다.

- ROAS/CTR `value`는 % 스케일 숫자 원본(소수 1자리 포맷은 빌더가 한다). `thumbnail_url`에는
  `get_ad_creative_info` 항목의 `image_url`을 넣는다 — 없으면 null.
- 유효 후보가 하나도 없으면(양쪽 다) `s1` 키를 빼서 "데이터 준비 중"으로 렌더링한다.
