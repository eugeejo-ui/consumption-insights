# Phase 3 · Task 3: 카드 데이터와 게시문

| 항목 | 내용 |
|---|---|
| 상태 | **계획 승인** (2026-09-15, 확인 사항 6건 모두 권고안). **완료** (2026-09-15). 테스트 79개. 코드 커밋 `06ace44` |
| 상위 계획 | `docs/plans/phase3-linkedin-cardnews.md` Task 3, 결정 D11·D15·D16·D17·D18·D19·D20 |
| 문안 정본 | `docs/scripts/cards-script.md`, `docs/scripts/linkedin-post-script.md` |
| 담당 | C (사용자 확인 2회: 계획 승인, Step 0 보완 문안 승인) |

## 목표

E1인 날의 `events.json`을 **카드 장별 데이터**와 **LinkedIn 게시문 텍스트**로 바꾼다. 디자인(HTML)과 굽기는 Task 4의 일이다. 이 Task는 **무엇을 싣는가**를 코드로 고정한다.

코드로 강제하는 검사는 네 가지다. 하나라도 어긋나면 생성을 중단한다.

| 검사 | 근거 | 방식 |
|---|---|---|
| 누락 검사 | 규칙 18, 디자인 계획 4-4 | 카드에 실린 단가·월 사용료·순위 항목 수 = `events.json` 항목 수 |
| 숫자 검사 | 규칙 16, Phase 2 Task 2 | 카드와 게시문의 모든 숫자가 `events.json`에 있다(`render_post.check_numbers` 재사용) |
| 글자 수 검사 | 카드 스크립트 4절 | 역할별 상한을 넘으면 중단한다. 잘라내지 않는다 |
| 게시문 길이 검사 | 규칙 18 | 3,000자를 넘으면 중단한다. 항목을 잘라서 맞추지 않는다 |

## 착수 전 확인 사항 (결정 필요)

확정 스크립트와 기존 코드를 대조하는 과정에서, 스크립트에 정의되지 않은 값 5건과 구성 결정 1건을 확인했다. 규칙 16에 따라 **문안을 확정하지 않은 채 렌더러를 구현하지 않는다.** 1~5는 Step 0에서 스크립트에 보완하고 승인을 받는다.

| # | 발견 | 영향 | 권고 |
|---|---|---|---|
| 1 | `{서비스}` 라벨은 `컴퓨트` 예시 하나뿐이다. 실제 서비스는 `compute`·`storage`·`scan` 세 가지다 | 스토리지나 BigQuery 스캔 단가가 바뀐 날 카드 문구가 정해져 있지 않다 | 라벨표를 추가한다. `컴퓨트` / `스토리지` / `주문형 쿼리`. 앞의 둘은 대시보드와 같은 용어이고, 셋째는 BigQuery 가격 페이지의 한국어 표기 `쿼리(주문형)`를 따른다 |
| 2 | 단가가 새로 생기거나 없어진 항목(SKU 교체)은 `{전}` 또는 `{후}`가 비고 변화율이 없다 | 규칙 18상 이 항목도 실어야 하나 표기가 없다 | `없음 → $0.4` 형식으로 적고 변화율 괄호를 생략한다. 검토 보고서·글 초안과 같은 표기다 |
| 3 | 월 사용료 변동 내역 리드의 `±1%`가 고정 문안으로 적혀 있다. 실제 값은 `config/thresholds.yaml`의 E1 기준이다 | 기준을 바꾸면 카드가 틀린 기준을 적는다 | `±{기준}%` 자리표시자로 바꾼다. 문장은 그대로다 |
| 4 | 게시문 `월 비용 영향이 가장 큰 조합은 {시나리오} · {리전}입니다.` | (a) 카드 차트 장에서 불분명하다고 지적받은 `영향` 표현이 남아 있다. (b) 월 비용 변동 없이 순위만 바뀐 날에는 가리킬 조합이 없다 | `월 비용 변동 폭이 가장 큰 조합은 …`으로 카드 리드와 맞추고, 월 비용 변동이 있는 날만 출력한다. `월 비용` 용어는 D17에 따라 다른 대화에서 교체하므로 그대로 둔다 |
| 5 | 단가 표시 자릿수가 정해져 있지 않다. 스크립트 예시는 `$0.394`(소수 셋째 자리)다 | 반올림하면 작은 인상이 가려진다. 예: ADLS `$0.0208 → $0.0209`가 `$0.021 → $0.021`로 보인다 | 공시값을 그대로 적고 끝의 0만 지운다. 검토 보고서와 같은 방식이다. 스크립트 예시를 실제 표기(`$0.39375`)로 고친다 |
| 6 | **마무리 안내 장.** 사용자가 대시보드 안내로 끝맺는 장을 추가할 의사를 밝혔으나(2026-09-14) 스크립트에 없다 | 장 구성, 최소 장수, 마지막 장 표시(`끝`), 이 Task 테스트의 장 순서 단언이 모두 달라진다 | **A안(권고):** Step 0에서 마무리 장 문안까지 확정하고 이 Task에 포함한다. **B안:** 현재 구성으로 진행하고 나중에 별도 개정으로 넣는다. B안은 이 Task의 테스트를 다시 고쳐야 한다 |

A안을 택하면 Step 0에서 함께 고치는 문서가 늘어난다. 디자인 계획 1-1(`10-closing` 사용), 3-2(구성표), 4-1·4-2(장수), 코드 계획 D11(최소 장수), `CLAUDE.md` 결정 로그(새 결정)다. D16(`가정과 산출 근거` 장을 두지 않는다)은 유지된다. 마무리 장은 고지가 아니라 안내다.

## 승인 결과 (2026-09-15)

사용자가 "권고안대로 진행해"라고 지시했다. 확인 사항 6건을 모두 권고안으로 확정했다. 6번은 **A안**이다(마무리 안내 장을 이 Task에 포함, D20).

## Step 0 실행 결과 (2026-09-15)

| 대상 | 반영 |
|---|---|
| `docs/scripts/cards-script.md` | 0절 자리표시자(`{기준}` 추가, `{대표 시나리오}` 정의 보강, 예시 `$0.39375`), 0-1절 서비스 라벨, 0-2절 금액 표기, 1-1절 마무리 안내 장, 단가 추가·삭제 표기, 월 사용료 변동 내역 리드 `±{기준}%`, 소개 카드 5장 구성과 4장 각주, 4절 상한표·4-1절 장 표 |
| `docs/scripts/linkedin-post-script.md` | 변동 폭 줄(조건부), 순위 줄 `순서가`, 대표 조합 정의 |
| `docs/plans/phase3-card-design.md` | 1-1 `10-closing` 사용, 3-1 소개 5장, 3-2 정기 5장 이상, 4-1 장수 표, 4-2 예시(5·6·9장) |
| `docs/plans/phase3-linkedin-cardnews.md` | D20 추가, D11 갱신 |
| `docs/phases/phase-3-linkedin.md`, `CLAUDE.md` | 카드 구성·장수, D20, 진행 기록 |

**`/humanize-korean` 점검 [확인]:** run `2026-09-15-001`, light 경로(risk_band low, score 0). 변경률 0.0%, 터치율 0/21, 게이트 exit 0 수렴. 스킬이 보고한 제안 2건을 반영했고, 반영본도 게이트를 다시 통과했다(변경률 0.5%, 터치율 2/21).

| 위치 | 반영 전 | 반영 후 |
|---|---|---|
| 마무리 안내 장 리드 | 시나리오별 월 사용료와 서울 프리미엄, 가정과 산출 근거를 공개합니다. | 시나리오별 월 사용료, 서울 프리미엄, 가정과 산출 근거를 공개합니다. |
| 게시문 순위 줄 | 월 비용이 낮은 순서도 바뀌었습니다. | 월 비용이 낮은 순서가 바뀌었습니다. |

### 계획과 달라진 점

| 계획 | 실제 | 이유 |
|---|---|---|
| 확인 사항 5: 공시값을 그대로 적고 **끝의 0만 지운다** | 공시값을 그대로 적되 **소수 둘째 자리까지는 0을 채운다**(`$0.70`, `$23.00`) | 끝의 0을 모두 지우면 `$0.7`, `$23`처럼 금액 표기 관행과 어긋난다. 반올림하지 않는다는 핵심은 같다. 보완 문안 승인 때 함께 확인받는다 |
| `render_post._price`를 `format_price`로 공개해 재사용 | `card_data.price_label`을 새로 두고 `render_post.py`는 건드리지 않는다 | 위 표기 변경으로 카드·게시문 표기가 검토 보고서 표기와 달라졌다. 검토 보고서의 표기는 그대로 둔다 |
| 게시문 순위 줄 문안 유지 | `순서도` → `순서가` | 변동 폭 줄에 조건을 붙이면서 순위 줄이 단독으로 나오는 날이 생겼다(스킬 보고 제안) |
| 소개 카드 4장 | 소개 카드도 5장(마무리 안내 포함). 4장 각주에서 `산출 근거는 대시보드에 있습니다`를 뺐다 | D20은 모든 카드뉴스에 적용한다. 다음 장이 같은 내용을 알리므로 중복을 없앴다. 차트 장 각주(D19)와 같은 처리다. 구현은 Task 8이다 |
| 테스트 2·3·4의 장수 4·6·7장 | 5·7·8장 | 마무리 안내 장이 모든 카드뉴스의 마지막에 붙는다 |

## 건드리는 파일

| 파일 | 동작 |
|---|---|
| `docs/scripts/cards-script.md` | Step 0 보완(확인 사항 1·2·3·5, A안이면 6) |
| `docs/scripts/linkedin-post-script.md` | Step 0 보완(확인 사항 4) |
| `publish/card_data.py` | 신규. 이벤트 → 카드 장별 데이터, 누락·글자 수 검사 |
| `publish/render_linkedin.py` | 신규. 정기 게시문 렌더러, 숫자·길이 검사 |
| `templates/post_linkedin.md.j2` | 신규. 확정 게시문 문안 |
| `tests/conftest.py` | 수정. 변동 이벤트를 만드는 픽스처 `make_events` 추가(Task 4가 재사용) |
| `tests/test_card_data.py` | 신규. 테스트 13개 |
| `tests/test_render_linkedin.py` | 신규. 테스트 4개 |
| `docs/tasks/phase3/task-3-card-data-and-post.md` | 이 파일. 실행 후 결과를 덧붙인다 |
| `docs/plans/phase3-linkedin-cardnews.md`, `docs/phases/phase-3-linkedin.md`, `CLAUDE.md` | 규칙 7에 따라 갱신 |

**건드리지 않는 것:** `pipeline.py`(Task 5), 카드 HTML 템플릿(Task 4), 워크플로(Task 6), 소개 카드와 소개 게시문(Task 8).

## 인터페이스

```python
# publish/card_data.py
PER_PAGE = {"price": 5, "cost": 6, "rank": 2}          # 디자인 계획 4-1
LIMITS = {"cover_title": 20, "closing_title": 20,       # 카드 스크립트 4절: 한 줄 상한 × 줄 수 상한
          "title": 28, "lead": 90,
          "item": 32, "note": 40}                       # 항목·각주는 한 줄씩 나눠 싣는다
SERVICE_LABELS = {"compute": "컴퓨트", "storage": "스토리지", "scan": "주문형 쿼리"}   # Step 0 확정값으로 채운다
REGION_LABELS = {"us": "미국 리전", "seoul": "서울 리전"}

price_label(value: float | None) -> str                 # 스크립트 0-2절. 반올림하지 않는다. $0.70, $0.39375, 없음

cover_title(events: dict) -> list[dict]
    # 스크립트 2절 1장의 세 조건. [{"text": "월 사용료 ", "accent": False}, {"text": "순위 변동", "accent": True}]

price_change_cards(events: dict, rows: list[CostRow], prev_rows: list[CostRow], workloads: dict) -> list[dict]
    # events["significant"]가 거짓이면 ValueError. 카드는 E1인 날에만 만든다(상위 계획 Task 5)
    # events를 제자리에서 보강한다:
    #   events["display"] = {"price_change_count": int,
    #                        "chart": {"scenario": "W1", "us": {플랫폼: 달러 정수}, "seoul": {...}}}
    # 마지막에 check_complete, check_lengths, 숫자 검사를 차례로 부른다

check_complete(cards: list[dict], events: dict) -> None      # 어긋나면 ValueError("누락 …")
check_lengths(cards: list[dict]) -> None                     # 넘치면 ValueError("글자 수 …")
card_text(cards: list[dict]) -> str                          # 숫자 검사용. 카드에 찍히는 문자열을 모은다

# publish/render_linkedin.py
DASHBOARD_URL = "https://eugeejo-ui.github.io/consumption-insights/"
MAX_CHARS = 3000
render_linkedin(events: dict, workloads: dict) -> str         # 숫자 검사, 3,000자 초과 시 ValueError
```

**장 데이터 모양**

```python
{"kind": "cover",   "title": [...], "subtitle": "2026-09-13 · 단가 1건",
                    "lead": "직전 승인 가격(2026-09-11) 대비 변동 사항입니다."}
{"kind": "bullets", "group": "price" | "cost", "page": "(1/2)" | None, "title": [...], "lead": str,
                    "items": [{"strong": "Redshift 컴퓨트 · 미국 리전", "rest": "$0.375 → $0.40 (+6.7%)"}]}
{"kind": "chart",   "title": [...], "lead": str, "scenario": "W1",
                    "series": {"us": {"snowflake": 1550, ...}, "seoul": {...}}, "notes": [str, str]}
{"kind": "banners", "page": "(1/2)" | None, "title": [...], "lead": str,
                    "banners": [{"label": "소규모 BI 대시보드 · 미국 리전",
                                 "before": "Redshift › BigQuery › Snowflake › Databricks", "after": "…"}]}
{"kind": "closing", "title": [...], "lead": str, "url": "eugeejo-ui.github.io/consumption-insights"}   # 항상 마지막 장(D20)
```

상단 바, 하단 알약, 범례(`미국 리전` `서울 리전`), 배너의 `이전`·`현재` 같은 **틀 문구는 템플릿(Task 4)에 둔다.** 데이터에는 날마다 달라지는 문장과 각주만 담는다.

**설계 판단 세 가지**

1. **대표 시나리오는 전체 조합에서 고른다.** 스크립트 정의는 `cost_changes` 중 변화율 절댓값이 가장 큰 항목이다. 그런데 순위만 바뀌고 월 사용료 변동이 1% 미만인 날에는 `cost_changes`가 비어 대표가 없다. 그래서 `rows`와 `prev_rows`의 전체 조합에서 변화율(소수 첫째 자리 반올림)이 가장 큰 조합을 고른다. 동률이면 계산 순서(W1→W3, 플랫폼 순, 미국 리전 먼저)의 첫 항목이다. `cost_changes`가 비어 있지 않은 날에는 스크립트 정의와 결과가 같다. 이 보강을 Step 0에서 스크립트 0절 정의에 적는다.
2. **쪽 표시 `(1/2)`는 숫자 검사에서 제외한다.** 쪽 표시는 데이터가 아니라 장 순번이다. 장수가 맞는지는 누락 검사와 테스트가 확인한다. 이 숫자까지 `events.json`에 넣으면 검사의 의미 없이 파일만 커진다.
3. **게시문은 카드에 의존하지 않는다.** 확정 게시문은 `events`의 단가 변동을 직접 나열한다. 카드 생성이 실패해도 게시문은 만들어진다. 단가 줄은 카드와 같은 함수로 만들어 두 곳의 표기가 어긋나지 않게 한다.

## 단계

- [x] **Step 0 스크립트 보완 (규칙 16)** — 2026-09-15 승인
  - 확인 사항 1·2·3·5와 설계 판단 1을 `cards-script.md`에, 확인 사항 4를 `linkedin-post-script.md`에 반영한다. A안이면 마무리 장 문안과 관련 문서도 함께 고친다
  - 새로 쓰거나 바꾼 문안만 모아 `/humanize-korean`으로 점검하고, 결과를 두 스크립트의 점검 기록에 남긴다
  - **사용자 승인.** 승인 전에는 Step 1로 넘어가지 않는다
- [x] **Step 1** 테스트 17개를 먼저 쓰고 실패를 확인한다(`ModuleNotFoundError`)
- [x] **Step 2** `publish/card_data.py`를 구현한다
  - 표지 → 단가 변동 내역(5줄마다 1장) → 플랫폼별 월 사용료(1장) → 월 사용료 변동 내역(6줄마다 1장, 없으면 0장) → 순위 변동(배너 2개마다 1장, 없으면 0장) → 마무리 안내(1장, D20)
  - 금액은 `round()`로 달러 정수를 한 번 만들어 `events["display"]["chart"]`와 카드에 같은 값을 쓴다
- [x] **Step 3** `templates/post_linkedin.md.j2`와 `publish/render_linkedin.py`를 구현한다. 단가 표기는 `card_data.price_label`을 함께 쓴다
- [x] **Step 4** 전체 테스트를 돌린다 → 79개 통과
- [x] **Step 5 실제 스냅샷 확인**
  - 2026-09-11 승인 스냅샷에 시뮬레이션 변동(Redshift 미국 리전 컴퓨트 +5%)을 넣어 카드 데이터와 게시문을 만든다. 출력은 스크래치 폴더에만 둔다
  - 차트 금액이 Task 2 시험 카드의 값과 같은지 대조한다(미국 리전 1,550·2,056·933·1,693, 서울 리전 2,032·2,708·1,032·2,167)
  - 장수(5장), 게시문 글자 수, 생략 문구 0건을 확인한다
  - **게시문 전문을 사용자에게 보고한다**
- [x] **Step 6** 커밋 전 개인정보 검사(이메일, 로컬 사용자 경로, 개인 프로젝트 ID) → 커밋 `feat: build card data and the LinkedIn post text` → `git ls-files`로 새 파일 추적 확인
- [x] **Step 7** 이 파일에 실행 결과를 덧붙이고, 코드 계획 Task 3 절·진행계획·`CLAUDE.md`를 갱신한다. **보고하고 멈춘다**(규칙 10)

## 테스트 목록

픽스처 `make_events(changed)`는 테스트 가격(`conftest.PRICES`)의 일부 단가를 바꿔 `(events, rows, prev_rows)`를 돌려준다. 아래 기대값은 이 픽스처로 미리 계산해 확인했다 [확인 2026-09-14].

**`tests/test_card_data.py` (13개)**

| # | 이름 | 확인하는 것 |
|---|---|---|
| 1 | `test_cover_title_follows_the_three_conditions` | 순위 변동 → `월 사용료 순위 변동`, 월 사용료만 → `월 사용료 변동`, 단가만 → `단가 변동`. 강조 덩어리가 스크립트의 굵은 부분과 같다 |
| 2 | `test_five_cards_on_a_typical_day` | Redshift 미국 리전 컴퓨트 0.40 → 단가 1건·월 사용료 3건·순위 0건 → `cover, bullets(price), chart, bullets(cost), closing` 5장, `price_change_count == 1`. 마무리 장의 제목·리드가 스크립트 1-1절과 글자 단위로 같다 |
| 3 | `test_rank_banners_are_split_two_per_card` | 같은 단가 0.80 → 순위 변동 3건 → 순위 장 2장(`(1/2)` 배너 2개, `(2/2)` 배너 1개), 전체 7장이고 마지막은 마무리 장이다 |
| 4 | `test_every_item_is_carried_across_pages` | 단가 7건·월 사용료 12건·순위 2건 → 단가 2장(5+2)·월 사용료 2장(6+6)·순위 1장, 전체 8장. 쪽 표시가 맞고 `외 ` 문구가 없다 |
| 5 | `test_missing_item_stops_generation` | 항목 하나를 빼면 `check_complete`가 `누락`으로 중단한다 |
| 6 | `test_chart_card_always_shows_both_regions` | 변동이 미국 리전에만 있어도 `series`에 두 리전이 4개씩 있고, `events["display"]["chart"]`와 같다 |
| 7 | `test_chart_names_the_scenario_with_the_largest_change` | 0.40 → 리드가 `월 사용료 변동 폭이 가장 큰 시나리오는 소규모 BI 대시보드입니다.`와 글자 단위로 같다 |
| 8 | `test_no_cost_card_when_only_the_ranking_changes` | `cost_changes`를 비운 순위 변동 이벤트 → 월 사용료 변동 내역 장이 없고, 대표 시나리오는 전체 조합에서 정해진다 |
| 9 | `test_labels_follow_the_fixed_terms` | `Redshift 컴퓨트 · 미국 리전` 표기, 제목에 `월 사용료`, 카드 전체에 `월 비용`이 없다(D17) |
| 10 | `test_prices_follow_the_script_format` | 이전 단가가 없는 항목 → `없음 → $0.40`, 변화율 괄호 없음. 반올림하지 않는다(`$0.39375`, `$0.0208`) |
| 11 | `test_every_number_on_the_cards_is_in_events` | 정상 카드는 통과한다. 시나리오 이름에 `events.json`에 없는 숫자를 넣으면 중단한다 |
| 12 | `test_text_over_the_length_limit_stops_generation` | 상한을 넘는 제목·리드·항목이 있으면 `글자 수`로 중단한다 |
| 13 | `test_events_without_a_significant_change_are_rejected` | `significant`가 거짓이면 카드를 만들지 않는다 |

**`tests/test_render_linkedin.py` (4개)**

| # | 이름 | 확인하는 것 |
|---|---|---|
| 14 | `test_post_lists_every_price_change_and_the_dashboard_link` | 단가 7건이 한 줄씩 모두 있고, 대시보드 주소와 고정 해시태그가 있다 |
| 15 | `test_conditional_lines_follow_the_events` | 순위 줄은 순위가 바뀐 날만, 변동 폭 줄은 월 비용 변동이 있는 날만 나온다 |
| 16 | `test_post_over_3000_chars_stops` | 단가 변동이 많아 3,000자를 넘으면 `ValueError`로 중단한다. 항목을 자르지 않는다 |
| 17 | `test_a_number_not_in_events_is_rejected` | 시나리오 이름에 `events.json`에 없는 숫자를 넣으면 중단한다 |

**합계:** 62 → **79**

## 확인 방법 (증거)

| 확인 항목 | 방법 |
|---|---|
| 테스트 | `.venv\Scripts\python.exe -m pytest -q` 결과 개수 |
| 실제 금액 | Step 5 출력의 차트 금액을 Task 2 시험 카드(실제 승인 스냅샷) 값과 대조 |
| 문안 일치 | 테스트 7·9와 Step 5 출력을 스크립트 문장과 글자 단위로 대조 |
| 생략 금지 | 테스트 4, Step 5 출력에서 `외 ` 검색 0건 |
| 게시문 | Step 5 게시문 전문과 글자 수를 보고서에 싣는다 |

## 위험

| 위험 | 대응 |
|---|---|
| 코드의 문구가 스크립트와 조금씩 어긋난다 | 테스트가 스크립트 문장을 글자 단위로 단언한다. 스크립트를 파싱해 코드에 넣는 자동화는 하지 않는다(과하다) |
| 다른 대화의 `월 비용 → 월 사용료` 교체(D17)와 같은 파일을 동시에 고친다 | 커밋 전에 `git status`와 `git diff`로 다른 변경이 섞이지 않았는지 확인한다. 게시문 문구는 템플릿 한 곳에만 두어 교체 범위를 좁힌다 |
| 숫자 검사가 우연히 일치한 숫자를 통과시킨다(예: 날짜 속 `13`) | 기존 검사의 한계다. 이 Task는 항목 문자열을 테스트로 직접 단언해 보완한다 |
| 시나리오 이름에 숫자가 들어가면 생성이 멈춘다 | 현재 이름 3개에는 숫자가 없다. 이름을 바꿀 때 주의할 점으로 기록한다 |
| 순위 배너의 서열 문자열이 44자다(`Redshift › BigQuery › Snowflake › Databricks`) | 스크립트 4절 상한표에 배너 항목이 없다. Task 4에서 배너 글자 크기와 줄 수를 정하고 굽기로 확인한다 |
| 글자 수 상한은 글자 개수 기준이라 실제 폭과 다를 수 있다 | 최종 방어는 Task 4의 겹침 검사(CI 산출물 포함)다 |

## 상위 코드 계획과 달라지는 점

| 코드 계획 | 이 계획 | 이유 |
|---|---|---|
| `price_change_cards(events, rows, workloads)` | `prev_rows` 인자 추가 | 순위만 바뀐 날에도 대표 시나리오를 정의하기 위해서다(설계 판단 1) |
| `render_linkedin(events, cards)` | `render_linkedin(events, workloads)` | 확정 게시문은 카드가 아니라 `events`의 단가 변동을 나열한다. 카드 실패가 게시문을 막지 않는다 |
| 0.80 테스트: 5장, 배너 2개(리전별로 묶음) | 6장, 배너 3개를 2장에 나눔 | 확정 스크립트는 조합마다 배너 1개다. 실제 계산 결과 순위 변동은 3건이다 [확인] |
| 10장 초과 경고를 Task 3에서 남긴다 | Task 6으로 옮긴다 | 경고는 검토 PR 본문의 문장이라 규칙 16 대상이다. PR 본문 문안과 함께 쓴다 |
| 게시문 템플릿 초안 | 확정 스크립트 기준 | 초안은 스크립트 확정 전에 쓴 것이다 |
| 소개 게시문 언급 없음 | Task 8에서 소개 카드와 함께 | 소개 카드와 한 묶음으로 확인하는 편이 낫다 |
| 글자 수 검사 없음 | `check_lengths` 추가 | 스크립트 4절이 "상한을 넘으면 생성 시점에 중단한다"고 정했다 |
| 테스트 +11 → 73 | +17 → 79 | 위 항목(보완 표기, 글자 수 검사, 순위 분할, 순위만 바뀐 날)을 검증한다 |

## 완료 기준

- Step 0 보완 문안이 `/humanize-korean` 점검을 거쳐 승인됐다.
- 테스트 17개를 추가해 전체 79개가 통과한다.
- 누락·숫자·글자 수·게시문 길이 검사가 코드로 강제된다.
- 실제 승인 스냅샷 시뮬레이션의 차트 금액이 Task 2 시험 카드와 같다.
- 이 파일에 실행 결과가 덧붙고, 관련 문서가 갱신되고, 커밋됐다.

---

## 실행 결과 (2026-09-15)

**완료.** 테스트 17개를 추가해 전체 79개가 통과한다. 코드 커밋 `06ace44`.

### 실제로 한 일

| Step | 결과 |
|---|---|
| 0 | 스크립트 보완, `/humanize-korean` 점검(run `2026-09-15-001`, 게이트 수렴), 사용자 승인(단가 표기 조정 포함). 문서 커밋 `17b889b` |
| 1 | 테스트 17개 작성. 새 모듈이 없어 `ModuleNotFoundError`로 실패하는 것을 확인했다 |
| 2 | `publish/card_data.py` 구현. 장 구성, 쪽 나눔, 대표 시나리오, `events["display"]` 기록, 누락·글자 수·숫자 검사 |
| 3 | `templates/post_linkedin.md.j2`, `publish/render_linkedin.py` 구현. 단가 줄은 카드와 같은 `price_item`으로 만든다 |
| 4 | 새 테스트 17개 통과, 전체 **79개 통과** [확인] |
| 5 | 실제 승인 스냅샷 확인(아래) |
| 6 | 개인정보 검사 0건, LinkedIn 호출 코드 0건. 커밋 후 `git ls-files`로 새 파일 5개 추적 확인 |

### 바뀐 파일

| 파일 | 내용 |
|---|---|
| `publish/card_data.py` | 신규 |
| `publish/render_linkedin.py` | 신규 |
| `templates/post_linkedin.md.j2` | 신규. 확정 게시문 문안 |
| `tests/conftest.py` | 픽스처 `make_events` 추가 |
| `tests/test_card_data.py` | 신규. 13개 |
| `tests/test_render_linkedin.py` | 신규. 4개 |
| `docs/scripts/cards-script.md`, `docs/scripts/linkedin-post-script.md` | 보완안 확정 표기 |

### 실측값 [확인]

2026-09-11 승인 스냅샷에 시뮬레이션 변동(Redshift 미국 리전 컴퓨트 +5%, `$0.375 → $0.39375`)을 넣어 만들었다. 출력은 스크래치 폴더에만 두었다.

| 확인 항목 | 결과 |
|---|---|
| 장 구성 | 5장: 표지 → 단가 변동 내역 → 플랫폼별 월 사용료 → 월 사용료 변동 내역 → 마무리 안내 |
| 표지 제목 | 월 사용료 **변동** (순위 변동 없음) |
| 대표 시나리오 | W1 소규모 BI 대시보드(+3.7%) |
| 차트 금액 | 미국 리전 $1,550·$2,056·$933·$1,693, 서울 리전 $2,032·$2,708·$1,032·$2,167. **Task 2 시험 카드와 같다** |
| 단가 줄 | `Redshift 컴퓨트 · 미국 리전` / `$0.375 → $0.39375 (+5.0%)` (반올림하지 않음) |
| 월 사용료 변동 내역 | 3건 모두 실림(+3.7%, +3.0%, +1.7%) |
| 생략 문구 | 카드 0건, 게시문 0건 |
| 게시문 | 371자. 3,000자 한도의 12% |

게시문 전문:

```
데이터 플랫폼 월 비용 변동 · 2026-09-15

직전 승인 가격(2026-09-11) 대비 단가 1건이 바뀌었습니다.

▪ Redshift 컴퓨트 · 미국 리전 $0.375 → $0.39375 (+5.0%)

월 비용 변동 폭이 가장 큰 조합은 소규모 BI 대시보드 · 미국 리전입니다.

과금 단위가 서로 다른 네 플랫폼을 같은 워크로드 기준으로 환산해 비교했습니다.
약정 할인을 제외한 모델 추정치이며 가정과 계산 과정을 모두 공개합니다.

https://eugeejo-ui.github.io/consumption-insights/

#데이터플랫폼 #클라우드비용 #FinOps #Snowflake #Databricks #BigQuery #Redshift
```

순위만 바뀐 날에는 변동 폭 줄이 빠지고 `월 비용이 낮은 순서가 바뀌었습니다.`만 남는 것을 테스트 픽스처로 확인했다.

### 막혔던 것

없다. `tests/`가 패키지가 아니라 테스트 파일끼리 상수를 가져올 수 없어, 변동 조건 상수 세 개를 두 테스트 파일에 각각 두었다.

### 계획과 달라진 점 (구현 단계)

| 계획 | 실제 | 이유 |
|---|---|---|
| 공개 함수 7개(`price_label`, `cover_title`, `price_change_cards`, `check_complete`, `check_lengths`, `card_text`, `render_linkedin`) | 보조 함수 6개를 더 공개했다: `price_item`, `usd_label`, `scenario_names`, `note_price_change_count`, `representative_scenario`, `closing_card` | 게시문이 카드와 같은 단가 줄을 쓰고, Task 4 템플릿이 같은 금액 표기를, Task 8 소개 카드가 같은 마무리 장을 쓴다. 표기를 한 곳에서만 정의한다 |

Step 0에서 달라진 점은 위 "Step 0 실행 결과" 절에 있다.

### 다음 Task에 넘기는 것

- **Task 4 (카드 템플릿)**
  - 장 종류는 `cover`, `bullets`, `chart`, `banners`, `closing` 다섯 가지다. `page`는 제목 뒤에 강조 없이 붙인다.
  - 틀 문구(상단 바, 하단 알약 `넘기기 / →`·`끝`, 차트 범례 `미국 리전`·`서울 리전`, 배너의 `이전`·`현재`)는 템플릿에 둔다. 데이터에는 없다.
  - 차트 금액은 `card_data.usd_label`로 적는다. 숫자 검사가 이 표기를 기준으로 통과했다.
  - **순위 배너의 서열 문자열은 44자다.** 글자 수 상한표에 배너 항목이 없다. 글자 크기와 줄 수를 정하고 굽기로 확인한다.
  - 마무리 안내 장은 템플릿 `10-closing` 틀이다. 배경은 다른 장과 같고, 주소는 한 줄에 들어가는 크기로 정한다.
  - 테스트 픽스처는 `make_events`를 쓴다.
- **Task 5 (파이프라인)**
  - `price_change_cards`가 `events["display"]`를 채우므로 **카드 데이터를 먼저 만들고 `events.json`을 쓴다.**
  - `prev_rows`는 `estimate(PriceBook(previous_snapshot(day)), workloads)`로 만든다.
  - 게시문은 카드와 따로 만든다. 3,000자 초과 `ValueError`는 검토 PR에서 사람에게 알린다.
- **Task 6 (워크플로):** 10장 초과 경고 문장은 PR 본문 문안과 함께 스크립트 단계를 거친다(규칙 16).
- **Task 8 (소개 카드):** 마무리 장은 `closing_card()`를 재사용한다. 소개 4장 각주는 보완본(두 문장)을 쓴다.
- **D17 교체(다른 대화):** 게시문의 `월 비용`은 `templates/post_linkedin.md.j2` 세 곳(제목, 변동 폭 줄, 순위 줄)과 `tests/test_render_linkedin.py`의 상수 두 개에 있다. 교체할 때 함께 바꾼다.
