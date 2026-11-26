# MCP 도구 라우팅 규칙 (laighthouse 서버 — 전 스킬 공용)

`laighthouse` MCP 서버 도구 중 이 플러그인 스킬이 쓰는 것의 규칙이다. 외부 요인 스킬은 `get_external_context`(규칙은 각 스킬
SKILL.md와 `shared/assets/external_context/`)와, 날씨 스킬만 `get_ad_performance`를 함께 쓴다. 브랜드 이름이 거절되면 `get_brand_list`를 쓴다.
예외로 `nextmonth-budget-planning` 스킬은 미디어믹스 도구 셋(`list_media_mix_metrics`·`create_media_mix_job`·`list_media_mix_jobs`·`get_media_mix_job`. `list_media_mix_jobs` 는 조직에 따라 도구 목록에 없을 수 있다)을 쓴다 —
규칙은 그 스킬의 SKILL.md에 있다. `media-mix-backtest-check` 스킬도 같은 도구 셋(`create_media_mix_job` 은 `backtest: true`)과 `get_ad_performance` 를 쓴다.

## 1. `get_ad_performance` — 광고 성과 (유일한 성과 조회 도구)

예전의 daily/range/monthly 3종 표 도구를 하나로 통합한 도구다. 시그니처:

```json
{
  "brand_name": "<brand>",
  "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD",
  "time_grain": "day" | "month" | "total",        // 기본 "day"
  "group_by": ["media", "campaign_id", "campaign_name"],  // 차원명 리스트, 생략 시 총계
  "metrics": ["<광고비 키>", "<매출 키>"],           // 생략(null) 시 전체 지표, [] 이면 차원만
  "filters": {"media": ["<디스커버리로 받은 값>"]},   // 차원 → 허용값 리스트, 정확 일치. 생략 시 전체
  "day_offset": 15                                  // month grain 전용 — 각 월을 N일까지 자름
}
```

- 예전의 `media: str` 파라미터는 **제거됐다** — 매체 필터는 `filters={"media": [...]}`로 한다.
  값은 디스커버리 응답에 나온 문자열 그대로(정확 일치)만 쓴다.
- `metrics`: 생략(null) → 테넌트의 공개 지표 전부 / `[]` → 지표 없이 차원만(⚠️ 이때 봉투
  `metrics` 목록도 빈 배열로 온다 — 지표 키 디스커버리에는 쓸 수 없다) /
  리스트 → 그 지표만. 알 수 없는 지표명·차원명을 넣으면 서버가 유효한 이름 목록을 담은
  ValueError를 돌려준다 — 그 목록으로 바로잡는다(추측 재시도 금지).
- **검증 규칙(서버가 ValueError로 거절)**: `metrics:[]`는 `time_grain:"day"`가 아니면 비어 있지
  않은 `group_by`가 필요하다. `filters`는 알 수 없는 차원 키, `"date"` 키, 빈 값 리스트(`[]`)를
  거절한다. 서버 에러 메시지는 **그대로** 사용자에게 전달한다(재해석·추측 재시도 금지).
- **ELT 테넌트가 없는 브랜드**: 레거시 DB 폴백은 제거됐다. 서버가
  `Brand '<name>' is not ELT-published yet; ... requires the brand's data mart` ValueError를 돌려주며,
  이 문서의 모든 패턴은 **ELT 테넌트가 있는 브랜드에서만** 동작한다. 서버 에러를 그대로 전달한다.
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
  "dimensions": ["media"], "metrics": ["광고비", "..."], "metric_units": {"광고비": "₩", "...": null},
  "row_count": 42,
  "rows": [ { "date": "2026-08-01", "media": "Google", "광고비": 12345, "매출": 67890, "...": 0 } ] }
```

  - 행의 **차원 키는 영문**: `date`(day grain) / `month`(month grain, "YYYY-MM") / `media` /
    `source` / `campaign_id`/`campaign_name` / `ad_group_id`/`ad_group_name` /
    `ad_id`/`ad_name` / `ad_type`.
  - 행의 **지표 키는 테넌트별**이다 — 브랜드마다 이름이 다르다(한국어/영문/접미사 등).
    **응답의 `metrics` 목록이 유효한 지표 키의 유일한 진실이다** — 키를 추측하지 않는다.
    역할(광고비·노출·클릭·매출·전환)에 어떤 키를 쓸지는 응답 `metrics` 목록에서 이름으로 고른다(대소문자 무시, 동의어 포함).
  - **`metric_units`는 지표별 단위 기호 맵**이다 — 브랜드 카탈로그가 공개한 값 그대로(`"₩"`,
    `"%"`, `"회"` …), 공개된 단위가 없으면 `null`. 수치를 표시할 때 이 값을 **그대로** 붙이고,
    지표명(`광고비`, `roas` …)으로 단위를 추측하지 않는다. `null`이면 단위 없이 표시한다.
    `metrics: []` 호출에서는 `{}`로 온다.
  - ⚠️ 비율 지표는 **요청한 grain 기준으로 서버가 이미 계산한 % 값**이다(예: ROAS 122.4 =
    122.4%) — ×100 하지 않고, **행별 비율 값을 합산/평균해 상위 기간·상위 그룹 비율을 만들지
    않는다**(필요하면 원자 지표 합으로 다시 계산).
  - **매체 디스커버리**: `media`는 지표가 아니라 차원이며, 브랜드마다 값 집합이 다르다. 고정
    매체 목록을 어디에도 가정하지 않고, 매 실행 시작에
    `time_grain:"total", group_by:["media"]`(`metrics` 생략) 1회 호출로 실제 값과 지표 키를
    함께 받는다. **`media`가 `null`인 행이 Organic**(광고비 없이 매출만
    귀속)이다 — 정상 행이며 cost/impression/click은 항상 비어 있으므로 채우지 않는다.
    브랜드에 `media` 차원이 없어 호출이 실패하면 `group_by:["source"]`로 폴백해 `source`
    값을 매체 목록으로 쓴다. 표시명은 응답 값 그대로(접미사·번역 없음).

## 2. `get_brand_list` — 브랜드 목록 (불변)

- 서버가 `Unknown brand`로 거절할 때만 쓴다(아래 공통 규칙).

## 공통 규칙

- 모든 호출의 `brand_name`은 사용자가 말한 브랜드명(비슷한 이름을 확인받았으면 그 이름)을 **그대로** 넣는다 — 스킬 파일에 브랜드
  문자열을 두지 않는다.
- 서버가 `Unknown brand`로 거절하면(이름이 다르거나 그 브랜드를 읽을 권한이 없으면) `get_brand_list`를 1회 불러
  아래 기준에 맞는 이름을 후보로 고른다(1. 공백·대소문자·`(주)`·`주식회사`만 다른 이름, 2. 한쪽이 다른 쪽을 포함하는 이름, 3. 글자 1~2개만 다른 이름 순). **묻지 않고 바꿔 부르지 않는다** —
  AskUserQuestion으로 "'<사용자가 말한 이름>'은(는) '<후보>'를 말씀하신 건가요?"를 묻는다. 선택지는 후보 1~3개(가장 비슷한 것 먼저)와
  "아니요"이다. 후보를 고르면 그 이름을 이후 모든 호출의 `brand_name`, 스크립트의 `--brand`, 제목·파일명에 쓰고 거절된 라운드(동시에 보낸 호출 전체)를 새 이름으로 다시 보낸다.
  "아니요"를 고르거나 비슷한 이름이 없으면 볼 수 있는 브랜드 목록을 보여 주고 멈춘다.
  후보는 이름 기준으로 중복을 없앤다. 목록이 비어 있으면 브랜드 접근 권한과 MCP 사용 설정을 관리자에게 확인하게 한다. AskUserQuestion이 없는 호스트에서는 같은 질문과
  선택지를 채팅으로 내고 답을 기다린다.
- 서버가 `Several brands are named`로 거절하면 읽을 수 있는 브랜드 중 이름이 **완전히 같은** 것이 여럿이라는 뜻이다 —
  어느 이름을 골라도 같은 오류가 나므로 묻지 않는다. 서버 메시지를 그대로 전하고, 관리자에게 브랜드 이름을 구분해 달라고
  요청하게 한 뒤 멈춘다.
- 고카디널리티 응답(campaign/ad 차원)은 이 플러그인의 PostToolUse 캡처 훅
  (`hooks/capture_ad_performance.py`)이 파일로 우회시킨다 — 스텁에 적힌 경로의 파일을 읽어 쓴다(원본 재타이핑 금지).
