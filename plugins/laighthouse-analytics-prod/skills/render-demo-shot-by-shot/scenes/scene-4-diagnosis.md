# scene-4: 데이터 진단 (스토리보드 #4, 0:33–0:55)

Andy가 질문을 던지고, Laighthouse 답변 말풍선 안에 **대시보드 형태의 수치 표 2개**가
들어가는 장면. 표 수치는 전부 실제 MCP 응답이다.

## MCP 도구 호출

`mcp__laighthouse__get_ad_performance_monthly_table` **3회** — `media`만 바꿔 호출:

```json
{
  "brand_name": "{brand_name}",
  "start_month": "{target_month - 2개월}",   // 예: target_month가 2026-07이면 2026-05
  "end_month": "{target_month}",
  "group_by": "total",
  "media": "google" | "meta" | "naver"
}
```

- `campaign_type`은 넣지 않는다 (전체).
- 응답은 월×지표 markdown 표 — 값을 그대로 쓴다. ROAS가 소수(예: 0.87)면 ×100 후 %로
  표기한다 (0.87 → 87%).
- 세 매체 중 일부가 빈 응답이어도 오류가 아니다 — 해당 행만 `-`로 채운다.

## 표 구성 (Laighthouse 말풍선 내부)

1. **표 1 — 최근 3개월 매체별 요약**: 행 = Meta / Google / Naver, 열 = 3개월 각각의
   ROAS (응답의 ROAS 컬럼 그대로 — 매출/광고비로 재계산하지 않는다). 합계·평균 등 파생
   열은 만들지 않는다.
2. **표 2 — Meta 월별 상세**: meta 응답의 월별 행을 그대로 (광고비/노출/클릭/전환/매출/
   ROAS 등 응답에 있는 컬럼 중 5~6개).

## 대사 (그대로 — 브랜드명/월만 치환)

- **{persona_name}**: "{brand_name}의 Meta(인스타그램/페이스북) 성과가 떨어졌어. 무슨 일이야?"
- **Laighthouse**: "최근 3개월간 Meta, Google, Naver 데이터를 분석했습니다..."
- **Laighthouse** (표 2개 아래, 분석 결과 문단): "Google과 Naver 성과는 유지되었으나,
  Meta 성과만 급락했습니다. 원인은 **{M}월에 신규 집행한 광고 소재들**입니다."

⚠️ 분석 결과 문장은 대본 고정이다 — 실제 수치가 이 서사와 달라도 문장을 고치거나 수치를
맞추지 않는다 (목업 원칙).

## HTML

```html
<div class="scene-divider">Scene 4 · 데이터 진단</div>
<div class="msg user">
  <div class="avatar user">{…}</div>
  <div><div class="sender">{persona_name}</div>
    <div class="bubble">{brand_name}의 Meta(인스타그램/페이스북) 성과가 떨어졌어. 무슨 일이야?</div></div>
</div>
<div class="msg ai">
  <div class="avatar ai">L</div>
  <div><div class="sender">Laighthouse</div>
    <div class="bubble">
      최근 3개월간 Meta, Google, Naver 데이터를 분석했습니다...
      <div class="table-caption">최근 3개월 매체별 성과</div>
      <table>{표 1}</table>
      <div class="table-caption">Meta 월별 상세</div>
      <table>{표 2}</table>
      <p style="margin-top:10px;">Google과 Naver 성과는 유지되었으나, Meta 성과만
      급락했습니다. 원인은 <b>{M}월에 신규 집행한 광고 소재들</b>입니다.</p>
    </div></div>
</div>
```
