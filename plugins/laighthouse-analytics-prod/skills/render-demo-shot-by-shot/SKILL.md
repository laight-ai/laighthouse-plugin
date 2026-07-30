---
name: render-demo-shot-by-shot
description: >
  This skill should be used when the user asks to "스토리보드대로 따라가줘", "스토리보드대로 해줘",
  "스토리보드대로 진행해줘", "Shot-by-Shot대로 따라가줘", "샷바이샷대로 진행해",
  "follow the storyboard", or wants the Laighthouse demo-video storyboard
  (Shot-by-Shot.pdf scenes #3–#8, the blue-marked Claude chat scenes) followed
  scene-by-scene and rendered as a single HTML chat mockup with real MCP performance
  data and real creative thumbnails.
metadata:
  version: "0.1.0"
---

> ⚡ **thinking 지침**: 이 스킬 실행 시 thinking(추론)은 최대한 짧게 유지한다. 바로
> MCP 호출 → 데이터 수신 → 렌더링 순서로 진행한다.

## 역할

Laighthouse 데모 영상 스토리보드(Shot-by-Shot)의 **파란색 표시 장면(#3~#8, Claude 채팅
장면)**을 하나의 HTML **채팅 목업**으로 렌더링하는 오케스트레이터. Claude 데스크톱 앱
채팅 창을 흉내 낸 화면 안에서 Andy(사용자)와 Laighthouse(AI)의 대화가 스토리보드 순서
그대로 흐르고, 대화 중간에 성과 표·소재 썸네일·차트가 삽입된다.

이것은 **목업(mockup)**이다 — 보고서가 아니라 "이렇게 보인다"를 보여주는 시연 화면이다.

## 데이터 · 목업 원칙 (절대 지침)

> 🚫 **대사(대본)는 아래 각 장면 파일에 적힌 문구를 한 글자도 바꾸지 않고 그대로, 장면
> 순서 그대로 렌더링한다.** 요약·의역·재배열·생략 금지. 허용되는 치환은 장면 파일 속
> 템플릿 토큰 딱 두 가지뿐이다 — `{brand_name}`(스토리보드 원문의 "Jericho")과
> `{M}`(원문의 "7", `target_month`의 월 숫자).
>
> 🚫 **성과 수치는 MCP 응답을 그대로 렌더링한다.** 결측 보정·재계산·정렬 변경·임의 판단
> 전부 금지 (예외: ROAS 소수 → % 변환처럼 각 장면 파일에 명시된 표기 변환뿐).
> **실제 수치가 대본과 모순되어도(예: Meta가 실제로는 떨어지지 않았어도) 대사는 그대로,
> 수치도 그대로 둔다** — 목업이므로 서로 맞출 필요가 없고, 맞추려고 수치를 지어내는 것이
> 최악의 오류다.
>
> 🚫 **소재 썸네일은 `get_ad_creative_info`가 준 이미지를 그대로, 장면 파일에 정의된
> 위치·순서대로 배치한다.** 도구가 못 주는 이미지(무드보드, 신규 생성 시안)는 장면 파일에
> 정의된 placeholder 카드로 렌더링한다 — 외부 이미지 URL을 임의로 가져오지 않는다.
>
> 🚫 **`.py`/`.js`/`.ipynb` 등 별도 스크립트 파일을 절대 생성하지 않는다.** MCP 도구는
> 직접 호출하고 결과를 곧바로 HTML 문자열 조합에 사용한다. 이 스킬이 만드는 파일은 오직
> 최종 목업 HTML 하나뿐이다.
>
> ⏱ **긴 대기 없이 스켈레톤을 먼저 보여준다.** 장면 #3(MCP 호출 불필요)까지 채운 골격을
> 1차로 Artifact에 게시하고, 이후 장면 #4~#5의 MCP 데이터가 준비되는 대로 같은 Artifact
> 파일을 갱신해 placeholder를 실제 값으로 교체한다.

## 입력 파라미터

| 파라미터 | 설명 | 기본값 |
|--------|------|------|
| brand_name | MCP 호출용 브랜드명 (`get_brand_list` 응답과 정확히 일치). 대사 속 "Jericho"도 이 이름으로 치환 | 없음 — 미지정 시 `get_brand_list`를 호출해 사용자에게 선택지를 보여주고 확인받는다 |
| target_month | 대본의 "성과가 떨어진 달" (`YYYY-MM`). 대사 속 "7월"이 이 월로 치환된다 | 지난달 |
| persona_name | 채팅 사용자 이름 | Andy |

장면 구성은 항상 #3~#8 여섯 장면 전부이며 사용자가 장면을 골라 지정하는 개념이 없다.

## 실행 순서

1. 파라미터를 파싱한다. brand_name이 없으면 `get_brand_list`로 확인받는다. 사용자가
   brand_name을 지정했어도 `get_brand_list` 응답과 정확히 일치하는지 먼저 확인하고,
   불일치하면 가장 근접한 이름을 제시해 확인받는다 (불일치 이름으로 호출하면 전부 실패).
2. **1차 스켈레톤 게시**: 장면 #3·#6·#7·#8은 완성 상태로(전부 MCP 불필요 — #7 차트의
   고정 목업 수치·스크립트도 이 시점에 포함), 장면 #4의 표 2개와 #5의 썸네일 그리드
   2개만 "데이터 준비 중" placeholder로 채운 골격을 Artifact에 게시한다. 대사 말풍선은
   여섯 장면 모두 처음부터 전부 렌더링한다.
3. 장면 #4~#5의 MCP 도구를 호출한다 (각 장면 파일에 명시된 정확한 도구/파라미터 참고):
   - #4: `get_ad_performance_monthly_table` — media별(google/meta/naver) 최근 3개월.
   - #5: `get_ad_performance_monthly_table`(meta, `group_by:"ad"`) →
     `get_ad_creative_info`(meta 키 리스트)로 썸네일 확보.
4. 장면 #6~#8은 MCP 호출 없이 장면 파일의 고정 대본·placeholder·고정 목업 수치로
   렌더링한다 (#7의 A/B 차트 수치는 장면 파일에 고정값으로 정의되어 있다 — 임의 변경 금지).
5. 아래 **장면 Import 목록**의 파일을 순서대로 전부 import해 `{SCENES}`에 삽입한다.
6. 이 스킬 폴더의 `assets/chart.umd.min.js` 내용 전체를 `{CHART_JS_INLINE}` 자리에 그대로
   삽입한다 (CDN `<script src>` 절대 금지 — Artifact CSP가 외부 스크립트를 차단해 차트가
   빈 캔버스로 남는다).
7. 완성된 HTML을 **두 곳에 동시에** 낸다:
   - Artifact 도구로 게시 (2단계 스켈레톤과 같은 파일 갱신).
   - `~/Downloads/laighthouse-reports/{brand_name}_demo_shot-by-shot_{target_month}.html`
     로 저장 (디렉터리가 없으면 생성).
8. 완료 메시지는 아래 **완료 메시지 형식**을 그대로 따른다.

## 장면 Import 목록

| 순서 | 장면 (스토리보드 번호) | Import 경로 |
|-----|------|------------|
| 1 | #3 AI 에이전트 연결 | `@import scenes/scene-3-connection.md` |
| 2 | #4 데이터 진단 (Diagnosis) | `@import scenes/scene-4-diagnosis.md` |
| 3 | #5 원인 분석 (Visual Theme Analysis) | `@import scenes/scene-5-visual-theme.md` |
| 4 | #6 A/B 테스트 및 신규 소재 생성 | `@import scenes/scene-6-ab-variants.md` |
| 5 | #7 테스트 결과 확인 (Results Reveal) | `@import scenes/scene-7-results.md` |
| 6 | #8 스케일업 & 보고서 자동 작성 | `@import scenes/scene-8-scaleup-report.md` |

스토리보드 #1/#2/#9(오프닝·상황 설정·엔딩)는 채팅 밖 실사 연출 장면이므로 이 목업의 범위
밖이다 — 렌더링하지 않는다.

## 목업 골격 (Scaffold)

각 장면 HTML을 `{SCENES}` 자리에 순서대로 삽입한다. 채팅 말풍선/썸네일 그리드 등 공통
컴포넌트 클래스는 이 골격의 CSS를 그대로 쓴다 — 장면 파일에서 재정의하지 않는다.

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>Laighthouse Demo — Shot by Shot</title>
<script>
{CHART_JS_INLINE}
</script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif;
         background: #eef1f5; color: #1e293b; padding: 24px; }
  .chat-wrap { max-width: 780px; margin: 0 auto; background: #f8fafc;
               border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden;
               box-shadow: 0 4px 24px rgba(15,23,42,.08); }
  /* ── Claude 앱 상단바 목업 ── */
  .app-bar { display:flex; align-items:center; justify-content:space-between;
             padding: 12px 20px; background:white; border-bottom:1px solid #e2e8f0; }
  .app-bar .title { font-size:14px; font-weight:700; color:#1e293b; }
  .chip { display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600;
          color:#15803d; background:#f0fdf4; border:1px solid #bbf7d0;
          border-radius:999px; padding:4px 10px; }
  .chip .dot { width:7px; height:7px; border-radius:50%; background:#22c55e; }
  .chat-body { padding: 20px; display:flex; flex-direction:column; gap:14px; }
  /* ── 말풍선 ── */
  .msg { display:flex; gap:10px; align-items:flex-start; }
  .msg.user { flex-direction:row-reverse; }
  .avatar { width:30px; height:30px; border-radius:50%; flex:none; display:flex;
            align-items:center; justify-content:center; font-size:12px; font-weight:700; }
  .avatar.user { background:#3b82f6; color:white; }
  .avatar.ai { background:#0f172a; color:white; }
  .bubble { max-width: 82%; padding: 10px 14px; border-radius: 14px; font-size: 13.5px;
            line-height: 1.6; }
  .msg.user .bubble { background:#3b82f6; color:white; border-top-right-radius:4px; }
  .msg.ai .bubble { background:white; border:1px solid #e2e8f0; border-top-left-radius:4px; }
  .sender { font-size:11px; color:#94a3b8; margin-bottom:3px; }
  .msg.user .sender { text-align:right; }
  /* ── 장면 구분선 / 타이틀 카드 ── */
  .scene-divider { display:flex; align-items:center; gap:10px; color:#94a3b8;
                   font-size:11px; font-weight:600; letter-spacing:.08em;
                   text-transform:uppercase; margin: 6px 0; }
  .scene-divider::before, .scene-divider::after { content:""; flex:1; height:1px;
                   background:#e2e8f0; }
  .title-card { background:#0f172a; color:white; text-align:center; padding:22px;
                border-radius:14px; font-size:16px; font-weight:700; letter-spacing:.04em; }
  /* ── 말풍선 내부 표 / 카드 ── */
  .bubble table { width:100%; border-collapse:collapse; font-size:12px; margin-top:10px;
                  background:white; color:#1e293b; }
  .bubble th { background:#f1f5f9; color:#475569; font-weight:600; padding:6px 10px;
               text-align:left; border-bottom:1px solid #e2e8f0; white-space:nowrap; }
  .bubble td { padding:6px 10px; border-bottom:1px solid #f1f5f9; color:#374151; }
  .table-caption { font-size:11px; font-weight:700; color:#64748b; margin-top:12px; }
  /* ── 썸네일 그리드 ── */
  .thumb-grid { display:grid; grid-template-columns:repeat(4, 1fr); gap:8px; margin-top:10px; }
  .thumb { border:1px solid #e2e8f0; border-radius:10px; overflow:hidden; background:#f8fafc; }
  .thumb img { width:100%; aspect-ratio:1/1; object-fit:cover; display:block; }
  .thumb .ph { width:100%; aspect-ratio:1/1; display:flex; align-items:center;
               justify-content:center; text-align:center; font-size:11px; font-weight:600;
               color:white; padding:8px; }
  .thumb .cap { font-size:10.5px; color:#64748b; padding:5px 7px; line-height:1.4;
                border-top:1px solid #f1f5f9; background:white; }
  .grid-label { font-size:12px; font-weight:700; margin-top:12px; }
  .grid-label.good { color:#16a34a; } .grid-label.bad { color:#dc2626; }
  /* placeholder 그라데이션 (도구로 못 가져오는 시안/무드보드 목업) */
  .ph-office { background:linear-gradient(135deg,#334155,#64748b); }
  .ph-sea    { background:linear-gradient(135deg,#0ea5e9,#38bdf8); }
  .ph-resort { background:linear-gradient(135deg,#f59e0b,#fbbf24); }
  .ph-studio { background:linear-gradient(135deg,#8b5cf6,#a78bfa); }
  .thumb.selected { outline:2px solid #3b82f6; outline-offset:1px; }
  canvas { max-width:100%; }
</style>
</head>
<body>
<div class="chat-wrap">
  <div class="app-bar">
    <span class="title">Claude</span>
    <span class="chip"><span class="dot"></span>Laighthouse — Connected via MCP</span>
  </div>
  <div class="chat-body">

  {SCENES}

  </div>
</div>
<div style="text-align:center; font-size:12px; color:#94a3b8; padding:16px 0;">
  Laighthouse Demo Mockup — Engineered by Laighthouse AI
</div>
<script>
{SECTION_SCRIPTS}
</script>
</body></html>
```

말풍선 공통 마크업 (장면 파일들이 이 형태를 그대로 쓴다):

```html
<!-- 사용자(Andy) -->
<div class="msg user">
  <div class="avatar user">{persona_name 첫 글자}</div>
  <div><div class="sender">{persona_name}</div>
    <div class="bubble">{대사}</div></div>
</div>
<!-- Laighthouse -->
<div class="msg ai">
  <div class="avatar ai">L</div>
  <div><div class="sender">Laighthouse</div>
    <div class="bubble">{대사 + 표/차트/썸네일}</div></div>
</div>
```

## 데이터 부족 시

- MCP 데이터가 필요한 블록(#4 표, #5 썸네일)만
  `<div style="color:#94a3b8;font-size:12px;">데이터 준비 중</div>` 으로 대체하고,
  대사 말풍선과 나머지 장면은 항상 전부 렌더링한다 — 장면을 임의로 생략하지 않는다.
- #5에서 creative_id가 비어 있거나 썸네일이 null인 소재는 placeholder 카드
  (`.thumb .ph`)로 대체한다 — 오류가 아니다 (장면 파일 참고).

## 완료 메시지 형식

```
{brand_name} Shot-by-Shot 데모 목업({target_month}) 생성 완료.
가장 인상적인 부분: {한 문장 하이라이트}.
— by LaightAI
📁 {저장된 html 파일 경로}
```

- `{한 문장 하이라이트}`: 렌더링된 실데이터 중 눈에 띄는 한 가지만 (예: "실제 Meta ROAS가
  3개월 새 41% 하락해 대본과 정확히 맞아떨어졌습니다"). 여러 개 나열하지 않는다.
