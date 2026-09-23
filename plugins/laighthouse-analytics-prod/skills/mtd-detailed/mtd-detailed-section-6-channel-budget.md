# MTD Section 6: 광고 매체별 현황 (Channel Budget)

**report_type:** `mtd-detailed` (항상 포함). 매체별 목표 대비 소진/달성 현황. 행은
디스커버리로 받은 `media_list`의 각 매체 하나씩, **디스커버리 순서** — 고정 매체 목록·"Others"
행은 없다. Organic은 광고비/목표 개념이 없어 이 표에 넣지 않는다.

> ℹ️ 표 HTML(`<thead>` 포함)/파생 비율/통화·%·`-` 포맷/**모드별 컬럼 선택**은 전부 템플릿+빌더가
> 한다 — 모델은 매체별 **목표 원본 + 역할 원본 실적**만 빌더 입력 JSON의 `s6.rows`에 넣는다.
>
> | 모드 | 컬럼 |
> |---|---|
> | 매출 있음 | 월 예산 · 소진액 · 예산 소진율 · 목표 매출 · 광고 매출 · 매출 달성률 · 목표 ROAS · ROAS |
> | 매출 없음 | 월 예산 · 소진액 · 예산 소진율 · 노출 · 클릭 · CTR · CPC |

## MCP 도구 호출: `get_target_progress_v2` × len(media_list) (매체별 — 이 스킬에서 유일)

```json
{ "brand_name": "<brand>", "month": "YYYY-MM", "media": "<media_list 값 그대로>", "as_of_date": "target_date" }
```

- `generic-report-pattern.md` 5절 — 매체별 목표가 필요한 **유일한** 표라서 여기서만 매체마다
  부른다. `media`에는 `media_list`의 값을 **그대로** 넣는다(`.lower()`·표기 변환 금지 — 서버가
  대소문자 무시·한국어 별칭으로 매칭한다).
- section-1의 호출들(전체 매체 목표 1회 + 당월 실적 1회)과 **같은 1차 배치**에서 동시에 발사한다.
- 응답 처리 (아래는 전부 **목표 없음**, 오류 아님):
  - `No {media} budget/target available for {month}.` 한 줄
  - 마트 전제 미충족 안내 한 줄
  - 호출 에러(구버전 서버의 `media` enum 스키마 에러 포함)
  - 0 표(target 0) — 매칭되는 매체가 없을 때
- 표가 오면 `cost` 행 `target`(> 0일 때만) → `월_예산`, `revenue` 행 `target`(> 0일 때만) →
  `목표_매출`. **`actual`/`progress_ratio` 열은 쓰지 않는다.**

## 실적 — 신규 호출 없음

- `cost`/`revenue`/`impression`/`click`: section-1의 `get_ad_performance`(당월, month grain,
  `group_by:["media"]`, `filters` 생략) 응답에서 그 매체 행(`media` = 그 매체 문자열)의 역할 키
  값. **목표 유무와 무관하게 항상 이 값**이다 — 목표 도구의 `actual`은 쓰지 않는다.
  `metric_keys`에 revenue가 없으면 `revenue`는 넣지 않는다.

## 빌더 `s6.rows` (`media_list` 전 매체 — 목표 없는 매체도 행을 빼지 않는다)

```json
{ "rows": [
  { "name": "<media 값 1>", "월_예산": 50000000, "목표_매출": null,
    "cost": 21000000, "revenue": 34000000, "impression": 1200000, "click": 18000 },
  { "name": "<media 값 2>", "월_예산": null, "목표_매출": null,
    "cost": 8000000, "revenue": 12000000, "impression": 640000, "click": 9100 }
] }
```

- `name`은 응답 `media` 값 **그대로**(접미사·번역 없음). 행 순서는 `media_list` 순서.
- 숫자 원본 그대로, 목표 없음이면 `null`(빌더가 `-`로 표시).
- 빌더가 계산하는 것(참고 — 재구현 금지): 예산 소진율 = cost ÷ 월_예산 × 100, 매출 달성률 =
  revenue ÷ 목표_매출 × 100, 목표 ROAS = 목표_매출 ÷ 월_예산 × 100, ROAS = revenue ÷ cost × 100,
  CTR = click ÷ impression × 100, CPC = cost ÷ click. 분모가 없거나 0이면 `-`.
- 목표 없음은 오류가 아니다 — "데이터 준비 중"으로 빼지 말고 `-` 규칙대로 전 행을 넣는다.
- 응답 rows의 `media` 값이 디스커버리 `media_list`와 다르면 조용히 0을 만들지 말고 Executive
  Summary(`s2`)에 `⚠` 줄로 불일치를 명시한다.
