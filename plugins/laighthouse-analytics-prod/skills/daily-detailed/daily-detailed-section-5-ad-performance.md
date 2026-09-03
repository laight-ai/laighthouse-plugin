# Daily Section 5: 광고그룹 및 광고 성과 (D-1 vs D-0)

**report_type:** `daily-detailed` (항상 포함). 매체-캠페인-광고그룹-광고 단위로 **D-1과 D-0 딱
이틀만** 비교한다 — section-4보다 한 단계 깊은 버전이며 지표·규칙은 동일하다.

> ℹ️ 표 HTML/검색/페이지네이션 렌더링은 템플릿+빌더가, 계산·행 생성은
> `assets/dxd_table_rows.py`(`level:"ad"`)가 한다.

## MCP 도구 호출: `get_ad_performance` × len(media_list) (D-1~D0 이틀, 매체별 각각)

`media_list`(디스커버리 결과)의 **각 값마다 1회**, `filters`만 바꿔 호출한다:

```json
{ "brand_name": "<brand>", "start_date": "target_date-1일 YYYY-MM-DD", "end_date": "target_date", "time_grain": "day", "filters": {"media": ["<media_list의 값 i>"]}, "group_by": ["media", "campaign_name", "ad_group_name", "ad_name"] }
```

- **매체를 통합하지 않고 각각 부른다** — 광고(검색 매체는 키워드) 단위까지 행이 폭증하는
  고카디널리티 호출이라(마크다운 시절 실측 13만 자+), `filters` 생략 통합은 금지된 회귀다.
  각 행에 `campaign_name`/`ad_group_name`/`ad_name` 3단계가 전부 들어있다.
- `filters.media` 값은 디스커버리 응답 문자열 **그대로**(정확 일치) — 매체명을 리터럴로
  열거하거나 대소문자·표기를 바꾸지 않는다. Organic(`media: null`)은 필터로 지정할 수 없고
  광고비도 없어 이 표의 대상이 아니다(호출하지 않음).
- 매출/전환(revenue/conversion 역할 키)이 각 행의 지표로 함께 들어온다 — 별도 매출 호출·캠페인
  단위 매출 공유 규칙은 없다(귀속 세분화는 ELT 소스를 그대로 따른다).
- 호출들은 의존성이 없으므로 한 메시지에서 병렬 발사. 매체에 따라 `ad_group_name`/`ad_name`이
  비어 있을 수 있다(`-`로 표시됨, 오류 아님).

## 계산·행 생성: `assets/dxd_table_rows.py` (필수 절차 — 손계산·새 스크립트 금지)

캡처 훅 스텁으로 온 응답은 경로를 `json_files`에, 원본으로 온 응답은 `json`에 통째로
(둘을 섞어도 된다). 매체 수만큼의 응답 전부를 한 번에 넘기고(스크립트가 봉투를 이어붙인다),
section-4와 **같은** `metric_keys`/`currency`/`threshold`를 함께 넘기고, 출력은 빌더가 읽을
파일로 저장:

```bash
python3 assets/dxd_table_rows.py <<'PYEOF' > /tmp/s5_rows.json
{"level":"ad","d1_date":"2026-08-09","d0_date":"2026-08-10",
 "metric_keys":{...section-4와 동일...},"currency":"₩","threshold":10000,
 "json_files":["<매체1 경로>","<매체2 경로>", "..."]}
PYEOF
```

출력 파일 경로를 빌더 입력 JSON의 `s5.rows_file`에 넣으면 끝. (section-4와 같은 스크립트를
`level`만 바꿔 호출하는 것 — 조인·지표 컬럼(conversion 없으면 전환·CPA 생략)·변화율·`threshold`
필터·정렬·`<tr>` 생성 전부 포함. 매체 라벨은 행의 `media` 값 그대로.)

> 🚫 **응답이 크다고 느껴져도 선택지는 둘뿐이다**: (1) 원본을 가공 없이 전부 스크립트에 넘기거나
> (2) 정말 불가능하면 `s5`를 빌더 입력에서 빼서 "데이터 준비 중"으로 표시한다. **다른 섹션
> (section-4 등)에서 받은 값을 재사용하거나 비슷한 숫자를 만들어 채우는 것은, 그 숫자가 진짜
> 쿼리 결과라도 전부 금지다** — 실제 사고 두 건(출처 불명 수치 삽입, section-4 캠페인 합계로
> 바꿔치기)이 이 규칙으로 막는 대상이다. section-4와 section-5는 `group_by`가
> 달라 애초에 값을 공유할 수 있는 관계가 아니다. 이미 정상적으로 받은 광고 단위 응답이
> 있다면 그대로 쓴다 — "받았지만 크다"는 이유로 대체하는 경우는 존재하지 않는다.
