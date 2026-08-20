# Breezm MTD Section 6: 광고 매체별 현황 (Channel Budget)

**report_type:** `mtd-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). 매체별 목표 대비
소진/달성 현황.

> ℹ️ 표 HTML/헤더 정렬/₩·%·N/A 포맷은 전부 템플릿+빌더가 한다 — 모델은 아래 규칙으로 매체별
> 원본 수치만 계산해 빌더 입력 JSON의 `s6.rows`에 넣는다. **신규 MCP 호출 없음** — 섹션 1의
> `get_target_progress_v2` ×3 응답과 `get_ad_performance`(month grain, `media` 생략) 응답을
> 그대로 재사용한다.

## 매체별 계산 규칙 (cost/revenue 독립 판단)

- **절대 규칙**: `광고_매출`은 목표 유무와 무관하게 **항상** 섹션 1이 받은 `get_ad_performance`
  (`media` 생략) 응답의 해당 매체 행(`media` = `Google`/`Meta`/`Naver`) `매출_AB`를 쓴다 —
  `get_target_progress_v2`의 `revenue` 행 `actual`은 **절대 쓰지 않는다** (naver가 0을
  반환하는데 Airbridge 귀속 매출은 존재하는 사례 실측됨).
- no-budget 메시지 매체 → `월_예산`/`예산_소진율` null, `소진액`은 같은 공유 응답의 해당 매체
  행 `광고비`로 대체 (추가 호출 없음).
- 표 반환 매체 → `cost` 행: `월_예산` = target, `소진액` = actual, `예산_소진율` =
  progress_ratio × 100. (target 0이면 no-budget과 동일 처리.)
- `revenue`/`roas` 행은 target만 쓴다: target > 0이면 `목표_매출` = revenue target,
  `목표_ROAS` = roas target × 100. target 0이면(현재 세 매체 전부) 둘 다 null.
- `매출_달성률` = 광고_매출 ÷ 목표_매출 × 100 (목표_매출 null이면 null),
  `ROAS` = 광고_매출 ÷ 소진액 × 100 (소진액 0이면 null).

## 빌더 `s6.rows` (세 매체 행 전부 — no-budget 매체도 행을 빼지 않는다)

```json
{ "rows": [
  { "channel": "Google Ads", "월_예산": 50000000, "소진액": 21000000, "예산_소진율": 42.0,
    "목표_매출": null, "광고_매출": 34000000, "매출_달성률": null, "목표_ROAS": null, "ROAS": 161.9 },
  { "channel": "Meta Ads", ... },
  { "channel": "Naver Ads", ... }
] }
```

- 숫자 원본 그대로, 계산 불가면 `null`(빌더가 N/A로 표시). 행 순서는 Google/Meta/Naver Ads.
- no-budget 메시지는 오류가 아니다 — "데이터 준비 중"으로 빼지 말고 N/A 규칙대로 세 행 전부.
- 응답 rows의 실제 `media` 값이 상수(`Google`/`Meta`/`Naver`)와 다르면 조용히 0을 만들지
  말고 Executive Summary(`s2`)에 `⚠` 줄로 불일치를 명시한다.
