# Breezm MTD Section 7: 캠페인 성과 (Campaign Performance)

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 매체-캠페인 단위,
MTD(월초~target_date).

> ℹ️ 표 HTML/검색/페이지네이션 렌더링은 템플릿이, **조인(캠페인명 정확 일치)·파생지표(CTR/CPA/
> ROAS)·광고비 내림차순 정렬·`<tr>` 생성·포맷팅은 전부 `assets/build_report.py`가 한다** —
> 모델의 역할은 아래 MCP 4회 호출과 응답 행을 빌더 입력 `s7`에 담는 것뿐이다.

## MCP 도구 호출: `get_ad_performance_range_table` × 4 (google/meta/naver/airbridge, 각각 `group_by: "campaign"`)

```json
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "google", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "meta", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "naver", "group_by": "campaign" }
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "media": "airbridge", "group_by": "campaign" }
```

- **매체별로 4번 나눠 부른다 — `media`를 생략하지 않는다.** 실측(2026-08-11)으로, `media` 생략
  시 이 스킬이 쓰지 않는 `ga4` 캠페인 행 58개가 유효 행(41개)보다 많이 섞여 오는 것이
  확인됐다 — 매체별 명시적 호출이 낫다.
- ✅ `get_ad_performance_range_table`은 기간 전체를 **캠페인당 이미 합산한 행 1개**로 반환한다
  (일별 행 아님) — 날짜별 재합산(Bash 집계)이 필요 없고, MTD 구간(≤31일)은 span 한도(92일)
  안에 항상 든다. `is_active`는 항상 비어있다(안 씀).
- 네 호출은 의존성이 없으므로 한 메시지에서 병렬 발사.
- ⚠️ `campaign-type` 금지 — airbridge 행이 조용히 누락된다. `group_by`는 문자열 `"campaign"`.

## 빌더 `s7` 입력 (조인·파생·정렬·포맷은 빌더가 처리)

**권장 — 응답 원본 마크다운을 그대로 넘긴다** (4개 응답 전부를 `markdown` 배열에 가공 없이;
파일로 온 응답은 `markdown_files`에 경로 — 혼용 가능). 빌더가 파싱, `media` 필드 분리(ga4 등
자동 제외), airbridge 캠페인별 합산, 조인까지 전부 처리한다:

```json
"s7": { "markdown": ["<google 응답 원본>", "<meta 응답 원본>", "<naver 응답 원본>", "<airbridge 응답 원본>"] }
```

또는 직접 전사한 행 객체 (전 행 — 선별·요약·상위 N개 발췌 절대 금지):

```json
"s7": {
  "media_rows": [ {"channel": "Google Ads", "campaign": "...", "impression": 10000, "click": 500, "cost": 54832}, ... ],
  "airbridge_rows": [ {"campaign": "...", "revenue": 1200000, "reservation": 3}, ... ]
}
```

빌더가 적용하는 규칙(참고용 — 재구현·손계산 금지):
- 조인은 캠페인 이름 **정확 일치**만. 매체 쪽에만 있는 캠페인 → 매출/예약/CPA/ROAS `-`,
  airbridge 쪽에만 있는 캠페인 → 표에서 제외(각주는 고정 문구로 갈음).
- `CTR` = 클릭÷노출×100(노출 0이면 N/A), `예약 완료 CPA` = 광고비÷예약 완료(0이면 N/A),
  `ROAS` = 매출÷광고비×100(광고비 0이면 N/A). 광고비 내림차순 정렬, 검색·페이지네이션용
  `{search, html}` 행 생성.

> 🚫 **응답이 크다고 느껴져도 선택지는 둘뿐이다**: (1) 원본을 가공 없이 전부 빌더에 넘기거나
> (2) 정말 불가능하면 `s7`을 빌더 입력에서 빼서 "데이터 준비 중"으로 표시한다. 다른 섹션 값
> 재사용·근사치·추정 수치 대체는 그 숫자가 진짜 쿼리 결과라도 **전부 금지**다. 이미 정상적으로
> 받은 응답은 그 세분화 단위 그대로 쓴다 — "받았지만 크다"며 바꾸는 경우는 존재하지 않는다.
