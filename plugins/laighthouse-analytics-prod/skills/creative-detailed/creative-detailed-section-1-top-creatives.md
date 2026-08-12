# Breezm Creative Section 1: 최우수 소재 (ROAS / CTR, 최근 7일 기준)

**report_type:** `creative-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). **메타
(Meta Ads)만 대상.** 기준일 포함 **최근 7일을 통째로 합산**해 소재(개별 광고) 단위
**ROAS 1·2위**와 **CTR 1·2위**를 카드로 보여준다 — 날짜별 비교가 아니라 7일 누적 값 기준이다.

> ℹ️ 카드 HTML(3행 구조, 이미지→링크 fallback, 각주)은 전부 `assets/report-template.html` +
> `assets/build_report.py`가 처리한다 — 모델은 아래 규칙으로 랭킹만 정해 빌더 입력 JSON의
> `s1`에 넣는다.

## MCP 도구 호출: `get_ad_performance_range_table` × 2 (`group_by:"ad"`, 최근 7일)

```json
{ "brand_name": "breezm", "media": "meta", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
{ "brand_name": "breezm", "media": "airbridge", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "group_by": "ad" }
```

- 응답은 날짜별 행이 아니라 **소재(`campaign_name`+`asset_group`+`ad_name`)당 7일 전체를 이미
  합산한 한 행**이다 (`is_active`는 항상 None — 무시). **이 두 응답은 section-5가 그대로
  재사용한다** — section-5는 다시 호출하지 않는다. section-3의 상위 5개 소재 선정도 이 meta
  응답을 정렬해서 한다.
- ⚠️ **`media`는 반드시 명시한다 — 생략 금지**(불필요한 매체 행으로 응답만 커진다). 두 호출은
  서로 의존하지 않으므로 section-3의 daily 2회와 함께 한 메시지에 병렬 발사한다.
- ⚠️ `campaign-type` 금지. `group_by`는 문자열 `"ad"` 그대로.
- ✅ **이 응답은 이미 작다(소재당 한 행) — 받은 그 자리에서 바로 조인·정렬 결과를 낸다.**
  Bash도 스크립트도 스크래치 파일(`meta.tsv` 등)도 만들지 않고, 각 행을 자연어로 하나씩
  서술하지도 않는다(§ SKILL.md 실행 방식 절대 지침 — 실제 사고로 확정된 규칙).

## MCP 도구 호출: `get_ad_creative_info` × 1 (최종 선정 소재만, 랭킹 확정 후 순차 호출)

```json
{ "brand_name": "breezm", "meta": [ { "account_id": "{platform_account_id}", "creative_id": "{creative_id}" }, ... ] }
```

- ROAS 1·2위 + CTR 1·2위의 `platform_account_id`/`creative_id` 쌍만(최대 4개, 중복은 유니크로)
  모아 **1회** 호출한다 — 전체 소재를 조회하지 않는다. 두 값은 meta 응답 행에 들어있다.
- 결과의 `thumbnail_image_url`만 쓴다 — `thumbnail_image_data_url`(base64)은 쓰지 않는다.

## 계산·선정 규칙

- **조인**: meta 행과 airbridge 행을 `campaign_name`+`asset_group`+`ad_name` **세 필드 정확
  일치**로 조인한다(정규화/부분일치 금지). airbridge 미매칭 소재 → ROAS 랭킹 제외(CTR 랭킹은
  가능). 매체 쪽에 없는 airbridge 소재 → 이 섹션 전체에서 제외.
- `CTR` = `click` ÷ `impression` × 100 (노출 0이면 CTR 랭킹 제외).
  `ROAS` = `airbridge_revenue` ÷ `cost` × 100 (광고비 0이면 ROAS 랭킹 제외).
- 각 랭킹 내림차순 1·2위. 두 랭킹은 독립(같은 소재가 양쪽 1위여도 그대로). 유효 후보가 2개
  미만이면 그 배열에 1개만 넣는다 — 2위 칸 `-`/이미지 생략은 빌더가 처리한다.

## 빌더 `s1` 필드

```json
"s1": {
  "roas": [ {"name": "{소재(광고) 이름만 — 캠페인/광고그룹명 붙이지 않음}", "value": 812.3, "thumbnail_url": "https://..."}, {...2위...} ],
  "ctr":  [ {"name": "...", "value": 4.9, "thumbnail_url": null}, ... ]
}
```

- `value`는 % 스케일 숫자 원본(소수 1자리 포맷은 빌더가 한다). `thumbnail_url`이 없으면 null.
- 유효 후보가 하나도 없으면(양쪽 다) `s1` 키를 빼서 "데이터 준비 중"으로 렌더링한다.
