# Daily Section 1: 목표 달성 현황 (Target Achievement)

**report_type:** `daily-detailed` (항상 포함). 데일리 보고서에서도 이 카드는 **당월 MTD 목표
대비 진행 상황**을 그대로 보여준다 (예산이 월 단위로 설정되므로 매일 확인할 가치가 있다).

**규칙은 `shared/references/target-achievement.md`가 단일 소스다** — 호출 2개(목표 1회 + 실적
1회), 목표 없음 판정, 빌더 `s1` 필드, 모드별 카드 구성을 거기서 따른다. 이 스킬의 기간:

| 자리 | 값 |
|---|---|
| `{month}` | target_date의 `YYYY-MM` |
| `{as_of}` | target_date |
| `{start}` ~ `{end}` | 당월 1일 ~ target_date |

- 응답 rows의 `media` 값이 디스커버리 `media_list`와 다르면 Executive Summary(`s2`)에 `⚠`로
  시작하는 불일치 안내 줄을 추가한다.
