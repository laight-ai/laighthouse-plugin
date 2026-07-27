# creative-section-3: 소재 썸네일 · 성과 매칭

## MCP 도구 호출

`mcp__laighthouse__get_ad_creative_info` 1회 — 소재 썸네일을 가져와 섹션 1의 성과
집계와 조인한다. **실측 스키마 (laighthouse-prism 1.27.0, 2026-07-27 확인):**

```json
// 요청 — 키는 그룹 A 응답(markdown)의 platform_account_id / creative_id 컬럼에서 추출
{
  "brand_name": "{brand_name}",
  "meta":   [{"account_id": 123, "creative_id": 456}, ...],   // 플랫폼별 리스트
  "google": [], "tiktok": []
}
// 응답 — 요청 키를 요청 순서대로 에코
{
  "google": [], "tiktok": [],
  "meta": [{"account_id": 123, "creative_id": 456,
            "thumbnail_image_url": "https://... | null",
            "thumbnail_image_data_url": "data:image/...;base64,... | null"}]
}
```

- **키 추출 규칙**: 그룹 A 응답에서 `platform_account_id`/`creative_id`가 모두 채워진
  행의 고유쌍을 광고비 상위 순으로 **최대 20개** 추려 해당 플랫폼(media 파라미터와
  동일) 리스트로 보낸다. 두 컬럼이 비어 있으면(= `group_by="ad-set"` 폴백 상태이거나
  브랜드 테이블에 creative_id 미컴파일 — 2026-07-27 기준 더마토리 포함 다수) 이 그룹을
  combined.json에서 **생략**한다 → map_report가 "데이터 준비 중" 처리.
- `thumbnail_image_data_url`은 호출당 최대 20개까지만 다운로드되며 실패 시 null
  (URL은 항상 반환). null이면 표에 `-`로 표시된다.

## 저장 형식

```json
{
  "creative": <get_ad_creative_info 응답 그대로>,
  "performance": <섹션 1에서 저장한 get_ad_performance_daily_table 응답 재사용>
}
```

## DOCX 섹션 (매핑 스크립트가 생성 — `map_creative_group_b`)

`table` "소재 썸네일 · 성과 매칭" — [썸네일(이미지 임베드), 소재, 플랫폼, 광고비,
매출, ROAS]. 썸네일은 base64 data URL을 docx에 **이미지로 직접 삽입**하고,
성과 매칭은 creative_id 기준(미매칭 소재는 성과 칸 `-`).
