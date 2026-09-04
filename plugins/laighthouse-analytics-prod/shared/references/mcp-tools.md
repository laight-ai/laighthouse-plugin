# MCP 도구 라우팅 규칙 (laighthouse 서버 — 전 스킬 공용)

`laighthouse` MCP 서버가 제공하는 도구 인벤토리와 사용 규칙의 단일 소스(single source of
truth)다. 서버가 ELT 기반으로 개편되면서(2026-08) 도구 수가 대폭 줄었다 — **스킬이 쓰는 도구는 아래 5개가
전부다**(서버에는 헬스체크용 `ping`이 추가로 등록되어 있으나 스킬은 쓰지 않는다). 여기 없는 도구 이름(예전의 daily/range/monthly 표 도구 3종, SKU 매출 계열,
naver 전용 계열, v1 target_progress, 리포트 공유 계열)은 **서버에서 제거되어 더 이상
존재하지 않는다** — 호출하면 unknown tool 에러다.

## 1. `get_ad_performance` — 광고 성과 (유일한 성과 조회 도구)

예전의 daily/range/monthly 3종 표 도구를 하나로 통합한 도구다. 시그니처:

```json
{
  "brand_name": "<brand>",
  "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD",
  "time_grain": "day" | "month" | "total",        // 기본 "day"
  "group_by": ["media", "campaign_id", "campaign_name"],  // 차원명 리스트, 생략 시 총계
  "metrics": ["광고비", "매출_AB"],                 // 생략(null) 시 전체 지표, [] 이면 차원만(디스커버리)
  "filters": {"media": ["<디스커버리로 받은 값>"]},   // 차원 → 허용값 리스트, 정확 일치. 생략 시 전체
  "day_offset": 15                                  // month grain 전용 — 각 월을 N일까지 자름
}
```

- 예전의 `media: str` 파라미터는 **제거됐다** — 매체 필터는 `filters={"media": [...]}`로 한다.
  값은 디스커버리 응답에 나온 문자열 그대로(정확 일치)만 쓴다.
- `metrics`: 생략(null) → 테넌트의 공개 지표 전부 / `[]` → 지표 없이 차원만(디스커버리 모드) /
  리스트 → 그 지표만. 알 수 없는 지표명·차원명을 넣으면 서버가 유효한 이름 목록을 담은
  ValueError를 돌려준다 — 그 목록으로 바로잡는다(추측 재시도 금지).
- **검증 규칙(서버가 ValueError로 거절)**: `metrics:[]`는 `time_grain:"day"`가 아니면 비어 있지
  않은 `group_by`가 필요하다. `filters`는 알 수 없는 차원 키, `"date"` 키, 빈 값 리스트(`[]`)를
  거절한다. 서버 에러 메시지는 **그대로** 사용자에게 전달한다(재해석·추측 재시도 금지).
- **ELT 테넌트가 없는 브랜드(레거시 DB 폴백)**: `filters`와 null이 아닌 `metrics`를 거절하고
  `group_by`는 최대 1개만 허용한다 — 따라서 이 문서의 브랜드 비종속 패턴(디스커버리 `metrics:[]`,
  `filters` 매체 필터)은 **ELT 테넌트가 있는 브랜드에서만** 동작한다. 서버 에러를 그대로 전달한다.
- **상한**: 조회 구간은 `day`/`total` 366일, `month` 730일까지; 응답은 50,000행이 한도다.
- **time_grain 매핑(구 도구 대응)**: 일별 표(`daily_table`) → `"day"`, 구간 합산 표
  (`range_table`) → `"total"`, 월별 표(`monthly_table` + `day_offset`) → `"month"`(+
  `day_offset`).
- **group_by 매핑(구 문자열 enum 대응)**: `total` → group_by 생략 / `media` → `["media"]` /
  `campaign` → `["campaign_id","campaign_name"]` / `ad-set` → `["ad_group_id","ad_group_name"]` /
  `ad` → `["ad_id","ad_name"]`. 필요한 상위 차원(예: `media`, `campaign_name`)을 리스트에
  추가해 함께 받을 수 있다.
- **응답은 markdown 표가 아니라 JSON 봉투다**:

```json
{ "source": "elt", "tenant": "<brand>", "time_grain": "day",
  "dimensions": ["media"], "metrics": ["광고비", "..."], "row_count": 42,
  "rows": [ { "date": "2026-08-01", "media": "Google", "광고비": 12345, "매출_AB": 67890, "...": 0 } ] }
```

  - 행의 **차원 키는 영문**: `date`(day grain) / `month`(month grain, "YYYY-MM") / `media` /
    `source` / `campaign_id`/`campaign_name` / `ad_group_id`/`ad_group_name` /
    `ad_id`/`ad_name` / `ad_type`.
  - 행의 **지표 키는 테넌트별**이다 — 브랜드마다 이름이 다르다(한국어/영문/접미사 등).
    **응답의 `metrics` 목록이 유효한 지표 키의 유일한 진실이다** — 키를 추측하지 않는다.
    보고서의 고정 역할(cost/impression/click/revenue/conversion)에 어떤 키를 쓸지는
    `generic-report-pattern.md`의 **지표 역할 해석 규칙**으로 실행마다 한 번 결정한다.
  - ⚠️ 비율 지표는 **요청한 grain 기준으로 서버가 이미 계산한 % 값**이다(예: ROAS 122.4 =
    122.4%) — ×100 하지 않고, **행별 비율 값을 합산/평균해 상위 기간·상위 그룹 비율을 만들지
    않는다**(필요하면 원자 지표 합으로 다시 계산).
  - **매체 디스커버리**: `media`는 지표가 아니라 차원이며, 브랜드마다 값 집합이 다르다. 고정
    매체 목록을 어디에도 가정하지 않고, 매 실행 시작에
    `time_grain:"total", group_by:["media"], metrics:[]` 1회 호출로 실제 값을 받는다(절차는
    `generic-report-pattern.md`). **`media`가 `null`인 행이 Organic**(광고비 없이 매출만
    귀속)이다 — 정상 행이며 cost/impression/click은 항상 비어 있으므로 채우지 않는다.
    브랜드에 `media` 차원이 없어 호출이 실패하면 `group_by:["source"]`로 폴백해 `source`
    값을 매체 목록으로 쓴다. 표시명은 응답 값 그대로(접미사·번역 없음).

## 2. `get_ad_creative_info` — 소재 메타데이터/이미지

```json
{ "brand_name": "<brand>", "source": "meta_ads", "name_query": "AD_251212_old5059_02", "limit": 20 }
```

- `source`는 닫힌 enum이 아니라 **정확 일치 필터**다(선택, 임의 문자열). 마트의 `source` 차원
  값 — 디스커버리를 `group_by:["media","source"]`로 호출하면 행에 함께 나온다 — 을 그대로
  넣는다. 마트에 없는 값을 넣으면 **에러가 아니라 `items: []`**가 돌아온다(값을 추측하지
  않는다). `name_query`는 소재 이름 검색(선택), `limit`은 개수 제한(선택).
- 응답은 JSON: `{"source": "elt", "items": [...]}` — 각 항목은 광고 메타데이터 행이며 서버
  계산 `image_url`을 포함한다. ⚠️ **이미지 URL은 IP 화이트리스트 뒤에 있다** — 허용되지 않은
  네트워크에서는 이미지가 렌더링되지 않을 수 있다(오류 아님, 템플릿 onerror 폴백으로 처리).
- 예전 시그니처(`meta: [{account_id, creative_id}]` 배열,
  `thumbnail_image_url`/`thumbnail_image_data_url` 필드)는 폐기됐다.

## 3. `get_target_progress_v2` — 월 목표 대비 진행

```json
{ "brand_name": "<brand>", "month": "YYYY-MM", "as_of_date": "YYYY-MM-DD" }
```

- **`media` 생략(기본, 권장)**: naver/google/meta/tiktok 4개 매체 블록이 빈 줄로 이어붙어
  한 번에 온다 — 블록마다 자기 `media: <값>` 헤더 줄을 갖는다. 디스커버리로 받은
  `media_list`와 대소문자 무관 일치하는 블록만 쓰고, 나머지(브랜드가 쓰지 않는 매체)는
  버린다. **1회 호출로 충분** — 매체마다 반복 호출하지 않는다.
- **`media` 명시(선택)**: `"naver"|"google"|"meta"|"tiktok"` 중 하나를 넘기면 해당 매체
  블록 하나만 온다(단일 매체 동작은 이전과 동일, 변경 없음).
- 각 블록은 여전히 markdown 표다 — 행(cost/revenue/roas) × 열(target|actual|
  progress_ratio). 해당 매체 예산이 전혀 없으면 리터럴
  `"No {media} budget/target available for {month}."` 한 줄이 반환된다 — **오류가 아니다**.
- ⚠️ ROAS류 수치는 비율값(예: 0.87, 5.06)이므로 반드시 ×100 후 표시한다 (0.87 → 87%).
- `revenue` 행의 `actual`은 매출 실적으로 쓰지 않는다 — 실적 매출은 항상
  `get_ad_performance`의 revenue 역할 키에서 가져온다 (naver actual 0 반환 사례 실측).

## 4. `get_brand_list` — 브랜드 목록 (불변)

## 5. `list_promotions` — 프로모션 목록 (불변)

```json
{ "brand_name": "<brand>", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }
```

- 응답 `items[]`의 `{title, date_begin, date_end}`를 각 스킬 빌더에 가공 없이 넘긴다.

## 공통 규칙

- 모든 호출의 `brand_name`은 사용자가 말한 브랜드명을 **그대로** 넣는다 — 스킬 파일에 브랜드
  문자열을 두지 않는다. 서버가 `Unknown brand`로 거절할 때만 `get_brand_list`로 정확한 이름을
  확인한다.
- Executive Summary류 분석 텍스트는 `df_dify` MCP를 호출하지 않고, 이미 수집한 수치 데이터를
  근거로 실행 LLM이 직접 작성한다 (근거 수치가 없으면 생성하지 않음).
- 고카디널리티 응답(campaign/ad 차원)은 이 플러그인의 PostToolUse 캡처 훅
  (`hooks/capture_ad_performance.py`)이 파일로 우회시킨다 — 스텁에 적힌 경로를 asset
  스크립트의 `json_files` 입력으로 그대로 넘긴다(원본 재타이핑 금지).
