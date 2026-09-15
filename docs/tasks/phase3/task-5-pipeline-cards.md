# Phase 3 · Task 5: 파이프라인 연결

| 항목 | 내용 |
|---|---|
| 상태 | **계획 승인 대기** (2026-09-15 작성). 승인 전에는 구현하지 않는다(규칙 15) |
| 상위 계획 | `docs/plans/phase3-linkedin-cardnews.md` Task 5, 결정 D9(수집 단계에서 만들고 머지 후 게시), 규칙 14·18 |
| 담당 | C (사용자 확인 1회: 계획 승인) |

## 목표

Task 3·4에서 만든 카드 데이터·게시문·굽기를 `pipeline.py`에 연결한다. **E1인 날 1단계를 돌리면 검토 자료와 함께 카드와 게시문이 생기고, 승인된 날의 카드는 사이트 빌드 때 `site/cards/<날짜>/`로 복사된다.**

지켜야 할 원칙은 세 가지다.

1. **카드는 부가물이다.** 카드 데이터·게시문·굽기 중 무엇이 실패해도 `review.md`와 `events.json`은 남고 검토 PR은 열린다(상위 계획 전역 제약). 실패는 조용히 넘기지 않고 파일과 단계 출력에 남긴다.
2. **게시는 승인 이후다**(규칙 14, D9). 승인 기록(`approved.txt`)이 없는 날의 카드는 사이트에 복사하지 않는다. 시뮬레이션 스냅샷도 여기서 걸러진다.
3. **두부 글자 카드를 만들지 않는다.** 이 Task가 들어가면 매일 수집이 CI에서 카드를 굽는다. CI에는 한글 글꼴이 없다 [확인 2026-09-12]. 글꼴이 없으면 굽지 않고 실패로 기록한다.

## 건드리는 파일

| 파일 | 동작 |
|---|---|
| `pipeline.py` | 1단계에 카드·게시문 연결, `--cards DAY` 추가, 사이트 빌드 때 승인된 카드 복사 |
| `publish/render_cards.py` | 굽기 전 한글 글꼴 확인(`korean_font_available`) |
| `tests/test_pipeline.py` | 테스트 7개 추가 |
| `tests/test_render_cards.py` | 테스트 1개 추가. 실제 굽기 테스트는 한글 글꼴이 없으면 건너뛰도록 조건을 바꾼다 |
| `docs/tasks/phase3/task-5-pipeline-cards.md` | 이 파일. 실행 후 결과를 덧붙인다 |
| `docs/plans/phase3-linkedin-cardnews.md`, `docs/phases/phase-3-linkedin.md`, `CLAUDE.md` | 규칙 7에 따라 갱신 |

**건드리지 않는 것:** 워크플로(`collect.yml`·`publish.yml`은 Task 6), 카드 문안·템플릿(Task 3·4에서 확정), 소개 카드(`--cards intro`는 Task 8).

## 산출물 (E1인 날)

```
data/raw/<날짜>/
    review.md  events.json  post.md          # 기존. events.json에 display(건수·차트 금액)가 더해진다
    linkedin.md                              # 신규. 게시문
    cards/  cards.html  01-cover.png … NN-closing.png  cards.pdf   # 신규
    card-errors.txt                          # 신규. 실패가 있을 때만 생긴다
site/cards/<승인일>/                         # 사이트 빌드 때. 승인된 날만
    cards.html  *.png  cards.pdf  linkedin.md
```

## 인터페이스

```python
# pipeline.py
CARDS_DIR = "cards"
LINKEDIN_FILE = "linkedin.md"
CARD_ERRORS_FILE = "card-errors.txt"

make_card_outputs(folder: Path, events: dict, rows: list[CostRow], previous: list[PriceRecord] | None,
                  workloads: dict) -> list[str]
    # 1단계용. 이전 산출물(cards/, linkedin.md, card-errors.txt)을 먼저 지운다(같은 날 다시 돌린 경우)
    # E1이 아니면 아무것도 만들지 않는다
    # 순서: 카드 데이터 → 게시문 텍스트 → events.json 쓰기 → linkedin.md → 굽기
    # 단계마다 예외를 잡아 오류 문장 목록으로 돌려준다. 목록이 비어 있지 않으면 card-errors.txt에 쓴다

rebuild_cards(day: str) -> Path
    # --cards DAY. 저장된 events.json과 그날 스냅샷, events.compared_to 스냅샷으로 다시 만든다
    # 명시적으로 부른 명령이라 실패를 잡지 않고 그대로 드러낸다. approved.txt는 건드리지 않는다

publish_cards(site: Path = Path("site")) -> list[Path]
    # site/cards/를 비우고, approved.txt가 있는 날의 cards/와 linkedin.md를 site/cards/<날짜>/로 복사한다
    # build_site()와 confirm()이 사이트를 그린 뒤 부른다

# publish/render_cards.py
korean_font_available() -> bool
    # Windows·macOS는 참(맑은 고딕·Apple SD Gothic Neo 기본 포함) [지식]. 그 밖에는 `fc-list :lang=ko` 결과가 있어야 참
    # bake()가 맨 처음 확인한다. 없으면 RuntimeError("한글 글꼴이 없다 …")
```

**GitHub Actions 단계 출력(`GITHUB_OUTPUT`) 추가:** `cards=ok|failed|skipped`, `card_count=<장수>`. Task 6이 검토 PR 본문에 쓴다.

**`events.json` 쓰기 순서가 바뀐다.** 지금은 `review.md` 다음에 바로 쓴다. 카드 데이터가 `events["display"]`를 채우므로(Task 3 인계) 카드 데이터를 만든 뒤에 쓴다. 카드 데이터가 실패해도 `events.json`은 쓴다.

**`card-errors.txt`의 성격:** 개발자용 진단 기록이다(예외 메시지를 단계 이름과 함께 한 줄씩). 공개 문안이 아니므로 스크립트 단계 대상이 아니다. Task 6에서 이 내용을 검토 PR 본문에 보여 줄 때 감싸는 문장은 규칙 16의 스크립트 단계를 거친다.

## 단계

- [ ] **Step 1** 테스트 8개를 먼저 쓰고 실패를 확인한다
- [ ] **Step 2** `render_cards.korean_font_available`과 `bake`의 글꼴 확인을 구현한다. 실제 굽기 테스트의 건너뛰기 조건에 글꼴을 더한다
- [ ] **Step 3** `pipeline.py`에 `make_card_outputs`를 구현하고 `collect_and_review()`에 연결한다
- [ ] **Step 4** `rebuild_cards`와 `--cards DAY` 인자를 구현한다
- [ ] **Step 5** `publish_cards`를 구현하고 `build_site()`·`confirm()`에 연결한다
- [ ] **Step 6** 전체 테스트를 돌린다 → 100개 통과
- [ ] **Step 7 로컬 실측** (작업 사본을 더럽히지 않도록 임시 폴더에서)
  - 실제 승인 스냅샷을 임시 폴더로 복사하고, 수집기를 실제 승인 가격 + Redshift 미국 리전 +5%로 바꿔 1단계를 돌린다
  - 확인: `cards/` 7개 파일(HTML·PNG 5장·PDF), `linkedin.md`, `events.json`의 `display`, `card-errors.txt` 없음, 단계 출력 `cards=ok`
  - 글꼴이 없는 상황을 흉내 내 다시 돌린다. 확인: 검토 자료는 그대로, `card-errors.txt`에 글꼴 사유, `cards=failed`
  - 임시 폴더에서 승인 기록을 만든 뒤 `--build`를 돌려 `site/cards/<날짜>/`에 파일이 복사되는지 확인한다
- [ ] **Step 8** 개인정보 검사 → 커밋 `feat: make cards as part of the daily pipeline` → `git ls-files` 확인
- [ ] **Step 9** 이 파일에 실행 결과를 덧붙이고 관련 문서를 갱신한다. **보고하고 멈춘다**(규칙 10)

## 테스트 목록

`tests/test_pipeline.py` (7개). 굽기는 가짜 함수로 바꿔 브라우저 없이 검증한다. 가짜 함수는 파일을 만들고 받은 인자를 기록한다.

| # | 이름 | 확인하는 것 |
|---|---|---|
| 1 | `test_e1_run_writes_cards_and_the_linkedin_post` | E1인 날 `linkedin.md`가 생기고, 굽기가 `data/raw/<날짜>/cards`와 `가격 변동 리포트`로 불린다. `events.json`에 `display`가 있다. 단계 출력 `cards=ok`, `card_count=5`. `card-errors.txt`가 없다 |
| 2 | `test_non_e1_run_makes_no_cards_and_clears_stale_ones` | 단가는 바뀌었지만 E1이 아닌 날에는 굽기를 부르지 않는다. 같은 날 앞선 실행이 남긴 `cards/`·`linkedin.md`가 지워진다. `cards=skipped` |
| 3 | `test_card_failure_keeps_the_review_and_records_the_error` | 굽기가 예외를 내도 `review.md`·`events.json`·`post.md`·`linkedin.md`가 남는다. `card-errors.txt`에 사유가 있다. `cards=failed`. 1단계는 정상 종료한다 |
| 4 | `test_linkedin_failure_is_recorded_and_cards_still_bake` | 게시문이 3,000자 초과 등으로 실패해도 카드는 굽는다. 사유가 기록된다 |
| 5 | `test_cards_command_rebuilds_without_touching_approval` | `--cards DAY`가 저장된 `events.json`으로 카드와 게시문을 다시 만든다. `approved.txt` 내용이 그대로다 |
| 6 | `test_cards_command_refuses_a_day_without_an_e1_event` | `events.json`이 없거나 E1이 아닌 날은 `SystemExit`로 거부한다 |
| 7 | `test_site_build_publishes_only_approved_cards` | 승인된 날의 카드와 `linkedin.md`는 `site/cards/<날짜>/`로 복사되고, 승인 기록이 없는 날(시뮬레이션 포함)은 복사되지 않는다 |

`tests/test_render_cards.py` (1개)

| # | 이름 | 확인하는 것 |
|---|---|---|
| 8 | `test_bake_refuses_without_a_korean_font` | 글꼴 확인이 거짓이면 브라우저를 부르기 전에 `한글 글꼴`로 멈춘다 |

**합계:** 92 → **100**

## 확인 방법 (증거)

| 확인 항목 | 방법 |
|---|---|
| 테스트 | `.venv\Scripts\python.exe -m pytest -q` 결과 개수 |
| 1단계 연결 | Step 7 임시 폴더 실행의 파일 목록과 단계 출력 |
| 실패 격리 | 글꼴 없음 흉내 실행에서 검토 자료가 남는지 |
| 게시 범위 | `--build` 뒤 `site/cards/`에 승인된 날만 있는지 |

## 위험

| 위험 | 대응 |
|---|---|
| 이 Task를 push하면 CI 매일 수집이 카드를 굽는데 한글 글꼴이 없다 | `bake`가 글꼴을 먼저 확인하고 멈춘다. 검토 PR은 그대로 열리고 `card-errors.txt`에 사유가 남는다. 글꼴 설치는 Task 6이다. **push는 Task 6 실측 때 사용자 승인을 받아 함께 한다**(규칙 4). 그 전까지는 로컬 커밋만 한다 |
| CI의 pytest 단계에서 실제 굽기 테스트가 두부 글자로 돌거나 글꼴 확인에 걸려 실패한다 | 실제 굽기 테스트의 건너뛰기 조건을 "브라우저가 없거나 한글 글꼴이 없으면"으로 바꾼다 |
| 같은 날 다시 수집하면 앞선 실행의 카드가 남아 검토 PR에 섞인다 | 1단계가 이전 카드 산출물을 먼저 지운다(테스트 2). 굽기도 이전 PNG를 지운다(Task 4) |
| 카드 PNG·PDF를 커밋하면 저장소가 커진다 | E1인 날에만 생긴다. 한 번에 약 0.5~1MB로 추정한다 [가정]. 검토 PR 본문에 이미지를 보이려면 커밋이 필요하다(Task 6 설계) |
| `--cards`로 다시 만들 때 `workloads.yaml`이 그날 이후 바뀌었으면 차트 금액과 `events.json`이 어긋난다 | 숫자 검사가 어긋남을 잡아 멈춘다. 기존 `detect`도 현재 가정으로 계산하는 설계와 같다. 기록으로 남긴다 |
| 1단계 실행 시간이 늘어난다 | 로컬 Edge 기준 5장 약 47초 [확인]. CI Chrome은 Task 6에서 잰다 |

## 상위 코드 계획과 달라지는 점

| 코드 계획 | 이 계획 | 이유 |
|---|---|---|
| 테스트 4개(+4 → 89) | 8개(+8 → 100) | 게시문 실패 분리, `--cards` 거부, 승인된 카드만 게시, 글꼴 확인을 더 검증한다 |
| `--cards DAY`에서 `DAY`가 `intro`면 소개 카드 | 날짜만 받는다 | 소개 카드는 Task 8에서 `intro`를 더한다 |
| 굽기 실패는 경고만 출력 | `card-errors.txt`와 단계 출력 `cards=failed`로 남긴다 | 규칙 18이 게시문 3,000자 초과 시 "사람에게 알린다"고 정했다. 경고 출력은 CI 로그에 묻힌다 |
| 글꼴 확인 없음 | 굽기 전에 한글 글꼴을 확인한다 | Task 4 인계. 레이아웃 검사는 두부 글자를 잡지 못한다 |
| `--build`의 카드 복사를 Task 6에 적은 곳이 있다(파일 구조 절) | Task 5에서 한다 | `pipeline.py`의 로컬 동작이라 테스트로 검증할 수 있다. Task 6은 워크플로만 다룬다 |

## 완료 기준

- E1인 날 1단계가 카드·게시문을 만들고, 어떤 실패도 검토 자료를 막지 않는다.
- 승인된 날의 카드만 사이트 빌드에 포함된다.
- 한글 글꼴이 없으면 굽지 않고 사유를 남긴다.
- 테스트 8개를 추가해 전체 100개가 통과한다.
- 이 파일에 실행 결과가 덧붙고, 관련 문서가 갱신되고, 커밋됐다.
