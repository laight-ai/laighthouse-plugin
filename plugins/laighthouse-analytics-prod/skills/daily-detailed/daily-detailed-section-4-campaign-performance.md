# Breezm Daily Section 4: 캠페인 성과 (D-1 vs D-0)

**report_type:** `daily-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 캠페인 단위로
**전날(D-1)과 기준일(D-0) 딱 이틀만** 비교한다.

> ℹ️ 표 HTML/검색/페이지네이션/색상·화살표 렌더링은 전부 템플릿+빌더가, 조인·파생지표·변화율·
> 필터·정렬·`<tr>` 생성은 `assets/dxd_table_rows.py`가 한다 — 모델의 역할은 아래 MCP 1회 호출과
> 스크립트 실행뿐이다.

## MCP 도구 호출: `get_ad_performance` × 1 (D-1~D0 이틀, `media` 생략)

```json
{ "brand_name": "breezm", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "time_grain": "day", "group_by": ["media", "campaign_id", "campaign_name"] }
```

- `start_date`는 항상 target_date의 하루 전날. **`media`는 생략**(넣지 않음) — 캠페인 단위는
  카디널리티가 낮아 1회 통합 호출이 안전하다(행의 `media` 차원 값으로 스크립트가 자동 분리).
  ⚠️ 캠페인 수가 매체당 두세 자릿수를 넘는 브랜드가 생기면 응답 크기를 재보고 매체별 호출로
  재분리한다.
- 응답은 JSON 봉투(`rows` 배열) — 각 행에 `date`/`media`/`campaign_id`/`campaign_name` 차원과
  `광고비`/`노출`/`클릭`/`매출_AB`/`예약완료_AB` 등 지표가 함께 들어있다(별도 매출 조인 없음).

## 계산·행 생성: `assets/dxd_table_rows.py` (필수 절차 — 손계산·새 스크립트 금지)

응답이 `[laighthouse-capture-hook] ... 저장됨: <경로>` 스텁으로 오면(캡처 훅 동작 호스트)
그 경로를 `json_files`로, 원본 JSON 봉투가 그대로 오면 `json`에 원본 문자열 통째로
(손 전사·행 선별 절대 금지 — ₩10,000 초과 행이 조용히 누락될 위험). 출력은 빌더가 읽을
파일로 저장한다:

```bash
python3 assets/dxd_table_rows.py <<'PYEOF' > /tmp/s4_rows.json
{"level":"campaign","d1_date":"2026-08-09","d0_date":"2026-08-10","json_files":["<스텁에 적힌 경로>"]}
PYEOF
```

스크립트가 D-1/D-0 비교(media+campaign 키 정확 일치), 6개 지표(광고비/CTR/예약 완료/예약 완료
CPA/매출/ROAS — 매출·예약은 각 행의 `매출_AB`/`예약완료_AB`)와 변화율·화살표·색상, D-0 광고비
₩10,000 이하 필터, D-0 광고비 내림차순 정렬, `<tr>` HTML 생성까지 전부 처리한다. 지표 키는
브리즘 기본값이 내장돼 있고 응답 `metrics`와 대조·검증된다(다른 테넌트면 `metric_keys`로
넘긴다). 출력 파일 경로를 빌더 입력 JSON의 `s4.rows_file`에 넣으면 끝.

> 🚫 **응답이 크다고 느껴져도 선택지는 둘뿐이다**: (1) 원본을 가공 없이 전부 스크립트에 넘기거나
> (2) 정말 불가능하면 `s4`를 빌더 입력에서 빼서 "데이터 준비 중"으로 표시한다. 다른 섹션 값
> 재사용·근사치·추정 수치 대체는 그 숫자가 진짜 쿼리 결과라도 **전부 금지**다 — 실제로 이
> 규칙 위반(출처 불명 수치 삽입, 타 섹션 값 바꿔치기) 사고가 두 차례 있었다. 이미 정상적으로
> 받은 응답은 그 세분화 단위 그대로 쓴다.
