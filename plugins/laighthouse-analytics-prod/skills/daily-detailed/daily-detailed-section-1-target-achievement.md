# Daily Section 1: 목표 달성 현황 (Target Achievement)

**report_type:** `daily-detailed` (항상 포함). 데일리 보고서에서도 이 카드는 **당월 MTD 목표
대비 진행 상황**을 그대로 보여준다 (예산이 월 단위로 설정되므로 매일 확인할 가치가 있다).
모든 "매출"은 `get_ad_performance` 응답 행의 revenue 역할 키(`metric_keys.revenue`) 값이다.

> ℹ️ 이 섹션의 HTML/렌더링은 전부 `assets/report-template.html` + `assets/build_report.py`가
> 처리한다 — 모델은 아래 규칙으로 **값만 계산**해서 빌더 입력 JSON의 `s1`에 넣는다.

---

## MCP 도구 호출: `get_target_progress_v2` × 1 (media 생략, 4개 매체 전부 응답)

```json
{ "brand_name": "<brand>", "month": "YYYY-MM", "as_of_date": "target_date" }
```

- `media`를 생략하면 응답은 naver, google, meta, tiktok 순서로 **고정된 4개 블록**이 빈
  줄로 이어붙어 온다 — `media_list`와 무관하게 항상 이 순서로 4개가 온다.
- 각 블록은 (a) `month:`/`as_of_date:`/`media:` 헤더 3줄 + 빈 줄 + 표, 또는 (b) 헤더 없이
  `"No {media} budget/target available for {month}."` 한 줄 중 하나다 — 표 없는 블록은
  `media:` 헤더가 없으므로 헤더 줄로 찾지 말고, **고정 순서대로 정확히 4개 세그먼트로
  나눠** 1번째=naver, 2번째=google, 3번째=meta, 4번째=tiktok로 배정한다.
- 그 중 `media_list`(디스커버리 결과)에 있는 매체에 해당하는 세그먼트만 쓰고, 나머지는
  버린다. 매체명을 리터럴로 열거하지 않는다. Organic(`media: null`)은 목표 개념이 없어
  이 블록들과 무관하다.

> ℹ️ 블록마다 헤더 라인 뒤에 행(cost/revenue/roas) × 열(target|actual|
> progress_ratio) 표. 해당 매체 예산이 전혀 없으면 `"No {media} budget/target available for
> {month}."` 한 줄이 반환된다 — 오류가 아니다. **표를 반환하더라도 `cost`/`revenue` 목표는
> 서로 독립적으로 있을 수도 없을 수도 있다** (revenue 목표가 `target: 0`으로 비어 있는
> 브랜드가 흔하다).
> ⚠️ ROAS 관련 수치는 비율값(0.87)로 오므로 ×100 해서 %로 만든다.

## MCP 도구 호출: `get_ad_performance` × 1 (매출 실적 + fallback 소진액)

```json
{ "brand_name": "<brand>", "start_date": "당월 YYYY-MM-01", "end_date": "target_date", "time_grain": "month", "group_by": ["media"] }
```

- **`filters` 생략** — 이 1회 호출이 매체당 한 행(`month` 키 포함)으로 (a) 매출 실적
  (각 행의 revenue 키 합)과 (b) no-budget fallback 소진액(각 행의 cost 키)을 동시에 준다.
  응답은 JSON 봉투(`rows` 배열)이며, `media` 차원 값은 디스커버리와 같은 문자열이다
  (`has_organic`이면 `media: null` 행도 함께 온다).
- **위 `get_target_progress_v2` 호출과 같은 배치(한 메시지)에서 동시에 발사한다** — 목표
  판정을 기다리는 조건부 라운드를 만들지 않는다.
- **절대 규칙**: `기간 매출`은 목표 유무와 무관하게 **항상** 이 호출의 revenue 키에서 가져온다 —
  `get_target_progress_v2`의 `revenue` 행 `actual`은 어떤 매체에서도 매출 실적으로 쓰지
  않는다 (naver에서 0을 반환하는 사례 실측됨).

## 계산 규칙 (매체별로 cost/revenue를 독립 판단)

- **no-budget 메시지 / 미지원 매체 / 호출 에러** 매체 → 목표 예산 없음, 소진액은
  `get_ad_performance` 응답의 해당 매체 행 cost 키.
- **표 반환** 매체 → `cost` 행 `target > 0`이면 목표 예산 = target, 소진액 = actual.
  target이 0/없으면 no-budget과 동일 처리.
- `revenue` 행은 cost와 별개로: `target > 0`이면 목표 매출 = target, 0이면(기본 상태) 그 매체는
  목표 매출 합산·매출 달성률·목표 ROAS에서 제외. (`revenue` actual은 어떤 경우에도 안 씀.)
- no-budget 메시지는 오류가 아니다 — "데이터 준비 중"으로 처리하지 않고 N/A 규칙대로 계산한다.

집계(`media_list` 전 매체 합산, Organic 제외) → **빌더 `s1` 필드** (숫자 원본 그대로, 계산
불가면 `null` — 통화 콤마·%·N/A 포맷은 빌더가 한다):

| 빌더 필드 | 값 |
|---|---|
| `목표_예산` | 유효한 매체들의 cost target 합 (하나도 없으면 null) |
| `소진액` | 전 매체 소진액(정상 또는 fallback) 전부 합 |
| `소진율` | 소진액 ÷ 목표_예산 × 100 (목표_예산 null이면 null) |
| `목표_매출` | 유효한 매체들의 revenue target 합 (없으면 null) |
| `기간_매출` | 전 매체 행의 revenue 키 합 (항상 이 값) |
| `매출_달성률` | 기간_매출 ÷ 목표_매출 × 100 (목표_매출 null이면 null) |
| `목표_ROAS` | 목표_매출 ÷ 목표_예산 × 100 (둘 중 하나 null이면 null) |
| `실제_ROAS` | 기간_매출 ÷ 소진액 × 100 (소진액 0이면 null) |
| `footnote` | 목표(예산 또는 매출) 없는 매체가 하나라도 있으면 `true` (고정 각주는 빌더가 넣는다) |

- 응답 rows의 `media` 값이 디스커버리 `media_list`와 다르면 조용히 0을 만들지 말고,
  Executive Summary(`s2`)에 `⚠`로 시작하는 불일치 안내 줄을 추가한다.
