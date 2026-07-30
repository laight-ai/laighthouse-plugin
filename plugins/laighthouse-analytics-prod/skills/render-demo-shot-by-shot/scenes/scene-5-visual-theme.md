# scene-5: 원인 분석 — Visual Theme Analysis (스토리보드 #5, 0:55–1:13)

화면이 분할되며 **"지난 12개월간 잘 나온 소재 썸네일"**과 **"{M}월에 망한 소재 썸네일"**이
비교되는 장면. 썸네일은 실제 소재 이미지를 도구로 가져와 그대로 배치한다.

## MCP 도구 호출 (2단계)

1. `mcp__laighthouse__get_ad_performance_monthly_table` 1회 — 소재(ad) 단위 성과:

```json
{
  "brand_name": "{brand_name}",
  "start_month": "{target_month - 11개월}",
  "end_month": "{target_month}",
  "group_by": "ad",
  "media": "meta"
}
```

   - 응답에서 `platform_account_id`/`creative_id`가 모두 채워진 행만 대상으로:
     - **잘 나온 소재 4개**: `{target_month}` 이전 월 행을 광고비 내림차순 상위 20행으로
       자른 뒤, 그 안에서 ROAS 상위 4개 고유 creative.
     - **망한 소재 4개**: `{target_month}` 월 행을 광고비 내림차순 상위 20행으로 자른 뒤,
       그 안에서 ROAS 하위 4개 고유 creative.
   - 두 컬럼이 비어 있으면(브랜드 테이블에 creative_id 미컴파일) 썸네일 단계
     (`get_ad_creative_info`)를 건너뛰고 8칸 전부 placeholder 카드로 렌더링한다 — 오류가
     아니다. 이때 잘 나온 쪽 4칸은 `.ph-office`(캡션 "Top Creative 1"~"4"), 망한 쪽
     4칸은 `.ph-sea`(캡션 "{M}월 신규 소재 1"~"4")로 고정한다.

2. `mcp__laighthouse__get_ad_creative_info` 1회 — 위에서 추린 최대 8개 키:

```json
{ "brand_name": "{brand_name}",
  "meta": [{"account_id": ..., "creative_id": ...}, ...] }
```

   - `thumbnail_image_data_url`(base64)을 `<img src>`에 그대로 넣는다. null이면 해당 칸만
     placeholder 카드(잘 나온 쪽 `.ph-office`, 망한 쪽 `.ph-sea`)로 대체.
   - 캡션은 성과 응답의 소재명(있으면)과 ROAS 값 그대로 (`ROAS 412%` 식).

## 대사 (그대로 — 브랜드명/월만 치환)

- **{persona_name}**: "왜 성과가 안 좋았던 거야?"
- **Laighthouse**: "지난 12개월간 잘 팔린 소재는 모두 '깔끔하고 단정한 오피스 룩'이었습니다.
  하지만 이번 {M}월에는 처음으로 '휴양지/바다 컨셉'으로 바꿨고, 이 소재들이 인스타그램에
  집중적으로 노출되면서 Meta 성과가 떨어졌습니다."

## HTML

```html
<div class="scene-divider">Scene 5 · 원인 분석 (Visual Theme Analysis)</div>
<div class="msg user">…"왜 성과가 안 좋았던 거야?"…</div>
<div class="msg ai">
  <div class="avatar ai">L</div>
  <div><div class="sender">Laighthouse</div>
    <div class="bubble">
      지난 12개월간 잘 팔린 소재는 모두 '깔끔하고 단정한 오피스 룩'이었습니다.
      하지만 이번 {M}월에는 처음으로 '휴양지/바다 컨셉'으로 바꿨고, 이 소재들이
      인스타그램에 집중적으로 노출되면서 Meta 성과가 떨어졌습니다.
      <div class="grid-label good">지난 12개월간 잘 나온 소재</div>
      <div class="thumb-grid">
        <div class="thumb"><img src="{data_url}"><div class="cap">{소재명 · ROAS n%}</div></div>
        <!-- ×4 -->
      </div>
      <div class="grid-label bad">{M}월에 망한 소재</div>
      <div class="thumb-grid">
        <div class="thumb"><img src="{data_url}"><div class="cap">{소재명 · ROAS n%}</div></div>
        <!-- ×4 -->
      </div>
    </div></div>
</div>
```
