# MTD Section 1: 목표 달성 현황 (Target Achievement)

**report_type:** `mtd-detailed` (항상 포함). 당월 MTD 목표 대비 진행 상황 카드.

**규칙은 `shared/references/target-achievement.md`가 단일 소스다** — 호출 2개(목표 1회 + 실적
1회), 목표 없음 판정, 빌더 `s1` 필드, 모드별 카드 구성을 거기서 따른다. 이 스킬의 기간:

| 자리 | 값 |
|---|---|
| `{month}` | target_date의 `YYYY-MM` |
| `{as_of}` | target_date |
| `{start}` ~ `{end}` | 당월 1일 ~ target_date |

- 실적 호출(`get_ad_performance`, 당월 month grain, `group_by:["media"]`) 응답은 section-6이
  매체별 실적으로 그대로 재사용한다.
- section-6용 **매체별** `get_target_progress_v2` 호출(`mtd-detailed-section-6-channel-budget.md`)도
  이 섹션의 두 호출과 **같은 배치**에서 함께 발사한다 — section-1 카드는 매체별 응답을 합산하지
  않고 전체 매체(`media` 생략) 1회 응답만 쓴다.
