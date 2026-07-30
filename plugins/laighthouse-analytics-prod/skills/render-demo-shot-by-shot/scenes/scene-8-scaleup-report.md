# scene-8: 스케일업 & 보고서 자동 작성 (스토리보드 #8, 1:53–2:14)

승리한 (a) 컨셉 기반 **6개 추가 배경 변형 썸네일**이 생성되고, **깔끔한 1페이지 PDF 보고서
모형**이 연달아 뜨는 장면.

MCP 호출 없음 — 6개 변형은 생성 이미지 목업이므로 placeholder 카드(전부 `.ph-office` 계열
+ 배경 라벨), 보고서 모형은 아래 미니 카드로 그린다. 6개 배경 라벨 고정값:

`스튜디오` · `오피스 로비` · `회의실` · `카페` · `도심 거리` · `라운지`

(캡션은 "(a)-1"~"(a)-6".)

## 대사 (그대로)

- **{persona_name}**: "(a) 시안 대박이네. 다양한 배경으로 6개만 더 만들어줘. 그리고 내일
  미팅에 쓸 깔끔한 보고서로 정리해줄 수 있어?"
- **Laighthouse**: "네, 6개 신규 시안 생성 및 내일 미팅용 보고서 완성을 마쳤습니다."

## HTML

```html
<div class="scene-divider">Scene 8 · 스케일업 &amp; 보고서 자동 작성</div>
<div class="msg user">…"(a) 시안 대박이네. 다양한 배경으로 6개만 더 만들어줘. 그리고 내일 미팅에 쓸 깔끔한 보고서로 정리해줄 수 있어?"…</div>
<div class="msg ai">
  <div class="avatar ai">L</div>
  <div><div class="sender">Laighthouse</div>
    <div class="bubble">
      네, 6개 신규 시안 생성 및 내일 미팅용 보고서 완성을 마쳤습니다.
      <div class="grid-label">(a) 단정한 오피스 룩 컨셉 — 배경 변형 6종</div>
      <div class="thumb-grid" style="grid-template-columns:repeat(3,1fr);">
        <div class="thumb"><div class="ph ph-office">스튜디오</div><div class="cap">(a)-1</div></div>
        <!-- … 6칸 -->
      </div>
      <!-- 1페이지 PDF 보고서 모형 -->
      <div style="margin-top:12px; border:1px solid #e2e8f0; border-radius:10px;
                  background:white; padding:14px; display:flex; gap:12px; align-items:center;">
        <div style="width:54px; height:72px; flex:none; background:#f8fafc;
                    border:1px solid #e2e8f0; border-radius:4px; position:relative; padding:6px;">
          <div style="height:5px; background:#0f172a; border-radius:2px; margin-bottom:4px;"></div>
          <div style="height:3px; background:#e2e8f0; border-radius:2px; margin-bottom:3px;"></div>
          <div style="height:3px; background:#e2e8f0; border-radius:2px; margin-bottom:3px;"></div>
          <div style="height:18px; background:#dbeafe; border-radius:2px; margin-top:6px;"></div>
        </div>
        <div>
          <div style="font-size:13px; font-weight:700;">{brand_name} Meta 소재 개선 보고서.pdf</div>
          <div style="font-size:11.5px; color:#64748b; margin-top:2px;">
            1 page · A/B 테스트 결과 및 신규 소재 제안 · 내일 미팅용</div>
        </div>
      </div>
    </div></div>
</div>
```
