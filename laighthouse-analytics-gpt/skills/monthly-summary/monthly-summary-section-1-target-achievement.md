# Executive Monthly Section 1: 목표 달성 현황 (Target Achievement)

**report_type:** `monthly-summary` (항상 포함). 이 카드는 **당월(대상 월) 목표 대비 진행
상황**을 보여준다 — `target_date`가 월말이면 그 달의 최종 진행률이, 월중이면 그 시점까지의
진행률이 자연히 나온다.

**규칙은 `shared/references/target-achievement.md`가 단일 소스다** — 호출 2개(목표 1회 + 실적
1회), 목표 없음 판정, 빌더 `s1` 필드, 모드별 카드 구성을 거기서 따른다. 이 스킬의 기간:

| 자리 | 값 |
|---|---|
| `{month}` | target_date의 `YYYY-MM` |
| `{as_of}` | target_date |
| `{start}` ~ `{end}` | 당월 1일 ~ target_date |
