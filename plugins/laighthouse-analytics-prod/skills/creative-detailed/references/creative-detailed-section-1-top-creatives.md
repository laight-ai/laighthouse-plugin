# Creative Section 1: 최우수 소재 (ROAS 또는 클릭 / CTR, 최근 7일 기준)

**report_type:** `creative-detailed` (항상 포함). **`chosen_media` 하나만 대상**(SKILL.md 매체
선택). 기준일 포함 **최근 7일을 통째로 합산**해 소재(개별 광고) 단위 **ROAS 1·2위**(매출 없음 모드:
**클릭 1·2위**)와 **CTR 1·2위**를 카드로 보여준다 — 날짜별 비교가 아니라 7일 누적 값 기준이다.
카드 제목·각주·값 라벨은 빌더가 `metric_keys`로 모드를 판정해 바꾼다.

> ℹ️ 카드 HTML(3행 구조, 이미지→링크 fallback, 각주)은 전부 `assets/report-template.html` +
> `assets/build_report.py`가 처리하고, 랭킹은 `assets/rank_creatives.py`가 정한다 — 모델은
> 스크립트를 실행하고 썸네일 URL만 골라 빌더에 넘긴다(손으로 정렬하지 않는다).

## MCP 도구 호출: `get_ad_performance` × 1 (`time_grain:"total"`, 소재 단위, 최근 7일)

```json
{ "brand_name": "<brand>", "start_date": "기준일 6일 전 YYYY-MM-DD", "end_date": "target_date", "time_grain": "total", "group_by": ["campaign_name", "ad_group_name", "ad_name"], "filters": {"media": ["<chosen_media>"]} }
```

- 응답은 JSON 봉투(`rows` 배열)이며, 날짜별 행이 아니라 **소재(`campaign_name`+
  `ad_group_name`+`ad_name`)당 7일 전체를 서버가 이미 합산한 한 행**이다. 각 행에
  cost/impression/click(+revenue/conversion — 있을 때) 키 값과 서버 비율 지표가 함께 들어있다 —
  매출 조인이 필요 없다. **이 응답은 section-5가 그대로 재사용한다**(다시 호출하지 않는다).
  section-3의 상위 5개 소재 선정도 이 응답으로 한다. 소재가 수백 개면 캡처 훅 스텁으로 오는 것이
  정상이다.
- ⚠️ **`filters`는 반드시 명시한다 — 생략 금지**(불필요한 매체 행으로 응답만 커진다). 값은
  디스커버리 응답의 `media` 문자열 그대로(정확 일치). 이 호출은 section-3의 day 1회와 함께
  한 메시지에 병렬 발사한다.
- `rows`가 비어있으면 이 매체에 소재 단위 데이터가 없다 — 사용자에게 알리고 다른 매체를
  고르게 한다(SKILL.md 4단계).

## 랭킹: `assets/rank_creatives.py` (필수 — 손정렬·즉석 스크립트 금지)

응답이 캡처 스텁이면 경로를 `json_files`에, 원본이 그대로 오면 `json`에 문자열 통째로 넣는다
(스텁 파일을 Read로 열지 않는다). 결과는 `out` 파일에 저장되고 stdout에 요약이 나온다:

```bash
python3 assets/rank_creatives.py <<'PYEOF'
{"json_files": ["<total 응답 스텁 경로>"],
 "metric_keys": <discover.py 출력의 metric_keys 그대로>,
 "chosen_media": "<chosen_media>",
 "s5": true,
 "out": "/tmp/creative_rank.json"}
PYEOF
```

스크립트가 구현한 규칙(참고용 스펙 — 모델이 다시 계산하지 않는다):

- **최소 표본 기준**: 최우수 소재 랭킹(왼쪽·오른쪽 카드 모두)에는 **노출 1,000회 이상 그리고
  광고비가 `chosen_media` 7일 총광고비(total 응답 전체 행 광고비 합)의 1% 이상**인 소재만
  들어간다 — 노출 2회·클릭 1회짜리 소재가 CTR 50%로 1위가 되는 왜곡(실측)을 막는다. 기준을
  충족하는 소재가 하나도 없으면 전체 소재로 폴백한다. 기준과 적용 결과는 빌더가 section-1 하단
  각주로 자동 표기한다.
- 왼쪽 카드: **매출 있음** ROAS = 매출÷광고비×100 내림차순 1·2위(광고비 0 제외), **매출 없음**
  클릭 수(7일 합) 내림차순 1·2위. 오른쪽 카드(공통): CTR = 클릭÷노출×100 내림차순 1·2위(노출 0
  제외). 두 랭킹은 독립, 동점은 광고비 큰 소재 우선. 매출 `null`은 0으로 계산한다.
- **표시 이름**: `ad_name`이 비었거나 `"-"`이면 `"<ad_group_name> (소재명 없음)"`. 같은 카드의
  1·2위가 같은 표시 이름이면 `" (<ad_group_name>)"`(그래도 같으면 `" (<campaign_name>)"`)을
  덧붙인다.
- 상위 5개(section-3/4)는 광고비 내림차순 — 최소 표본 기준을 적용하지 않는다.
- stdout 요약: `s1`(카드 항목)·`lookups`(썸네일 조회 대상)·`top5_names`·`eligibility`·
  `media_totals`(매체 7일 합과 CTR/ROAS 또는 CPC)·`top_by_cost`(광고비 상위 10개 소재 요약 —
  Executive Summary 근거). `"s5": true`면 출력 파일에 section-5 rows 전체(`s5_rows`)도 들어간다
  (stdout에는 개수만).

## MCP 도구 호출: `get_ad_creative_info` (`lookups`의 소재만, `source` 없이)

```json
{ "brand_name": "<brand>", "name_query": "<lookups[i].ad_name>" }
```

- `lookups`(최대 4개, 유니크 — 소재명 없는 소재는 애초에 빠져 있다)마다 1회, 한 배치로 동시
  발사한다. ⚠️ **`source`를 넣지 않는다** — ELT는 닫힌 목록 외의 값을 400 에러로 거절하고,
  마트 `source` 차원 값과도 맞지 않는다(SKILL.md 매체 선택 4).
- **썸네일 매칭 규칙**: 응답 `{"source": "elt", "items": [...]}`(`name_query`는 서버에서 대소문자
  무시 부분 일치라 여러 개가 올 수 있다)에서 `ad_name`이 lookup의 `ad_name`과 **정확히
  일치**하고, 항목에 `adgroup_name`/`campaign_name`이 있으면 그것도 lookup의
  `ad_group_name`/`campaign_name`과 정확히 일치하는 항목을 고른다. 그런 항목 중 `image_url`이
  있는 첫 번째 것의 `image_url`을 쓴다.
- 에러 응답·`items: []`·일치 항목 없음·`image_url` 없음 → 그 lookup은 `null`(오류로 취급하지 않고
  재시도하지 않는다). ⚠️ 이미지 URL은 IP 화이트리스트 뒤에 있어 허용되지 않은 네트워크에서는
  안 뜰 수 있다 — 이미지 로드 실패 폴백은 빌더/템플릿이 처리한다.

## 빌더 `s1` 필드

```json
"rank_file": "/tmp/creative_rank.json",
"thumbnails": {"L1": "https://...", "L2": null},
"currency": "<discover.py 출력의 currency>",
"s1": {}
```

- `s1`은 **빈 객체**로 둔다 — 빌더가 `rank_file`의 `s1`을 쓰고, `thumbnails`(lookup id →
  `image_url`)로 이미지를 채운다. 값 포맷(ROAS 소수 1자리, CTR 소수 2자리, 클릭 콤마 정수),
  모드별 제목·각주, 최소 표본 기준 각주는 빌더가 한다.
- 랭킹 결과가 양쪽 다 비어 있으면(유효 소재 없음) 빌더가 "데이터 준비 중" 카드로 렌더링한다 —
  임의로 채우지 않는다.
