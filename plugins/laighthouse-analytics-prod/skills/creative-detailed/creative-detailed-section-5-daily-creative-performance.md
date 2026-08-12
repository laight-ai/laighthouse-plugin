# Breezm Creative Section 5: 최근 7일 소재 단위 누적 성과

**report_type:** `creative-detailed` — **브리즘(airbridge 기반) 전용** (항상 포함). **메타
(Meta Ads)만 대상.** 기준일 포함 **최근 7일을 통째로 합산**해 소재 단위 8개 지표를 한 표에
보여준다. ⚠️ 파일명의 "daily"는 매일 갱신되는 보고서라는 맥락일 뿐, **이 섹션의 데이터는
날짜별이 아니라 7일 누적값**이다.

> ℹ️ 표 HTML/검색/페이지네이션과 CTR·CPA·ROAS 계산·₩/% 포맷·광고비 내림차순 정렬·`<tr>` 생성은
> 전부 템플릿+빌더가 한다 — 모델은 조인이 끝난 소재별 **원본 수치**만 `s5.rows`에 넣는다.

## MCP 도구 호출: 신규 호출 없음 — section-1의 range_table 응답 2개를 그대로 재사용

section-1이 호출한 `get_ad_performance_range_table`(`media="meta"`/`media="airbridge"`,
`group_by:"ad"`, 최근 7일) 응답을 재사용한다 — **다시 호출하지 않는다**. section-1은 랭킹
1·2위만 뽑았지만 이 섹션은 **모든 소재를 전부** 나열한다(같은 원본의 다른 가공). 응답은 이미
소재당 한 행(7일 합산 완료)이므로 daily 응답을 받아 합산할 필요가 전혀 없다 — **받은 그
자리에서 바로 조인해 rows를 만든다**(Bash/스크립트/스크래치 파일 불필요, § SKILL.md 실행 방식
절대 지침).

## 조인 규칙 (section-1과 동일)

- `campaign_name`+`asset_group`+`ad_name` **세 필드 정확 일치**만 쓴다(정규화/부분일치 금지).
- 매체 쪽에만 있는 소재(airbridge 미매칭) → `revenue`/`reservation`을 **null**로 넣는다
  (빌더가 매출/예약/CPA/ROAS 칸을 `-`로 렌더링. 0과 다르다 — 0은 매칭됐는데 값이 0인 경우).
- airbridge 쪽에만 있는 소재 → 노출/클릭/광고비를 알 수 없으므로 rows에 포함하지 않는다.

## 빌더 `s5` 필드

```json
"s5": { "rows": [
  { "media": "Meta Ads", "campaign": "{campaign_name}", "asset_group": "{asset_group}", "ad_name": "{ad_name}",
    "impression": 12345, "click": 67, "cost": 89012,
    "revenue": 345678, "reservation": 3 }
] }
```

- 수치는 응답 원본 그대로(포맷·반올림·정렬 금지 — 빌더가 한다). 빌더가 계산하는 파생지표:
  CTR = 클릭÷노출×100(노출 0이면 N/A), CPA = 광고비÷예약 완료(0/없음이면 `-`),
  ROAS = 매출÷광고비×100(광고비 0이면 `-`).
- rows가 크면 `"rows_file": "/tmp/s5.json"`(rows 배열이 든 JSON 파일 경로)로 넘겨도 된다.
- 데이터가 비어있으면 `s5` 키를 뺀다 → "데이터 준비 중" 카드. 행 선별·근사치 대체는 금지 —
  전 소재를 전부 넣거나, 불가능하면 키를 뺀다(§ 데이터 처리 원칙의 이분법).
