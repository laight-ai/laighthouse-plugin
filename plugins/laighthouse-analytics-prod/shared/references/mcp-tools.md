# MCP 도구 라우팅 규칙 (laighthouse 서버 — 전 스킬 공용)

`laighthouse` MCP 서버가 제공하는 도구 인벤토리와 사용 규칙의 단일 소스(single source of
truth)다. 서버가 ELT 기반으로 개편되면서(2026-08) 도구 수가 대폭 줄었다 — **아래 6개가
전부다.** 여기 없는 도구 이름(예전의 daily/range/monthly 표 도구 3종, SKU 매출 계열,
naver 전용 계열, v1 target_progress, 리포트 공유 계열)은 **서버에서 제거되어 더 이상
존재하지 않는다** — 호출하면 unknown tool 에러다.

## 1. `get_ad_performance` — 광고 성과 (유일한 성과 조회 도구)

예전의 daily/range/monthly 3종 표 도구를 하나로 통합한 도구다. 시그니처:

```json
{
  "brand_name": "breezm",
  "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD",
  "time_grain": "day" | "month" | "total",        // 기본 "day"
  "group_by": ["media", "campaign_id", "campaign_name"],  // 차원명 리스트, 생략 시 총계
  "metrics": ["광고비", "매출_AB"],                 // 생략 시 테넌트 전체 지표
  "media": "Google" | "Meta" | "Naver",            // 생략 시 전 매체
  "day_offset": 15                                  // month grain 전용 — 각 월을 N일까지 자름
}
```

- **time_grain 매핑(구 도구 대응)**: 일별 표(`daily_table`) → `"day"`, 구간 합산 표
  (`range_table`) → `"total"`, 월별 표(`monthly_table` + `day_offset`) → `"month"`(+
  `day_offset`).
- **group_by 매핑(구 문자열 enum 대응)**: `total` → group_by 생략 / `media` → `["media"]` /
  `campaign` → `["campaign_id","campaign_name"]` / `ad-set` → `["ad_group_id","ad_group_name"]` /
  `ad` → `["ad_id","ad_name"]`. 필요한 상위 차원(예: `media`, `campaign_name`)을 리스트에
  추가해 함께 받을 수 있다.
- **응답은 markdown 표가 아니라 JSON 봉투다**:

```json
{ "source": "elt", "tenant": "breezm", "time_grain": "day",
  "dimensions": ["media"], "metrics": ["광고비", "..."], "row_count": 42,
  "rows": [ { "date": "2026-08-01", "media": "Google", "광고비": 12345, "매출_AB": 67890, "...": 0 } ] }
```

  - 행의 **차원 키는 영문**: `date`(day grain) / `month`(month grain, "YYYY-MM") / `media` /
    `source` / `campaign_id`/`campaign_name` / `ad_group_id`/`ad_group_name` /
    `ad_id`/`ad_name` / `ad_type`.
  - 행의 **지표 키는 테넌트별**이다 — 브리즘(breezm)은 한국어 지표명: `광고비`(비용) /
    `노출`(impressions) / `클릭`(clicks) / `매출_AB`(Airbridge 매출) / `예약완료_AB`(Airbridge
    예약)과 서버 계산 비율 지표 `ROAS_AB` / `CPM` / `CTR` / `CVR` / `CPA` / `CPA_AB`.
    **응답의 `metrics` 목록이 유효한 지표 키의 유일한 진실이다** — 키를 추측하지 않는다.
  - ⚠️ 비율 지표는 **요청한 grain 기준으로 서버가 이미 계산한 % 값**이다(`ROAS_AB` 122.4 =
    122.4%) — ×100 하지 않고, **행별 비율 값을 합산/평균해 상위 기간·상위 그룹 비율을 만들지
    않는다**(필요하면 원자 지표 합으로 다시 계산).
  - `media` 필터 값은 `"Google"`/`"Meta"`/`"Naver"` — 대소문자 변형과 한국어 표기는 서버가
    흡수한다. 예전의 `media="airbridge"` 행/`channel` 컬럼 개념은 사라졌다 — Airbridge 귀속
    매출·예약은 각 행의 `매출_AB`/`예약완료_AB` 지표로 함께 온다(별도 조인 불필요).
  - ⚠️ 그 대가로 **전체(오거닉 포함) 매출과 `Organic`/`Others` 채널 구분은 현재 제공되지
    않는다** — 해당 값이 필요한 섹션은 각 섹션 파일 규칙대로 `-`/"데이터 준비 중" 처리한다.

## 2. `get_ad_creative_info` — 소재 메타데이터/이미지

```json
{ "brand_name": "breezm", "source": "meta_ads", "name_query": "AD_251212_old5059_02", "limit": 20 }
```

- `source` ∈ `google_ads`|`meta_ads`|`naver_search_ads`|`tiktok_ads` (선택), `name_query`는
  소재 이름 검색(선택), `limit`은 개수 제한(선택).
- 응답은 JSON: `{"source": "elt", "items": [...]}` — 각 항목은 광고 메타데이터 행이며 서버
  계산 `image_url`을 포함한다. ⚠️ **이미지 URL은 IP 화이트리스트 뒤에 있다** — 허용되지 않은
  네트워크에서는 이미지가 렌더링되지 않을 수 있다(오류 아님, 템플릿 onerror 폴백으로 처리).
- 예전 시그니처(`meta: [{account_id, creative_id}]` 배열,
  `thumbnail_image_url`/`thumbnail_image_data_url` 필드)는 폐기됐다.

## 3. `get_target_progress_v2` — 월 목표 대비 진행 (계약 불변)

```json
{ "brand_name": "breezm", "month": "YYYY-MM", "media": "naver"|"google"|"meta"|"tiktok", "as_of_date": "YYYY-MM-DD" }
```

- **이 도구만 여전히 markdown 표를 반환한다** — 행(cost/revenue/roas) × 열(target|actual|
  progress_ratio). 해당 매체 예산이 전혀 없으면 리터럴
  `"No {media} budget/target available for {month}."` 한 줄이 반환된다 — **오류가 아니다**.
- ⚠️ ROAS류 수치는 비율값(예: 0.87, 5.06)이므로 반드시 ×100 후 표시한다 (0.87 → 87%).
- `revenue` 행의 `actual`은 매출 실적으로 쓰지 않는다 — 실적 매출은 항상
  `get_ad_performance`의 `매출_AB`에서 가져온다 (naver actual 0 반환 사례 실측).

## 4. `get_naver_channel_budget_progress` — naver 채널별 예산 진행

- 시그니처·응답 불변(사용 스킬: `mid-month-optimizer`). 서버 측에서는 deprecated로 표시됐지만
  동작한다 — 신규 스킬에서 새로 채택하지는 않는다.

## 5. `get_brand_list` — 브랜드 목록 (불변)

## 6. `list_promotions` — 프로모션 목록 (불변)

```json
{ "brand_name": "breezm", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }
```

- 응답 `items[]`의 `{title, date_begin, date_end}`를 각 스킬 빌더에 가공 없이 넘긴다.

## 공통 규칙

- 모든 호출의 `brand_name`은 정확한 영문 브랜드명(예: `"breezm"`)이다 — 한국어 표시명을 넣으면
  `Unknown brand` 에러.
- Executive Summary류 분석 텍스트는 `df_dify` MCP를 호출하지 않고, 이미 수집한 수치 데이터를
  근거로 실행 LLM이 직접 작성한다 (근거 수치가 없으면 생성하지 않음).
- 고카디널리티 응답(campaign/ad 차원)은 이 플러그인의 PostToolUse 캡처 훅
  (`hooks/capture_ad_performance.py`)이 파일로 우회시킨다 — 스텁에 적힌 경로를 asset
  스크립트의 `json_files` 입력으로 그대로 넘긴다(원본 재타이핑 금지).
