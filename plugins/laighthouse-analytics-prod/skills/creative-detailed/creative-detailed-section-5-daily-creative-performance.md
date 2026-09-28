# Creative Section 5: 최근 7일 소재 단위 누적 성과

**report_type:** `creative-detailed` (항상 포함). **`chosen_media` 하나만 대상**(SKILL.md 매체
선택). 기준일 포함 **최근 7일을 통째로 합산**해 소재 단위 지표를 한 표에 보여준다 — 매출 있음 모드:
노출/클릭/CTR/광고비/매출/ROAS, **매출 없음 모드: 노출/클릭/CTR/광고비/CPC** (+ 두 모드 모두
conversion 역할이 있을 때만 전환/CPA). ⚠️ 파일명의 "daily"는 매일
갱신되는 보고서라는 맥락일 뿐, **이 섹션의 데이터는 날짜별이 아니라 7일 누적값**이다.

> ℹ️ 표 HTML/검색/페이지네이션과 모드별 컬럼 선택·CTR·CPC·CPA·ROAS 계산·통화/% 포맷·광고비 내림차순 정렬·
> `<thead>`/`<tr>` 생성은 전부 템플릿+빌더가 하고, 소재별 원본 수치 rows는 `rank_creatives.py`
> (`"s5": true`)가 만든다 — 모델은 `s5: {}`와 최상위 `rank_file`·`metric_keys`(+`currency`)만
> 넘긴다. `<th>` 라벨은 `metric_keys` 값 그대로
> 렌더링되고, `conversion`이 없으면 전환·CPA 컬럼이 통째로 생략된다.

## MCP 도구 호출: 신규 호출 없음 — section-1의 total 응답을 그대로 재사용

section-1이 호출한 `get_ad_performance`(`time_grain:"total"`,
`filters:{"media":["<chosen_media>"]}`, 소재 단위, 최근 7일) 응답을 재사용한다 — **다시
호출하지 않는다**. section-1은 랭킹 1·2위만 뽑았지만 이 섹션은 **모든 소재를 전부** 나열한다
(같은 원본의 다른 가공). rows는 section-1의 `rank_creatives.py` 한 번 실행(`"s5": true`)이 출력
파일의 `s5_rows`로 이미 만들어 둔다 — 모델이 행을 옮겨 적거나 거르지 않는다.

## 매핑 규칙 (스크립트가 적용 — 참고용 스펙)

- 각 행을 그대로 rows 한 항목으로 옮긴다: `impression`←impression 키, `click`←click 키,
  `cost`←cost 키, `revenue`←revenue 키(`metric_keys`에 있을 때만 — 매출 없음 모드는 키 자체를
  생략), `conversion`←conversion 키(`metric_keys`에 있을 때만), `asset_group`←`ad_group_name`,
  `media`←`chosen_media` 값 그대로(접미사·번역 없음).
- `ad_name`이 비었거나 `"-"`이면 광고 칸은 `"<ad_group_name> (소재명 없음)"`(section-1/3/4와 같은
  폴백).
- revenue/conversion 키 값이 행에 없으면(null) 그대로 **null**로 넣는다(빌더가 그 소재의 매출/전환/
  CPA/ROAS 칸을 `-`로 렌더링). 합계·랭킹에서는 null 매출을 0으로 계산한다(SKILL.md 공통 규칙).

## 빌더 `s5` 필드

```json
"metric_keys": { "cost": "<cost 키>", "impression": "<impression 키>", "click": "<click 키>", "revenue": "<revenue 키 — 있을 때만>", "conversion": "<conversion 키 — 있을 때만>" },
"currency": "<discover.py 출력의 currency>",
"rank_file": "/tmp/creative_rank.json",
"s5": {}
```

- `s5`는 빈 객체로 둔다 — 빌더가 `rank_file`의 `s5_rows`를 쓴다. 빌더가 계산하는 파생지표:
  CTR = 클릭÷노출×100(소수 2자리, 노출 0이면 N/A), CPC = 광고비÷클릭(매출 없음 모드만, 클릭 0이면
  `-`), CPA = 광고비÷전환(0/없음이면 `-`, conversion 역할이 있을 때만), ROAS = 매출÷광고비×100(매출
  있음 모드만, 광고비 0이면 `-`).
- 표는 카드 안에서만 가로 스크롤되고(카드 밖으로 넘치지 않는다), 페이지 번호는
  `1 … 4 5 [6] 7 8 … 47`처럼 접혀 표시된다(템플릿 고정).
- (직접 넘길 때만) `"rows": [...]` 또는 `"rows_file": "<rows 배열 JSON 경로>"`도 받는다.
- 데이터가 비어있으면 `s5` 키를 뺀다 → "데이터 준비 중" 카드. 행 선별·근사치 대체는 금지 —
  전 소재를 전부 넣거나, 불가능하면 키를 뺀다(§ 데이터 처리 원칙의 이분법).
