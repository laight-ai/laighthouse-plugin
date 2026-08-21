# Breezm MTD Section 7: 캠페인 성과 (Campaign Performance)

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 매체-캠페인 단위,
MTD(월초~target_date).

> ℹ️ 표 HTML/검색/페이지네이션 렌더링은 템플릿이, **파생지표(CTR/CPA/ROAS)·광고비 내림차순
> 정렬·`<tr>` 생성·포맷팅은 전부 `assets/build_report.py`가 한다** —
> 모델의 역할은 아래 MCP 1회 호출과 응답을 빌더 입력 `s7`에 담는 것뿐이다.

## MCP 도구 호출: `get_ad_performance` × 1 (`time_grain:"total"`, 캠페인 단위, `media` 생략)

```json
{ "brand_name": "breezm", "start_date": "월초 YYYY-MM-01", "end_date": "target_date", "time_grain": "total", "group_by": ["media", "campaign_id", "campaign_name"] }
```

- **`media`는 생략한다** — ELT 응답에는 예전 같은 ga4/airbridge 잉여 행이 없어 1회 통합
  호출이 안전하다(행의 `media` 차원 값으로 빌더가 분리한다).
- ✅ `time_grain:"total"`은 기간 전체를 **캠페인당 이미 합산한 행 1개**로 반환한다(일별 행
  아님) — 날짜별 재합산(Bash 집계)이 필요 없다. 각 행에 `광고비`/`노출`/`클릭`/`매출_AB`/
  `예약완료_AB`가 함께 들어있어 매출 조인도 없다.

## 빌더 `s7` 입력 (파생·정렬·포맷은 빌더가 처리)

**권장 — 응답 원본 JSON 봉투를 그대로 넘긴다** (`json` 배열에 가공 없이; 캡처 훅 파일로 온
응답은 `json_files`에 경로 — 혼용 가능). 빌더가 봉투 파싱, `media` 분리, 행 변환까지 전부
처리한다(지표 키는 브리즘 기본값 내장, 다른 테넌트면 `s7.metric_keys` 지정):

```json
"s7": { "json": ["<get_ad_performance 응답 원본>"] }
```

또는 직접 전사한 행 객체 (전 행 — 선별·요약·상위 N개 발췌 절대 금지):

```json
"s7": {
  "media_rows": [ {"channel": "Google Ads", "campaign": "...", "impression": 10000, "click": 500, "cost": 54832}, ... ],
  "airbridge_rows": [ {"campaign": "...", "revenue": 1200000, "reservation": 3}, ... ]
}
```

빌더가 적용하는 규칙(참고용 — 재구현·손계산 금지):
- `CTR` = 클릭÷노출×100(노출 0이면 N/A), `예약 완료 CPA` = 광고비÷예약 완료(0이면 N/A),
  `ROAS` = 매출÷광고비×100(광고비 0이면 N/A). 광고비 내림차순 정렬, 검색·페이지네이션용
  `{search, html}` 행 생성. (매출/예약이 행에 함께 있어 예전 같은 airbridge 조인은 없다.)

> 🚫 **응답이 크다고 느껴져도 선택지는 둘뿐이다**: (1) 원본을 가공 없이 전부 빌더에 넘기거나
> (2) 정말 불가능하면 `s7`을 빌더 입력에서 빼서 "데이터 준비 중"으로 표시한다. 다른 섹션 값
> 재사용·근사치·추정 수치 대체는 그 숫자가 진짜 쿼리 결과라도 **전부 금지**다. 이미 정상적으로
> 받은 응답은 그 세분화 단위 그대로 쓴다 — "받았지만 크다"며 바꾸는 경우는 존재하지 않는다.
