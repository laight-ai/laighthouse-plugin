# Executive MTD Section 1: 목표 달성 현황 (Target Achievement)

**report_type:** `mtd-summary` (항상 포함). 당월 1일~기준일(MTD) 목표 대비 진행 상황 카드.

**규칙은 `shared/references/target-achievement.md`가 단일 소스다** — 호출 2개(목표 1회 + 실적
1회), 목표 없음 판정, 빌더 `s1` 필드, 모드별 카드 구성을 거기서 따른다. 이 스킬의 기간:

| 자리 | 값 |
|---|---|
| `{month}` | target_date의 `YYYY-MM` |
| `{as_of}` | target_date |
| `{start}` ~ `{end}` | 당월 1일 ~ target_date |

- section-3의 6개월 호출과 별개로 부른다 — 스켈레톤 선(先) 게시를 위해 의도적으로 합치지 않는다
  (SKILL.md § 병렬 호출 지침).
