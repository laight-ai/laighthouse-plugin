# MTD Section 7: 캠페인 성과 (Campaign Performance)

**report_type:** `mtd-detailed` (항상 포함). 매체-캠페인 단위, MTD(월초~target_date).

> ℹ️ 표 HTML/검색/페이지네이션 렌더링은 템플릿이, **`<thead>` 라벨(`metric_keys` 값)·파생지표
> (CTR/CPA/ROAS)·광고비 내림차순 정렬·`<tr>` 생성·포맷팅은 전부 `assets/build_report.py`가
> 한다** — 모델의 역할은 아래 MCP 1회 호출과 응답을 빌더 입력 `s7`에 담는 것뿐이다.

## MCP 도구 호출: `get_ad_performance` × 1 (`time_grain:"total"`, 캠페인 단위, `filters` 생략)

```json
{ "brand_name": "<brand>", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "time_grain": "total", "group_by": ["media", "campaign_id", "campaign_name"] }
```

- **`filters`는 생략한다** — 1회 통합 호출로 전 매체를 받는다(행의 `media` 차원 값이 그대로
  매체 라벨이 되고, `media`가 `null`인 행은 빌더가 "Organic"으로 표기한다 — 행을 버리지 않는다).
- ✅ `time_grain:"total"`은 기간 전체를 **캠페인당 이미 합산한 행 1개**로 반환한다(일별 행
  아님) — 날짜별 재합산(Bash 집계)이 필요 없다. 각 행에 cost/impression/click/revenue(/
  conversion) 키가 함께 들어있어 매출 조인도 없다.

## 빌더 `s7` 입력 (파생·정렬·포맷은 빌더가 처리)

**권장 — 응답 원본 JSON 봉투를 그대로 넘긴다** (`json` 배열에 가공 없이; 캡처 훅 파일로 온
응답은 `json_files`에 경로 — 혼용 가능). 빌더가 봉투 파싱·행 변환까지 전부 처리한다. 지표
키는 최상위 `metric_keys`(디스커버리에서 정한 역할 맵)를 우선 쓰고, 없으면 응답 `metrics`에서
`generic-report-pattern.md` 3절의 후보 순서로 자동 해석한다. `conversion` 역할이 없으면 전환·
CPA 컬럼이 표에서 빠진다:

```json
"metric_keys": {"cost": "광고비", "impression": "노출", "click": "클릭", "revenue": "매출_AB", "conversion": "예약완료_AB"},
"currency": "₩",
"s7": { "json": ["<get_ad_performance 응답 원본>"] }
```

또는 직접 전사한 행 객체 (전 행 — 선별·요약·상위 N개 발췌 절대 금지):

```json
"s7": {
  "rows": [ {"name": "Kakao", "campaign": "...", "impression": 10000, "click": 500, "cost": 54832, "revenue": 1200000, "conversion": 3}, ... ]
}
```

빌더가 적용하는 규칙(참고용 — 재구현·손계산 금지):
- `CTR` = 클릭÷노출×100(노출 0이면 N/A), `{conversion} CPA` = 광고비÷전환(0이면 N/A),
  `ROAS` = 매출÷광고비×100(광고비 0이면 N/A). 광고비 내림차순 정렬, 검색·페이지네이션용
  `{search, html}` 행 생성. `<th>` 텍스트는 `metric_keys`의 impression/click/cost/revenue/
  conversion 값(CTR/ROAS는 고정).

> 🚫 **응답이 크다고 느껴져도 선택지는 둘뿐이다**: (1) 원본을 가공 없이 전부 빌더에 넘기거나
> (2) 정말 불가능하면 `s7`을 빌더 입력에서 빼서 "데이터 준비 중"으로 표시한다. 다른 섹션 값
> 재사용·근사치·추정 수치 대체는 그 숫자가 진짜 쿼리 결과라도 **전부 금지**다. 이미 정상적으로
> 받은 응답은 그 세분화 단위 그대로 쓴다 — "받았지만 크다"며 바꾸는 경우는 존재하지 않는다.
