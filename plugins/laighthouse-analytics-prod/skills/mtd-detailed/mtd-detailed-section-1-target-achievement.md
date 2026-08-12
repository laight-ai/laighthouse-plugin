# Breezm MTD Section 1: 목표 달성 현황 (Target Achievement)

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 당월 MTD 목표
대비 진행 상황. 모든 "매출"은 Airbridge 매출(`airbridge_revenue`), 광고 채널은 airbridge 응답
`channel` ∈ {`Google Ads`, `Meta Ads`, `Naver Ads`} 행이다.

> ℹ️ 이 섹션의 HTML/렌더링은 전부 `assets/report-template.html` + `assets/build_report.py`가
> 처리한다 — 모델은 아래 규칙으로 **값만 계산**해서 빌더 입력 JSON의 `s1`에 넣는다.

---

## MCP 도구 호출: `get_target_progress_v2` × 3 (media만 바꿔 반복)

```json
{ "brand_name": "breezm", "month": "YYYY-MM", "media": "google", "as_of_date": "target_date" }
{ "brand_name": "breezm", "month": "YYYY-MM", "media": "meta", "as_of_date": "target_date" }
{ "brand_name": "breezm", "month": "YYYY-MM", "media": "naver", "as_of_date": "target_date" }
```

> ℹ️ 응답은 markdown이다 — 헤더 라인 뒤에 행(cost/revenue/roas) × 열(target|actual|
> progress_ratio) 표. 해당 매체 예산이 전혀 없으면 `"No {media} budget/target available for
> {month}."` 한 줄이 반환된다 — 오류가 아니다. **표를 반환하더라도 `cost`/`revenue` 목표는
> 서로 독립적으로 있을 수도 없을 수도 있다** (브리즘은 현재 세 매체 모두 cost 목표는 있고
> revenue 목표는 `target: 0`으로 빈 상태가 기본).
> ⚠️ ROAS 관련 수치는 비율값(0.87)로 오므로 ×100 해서 %로 만든다.

이 세 응답은 섹션 6(광고 매체별 현황, `s6`)이 그대로 재사용한다 — 별도 재호출 없음.

## MCP 도구 호출: `get_ad_performance_monthly_table` × 1 (매출 실적 + fallback 소진액)

```json
{ "brand_name": "breezm", "start_month": "당월 YYYY-MM", "end_month": "당월 YYYY-MM", "group_by": "media", "day_offset": "target_date.day" }
```

- **`media` 파라미터 생략** — 이 1회 호출이 (a) 매출 실적(airbridge 행 중 광고 채널 3종의
  `airbridge_revenue` 합)과 (b) no-budget fallback 소진액(google/meta/naver 행의 `cost`)을
  동시에 준다. `ga4` 등 그 외 매체 행은 무시. 섹션 6도 이 응답을 재사용한다.
- **위 `get_target_progress_v2` 3회와 같은 배치(한 메시지)에서 동시에 발사한다** — 목표 판정을
  기다리는 조건부 2차 라운드를 만들지 않는다.
- **절대 규칙**: `기간_매출`은 목표 유무와 무관하게 **항상** 이 호출의 airbridge 행에서
  가져온다 — `get_target_progress_v2`의 `revenue` 행 `actual`은 어떤 매체에서도 매출 실적으로
  쓰지 않는다 (naver에서 0을 반환하는 사례 실측됨).
- ⚠️ `campaign-type` 금지 — airbridge 행이 조용히 누락된다.

## 계산 규칙 (매체별로 cost/revenue를 독립 판단)

- **no-budget 메시지** 매체 → 목표 예산 없음, 소진액은 monthly_table 응답의 해당 매체 `cost`.
- **표 반환** 매체 → `cost` 행 `target > 0`이면 목표 예산 = target, 소진액 = actual.
  target이 0/없으면 no-budget과 동일 처리.
- `revenue` 행은 cost와 별개로: `target > 0`이면 목표 매출 = target, 0이면(기본 상태) 그 매체는
  목표 매출 합산·매출 달성률·목표 ROAS에서 제외. (`revenue` actual은 어떤 경우에도 안 씀.)

집계(세 매체 합산) → **빌더 `s1` 필드** (숫자 원본 그대로, 계산 불가면 `null` — ₩콤마·%·N/A
포맷은 빌더가 한다):

| 빌더 필드 | 값 |
|---|---|
| `목표_예산` | 유효한 매체들의 cost target 합 (하나도 없으면 null) |
| `소진액` | 세 매체 소진액(정상 또는 fallback) 전부 합 |
| `소진율` | 소진액 ÷ 목표_예산 × 100 (목표_예산 null이면 null) |
| `목표_매출` | 유효한 매체들의 revenue target 합 (없으면 null — 현재 기본 상태) |
| `기간_매출` | airbridge 광고 채널 3종 매출 합 (항상 이 값) |
| `매출_달성률` | 기간_매출 ÷ 목표_매출 × 100 (목표_매출 null이면 null) |
| `목표_ROAS` | 목표_매출 ÷ 목표_예산 × 100 (둘 중 하나 null이면 null) |
| `실제_ROAS` | 기간_매출 ÷ 소진액 × 100 (소진액 0이면 null) |
| `footnote` | 목표(예산 또는 매출) 없는 매체가 하나라도 있으면 `true` (고정 각주는 빌더가 넣는다) |

- no-budget 메시지는 오류가 아니다 — "데이터 준비 중"으로 빼지 말고 위 N/A(null) 규칙대로 넣는다.
- airbridge 응답의 실제 `channel` 값이 상수(`Google Ads`/`Meta Ads`/`Naver Ads`)와 다르면
  조용히 0을 만들지 말고, Executive Summary(`s2`)에 `⚠`로 시작하는 불일치 안내 줄을 추가한다.
