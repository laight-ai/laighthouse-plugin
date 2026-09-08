# Creative Section 5: 최근 7일 소재 단위 누적 성과

**report_type:** `creative-detailed` (항상 포함). **`chosen_media` 하나만 대상**(SKILL.md 매체
선택). 기준일 포함 **최근 7일을 통째로 합산**해 소재 단위 지표를 한 표에 보여준다(노출/클릭/
CTR/광고비/매출/ROAS + conversion 역할이 있을 때만 전환/CPA). ⚠️ 파일명의 "daily"는 매일
갱신되는 보고서라는 맥락일 뿐, **이 섹션의 데이터는 날짜별이 아니라 7일 누적값**이다.

> ℹ️ 표 HTML/검색/페이지네이션과 CTR·CPA·ROAS 계산·통화/% 포맷·광고비 내림차순 정렬·
> `<thead>`/`<tr>` 생성은 전부 템플릿+빌더가 한다 — 모델은 소재별 **원본 수치**만 `s5.rows`에
> 넣고, 최상위에 `metric_keys`(+`currency`)를 넘긴다. `<th>` 라벨은 `metric_keys` 값 그대로
> 렌더링되고, `conversion`이 없으면 전환·CPA 컬럼이 통째로 생략된다.

## MCP 도구 호출: 신규 호출 없음 — section-1의 total 응답을 그대로 재사용

section-1이 호출한 `get_ad_performance`(`time_grain:"total"`,
`filters:{"media":["<chosen_media>"]}`, 소재 단위, 최근 7일) 응답을 재사용한다 — **다시
호출하지 않는다**. section-1은 랭킹 1·2위만 뽑았지만 이 섹션은 **모든 소재를 전부**
나열한다(같은 원본의 다른 가공). 응답은 이미 소재당 한 행(7일 합산 완료)이고 매출/전환도
같은 행에 있으므로 day 응답 합산도 조인도 필요 없다 — **받은 그 자리에서 바로 rows를
만든다**(Bash/스크립트/스크래치 파일 불필요, § SKILL.md 실행 방식 절대 지침).

## 매핑 규칙

- 각 행을 그대로 rows 한 항목으로 옮긴다: `impression`←impression 키, `click`←click 키,
  `cost`←cost 키, `revenue`←revenue 키, `conversion`←conversion 키(`metric_keys`에 있을
  때만), `asset_group`←`ad_group_name`(빌더 필드명은 기존 그대로 `asset_group`이다),
  `media`←`chosen_media` 값 그대로(접미사·번역 없음).
- revenue/conversion 키 값이 행에 없으면(null) 그대로 **null**로 넣는다(빌더가 매출/전환/
  CPA/ROAS 칸을 `-`로 렌더링. 0과 다르다 — 0은 값이 실제로 0인 경우).

## 빌더 `s5` 필드

```json
"metric_keys": { "cost": "<cost 키>", "impression": "<impression 키>", "click": "<click 키>", "revenue": "<revenue 키>", "conversion": "<conversion 키 — 있을 때만>" },
"s5": { "rows": [
  { "media": "<chosen_media>", "campaign": "{campaign_name}", "asset_group": "{ad_group_name}", "ad_name": "{ad_name}",
    "impression": 12345, "click": 67, "cost": 89012,
    "revenue": 345678, "conversion": 3 }
] }
```

- 수치는 응답 원본 그대로(포맷·반올림·정렬 금지 — 빌더가 한다). 빌더가 계산하는 파생지표:
  CTR = 클릭÷노출×100(노출 0이면 N/A), CPA = 광고비÷전환(0/없음이면 `-`, conversion 역할이
  있을 때만), ROAS = 매출÷광고비×100(광고비 0이면 `-`).
- rows가 크면 `"rows_file": "/tmp/s5.json"`(rows 배열이 든 JSON 파일 경로)로 넘겨도 된다.
- 데이터가 비어있으면 `s5` 키를 뺀다 → "데이터 준비 중" 카드. 행 선별·근사치 대체는 금지 —
  전 소재를 전부 넣거나, 불가능하면 키를 뺀다(§ 데이터 처리 원칙의 이분법).
