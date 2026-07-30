# scene-7: 테스트 결과 확인 — Results Reveal (스토리보드 #7, 1:34–1:53)

**"다음 날 아침" 타이틀 카드**가 등장한 뒤, Laighthouse 말풍선 안에 **성과 비교
막대그래프**가 나타나는 장면.

MCP 호출 없음 — A/B 테스트 결과는 데모용 **고정 목업 수치**다. 아래 값을 그대로 쓴다
(임의 변경 금지 — 매 실행마다 같은 목업이 나와야 한다):

| 그룹 | (a) 오피스 | (b) 바다 | (c) 오피스 | (d) 리조트 |
|---|---|---|---|---|
| 남성 18-34 | 4.8 | 2.1 | 4.2 | 2.4 |
| 남성 35-54 | 5.1 | 1.9 | 4.0 | 2.2 |
| 여성 18-34 | 4.6 | 2.3 | 4.4 | 2.8 |
| 여성 35-54 | 5.3 | 2.0 | 4.5 | 2.5 |

단위: CTR(%). 모든 그룹에서 (a)가 1위 — 대본("모든 연령대와 성별 그룹에서 압도적 1위")과
일치하도록 설계된 수치다.

## 대사 (그대로)

- **Laighthouse**: "테스트 결과가 나왔습니다. 모든 연령대와 성별 그룹에서 **Variant (a) -
  단정한 오피스 룩**이 압도적 1위를 기록했습니다."

## HTML + 차트 스크립트

```html
<div class="scene-divider">Scene 7 · 테스트 결과 확인</div>
<div class="title-card">다음 날 아침</div>
<div class="msg ai">
  <div class="avatar ai">L</div>
  <div><div class="sender">Laighthouse</div>
    <div class="bubble">
      테스트 결과가 나왔습니다. 모든 연령대와 성별 그룹에서 <b>Variant (a) - 단정한
      오피스 룩</b>이 압도적 1위를 기록했습니다.
      <div style="margin-top:10px; background:white; border:1px solid #f1f5f9;
                  border-radius:10px; padding:10px;">
        <canvas id="abTestChart" height="220"></canvas>
      </div>
    </div></div>
</div>
```

`{SECTION_SCRIPTS}`에 삽입할 차트 초기화 (grouped bar, 그룹=연령·성별, 시리즈=Variant):

```js
new Chart(document.getElementById('abTestChart'), {
  type: 'bar',
  data: {
    labels: ['남성 18-34','남성 35-54','여성 18-34','여성 35-54'],
    datasets: [
      { label:'(a) 단정한 오피스', data:[4.8,5.1,4.6,5.3], backgroundColor:'#3b82f6' },
      { label:'(b) 바다',          data:[2.1,1.9,2.3,2.0], backgroundColor:'#93c5fd' },
      { label:'(c) 단정한 오피스', data:[4.2,4.0,4.4,4.5], backgroundColor:'#60a5fa' },
      { label:'(d) 리조트',        data:[2.4,2.2,2.8,2.5], backgroundColor:'#bfdbfe' }
    ]
  },
  options: {
    responsive: true,
    plugins: { legend: { position:'bottom', labels:{ font:{ size:11 } } },
               title: { display:true, text:'A/B 테스트 CTR (%) — 그룹별', font:{ size:12 } } },
    scales: { y: { beginAtZero:true, ticks:{ callback:v=>v+'%' } } }
  }
});
```
