# scene-6: A/B 테스트 및 신규 소재 생성 (스토리보드 #6, 1:13–1:34)

대화창에 **레퍼런스 이미지 그리드(무드보드)**가 뜨고 Andy가 몇 개를 클릭, 곧이어
**4개의 신규 광고 시안 썸네일**이 왼쪽에서 오른쪽 순서대로 생성되는 장면.

MCP 호출 없음 — 무드보드와 신규 시안은 도구로 가져올 수 없는 "생성된 이미지" 목업이므로
전부 placeholder 카드로 그린다. 4개 시안의 순서와 라벨은 아래 고정값 그대로:

| 순서 | 라벨 (그대로) | placeholder 클래스 |
|---|---|---|
| (a) | 남성/단정한 오피스 | `.ph-office` |
| (b) | 남성/바다 | `.ph-sea` |
| (c) | 여성/단정한 오피스 | `.ph-office` |
| (d) | 여성/리조트 | `.ph-resort` |

무드보드는 8칸 그리드(`.ph-office`/`.ph-sea`/`.ph-resort`/`.ph-studio` 반복, 캡션
"Ref 01"~"Ref 08")로 그리고, **Ref 01·Ref 02·Ref 05·Ref 08 네 칸에 고정으로**
`.selected` 클래스를 줘 "{persona_name}이 클릭한" 상태를 표현한다 (매 실행 동일해야 한다).

## 대사 (그대로)

- **{persona_name}**: "고객사에 보고할 확실한 근거가 필요해. 빠른 A/B 테스트를 돌려줄 수 있어?"
- **Laighthouse**: "레퍼런스 스타일 중 어떤 것을 테스트할까요?" (+ 무드보드 그리드)
- **Laighthouse** (시안 생성 말풍선): "4가지 신규 변형 시안을 생성했습니다." (+ 시안 4칸 그리드)
- **{persona_name}**: "좋아, 이 시안들로 승인할게. 시간 없으니 서둘러줘."

## HTML

```html
<div class="scene-divider">Scene 6 · A/B 테스트 및 신규 소재 생성</div>
<div class="msg user">…"고객사에 보고할 확실한 근거가 필요해. 빠른 A/B 테스트를 돌려줄 수 있어?"…</div>
<div class="msg ai">
  <div class="avatar ai">L</div>
  <div><div class="sender">Laighthouse</div>
    <div class="bubble">
      레퍼런스 스타일 중 어떤 것을 테스트할까요?
      <div class="grid-label">레퍼런스 무드보드</div>
      <div class="thumb-grid">
        <div class="thumb selected"><div class="ph ph-office">Office Look</div><div class="cap">Ref 01</div></div>
        <!-- … Ref 08까지, 3~4칸에 selected -->
      </div>
    </div></div>
</div>
<div class="msg ai">
  <div class="avatar ai">L</div>
  <div><div class="sender">Laighthouse</div>
    <div class="bubble">
      4가지 신규 변형 시안을 생성했습니다.
      <div class="thumb-grid">
        <div class="thumb"><div class="ph ph-office">남성<br>단정한 오피스</div><div class="cap">Variant (a)</div></div>
        <div class="thumb"><div class="ph ph-sea">남성<br>바다</div><div class="cap">Variant (b)</div></div>
        <div class="thumb"><div class="ph ph-office">여성<br>단정한 오피스</div><div class="cap">Variant (c)</div></div>
        <div class="thumb"><div class="ph ph-resort">여성<br>리조트</div><div class="cap">Variant (d)</div></div>
      </div>
    </div></div>
</div>
<div class="msg user">…"좋아, 이 시안들로 승인할게. 시간 없으니 서둘러줘."…</div>
```
