# MTD Section 8: 캠페인별 성과 심층 분석

**report_type:** `mtd` (항상 포함)

---

## 텍스트 생성: AI가 직접 작성 (`df_dify` MCP 호출 안 함); 수치는 `get_naver_campaign_performance` (mtd-section-12와 동일 호출)

⚠️ **`df_dify` MCP 서버는 현재 호출하지 않는다** (연결 불안정으로 타임아웃 시 빈 응답이 돌아옴).

```
작성 순서:
1. `get_naver_campaign_performance`(start_date=월초, end_date=target_date)로 캠페인별 성과 수치 데이터 수집 (mtd-section-10 캠페인별 성과 호출과 동일, 데이터 재사용 — 이미 캠페인별로 합산/정렬된 최종 값)
2. dify 호출 없이, 1의 수치 데이터를 근거로 AI가 analysis_by_campaign 텍스트를 직접 작성한다.
3. 성과 분석시, 광고비가 큰 것을 우선적으로 분석하되, 다른 캠페인과 비교하여 ROAS나 CTR, CPC, 구매, 평균단가 등 복수 지표의 높고 낮음을 분석하여 확인되는 특이사항을 중심으로 설명한다. 
```

---

## 응답 데이터 구조

```json
{
  "analysis_by_campaign": "광고비를 가장 많이 소진한 캠페인 3개를 선정하였습니다.\n\n분유_MO(파워링크)\n이번 달 클릭수는 82만건으로...\n\n06_음료(SP)_PC (쇼핑검색)\nCTR이 이번 달 8.5%로..."
}
```

- `analysis_by_campaign`는 `\n\n`으로 구분된 블록으로 구성
- 각 블록의 첫 줄이 안내문 또는 캠페인명이면 `<h4>` 소제목으로 렌더링 (첫 블록은 인트로 문단이라 `<p>`만)
- 나머지 문장은 `<p>`로 렌더링

---

## DOCX 섹션

```json
{
  "type": "text",
  "heading": "캠페인별 성과 심층 분석",
  "body": "{analysis_by_campaign}"
}
```

- `analysis_by_campaign`은 `\n\n`으로 구분된 블록 문자열(첫 블록은 인트로 문단, 이후 블록은
  캠페인명 + 설명)을 그대로 `body`에 넣는다 — 정적 문서에서는 소제목/본문을 별도 마크업으로
  나누지 않고 하나의 텍스트 블록으로 낸다.
- 강조하고 싶은 수치가 있으면 문장 자체에 자연스럽게 녹여 쓴다.