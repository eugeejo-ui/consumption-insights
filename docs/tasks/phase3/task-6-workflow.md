# Phase 3 · Task 6: 워크플로 연결

| 항목 | 내용 |
|---|---|
| 상태 | **계획 승인 대기** (2026-09-15 작성). 승인 전에는 구현하지 않는다(규칙 15) |
| 상위 계획 | `docs/plans/phase3-linkedin-cardnews.md` Task 6, 결정 D9, 규칙 4·14·16·18 |
| 담당 | C (사용자 확인 3회: 계획 승인, **검토 PR 본문 문안 승인**, **push·시뮬레이션 실행 승인**) |

## 목표

CI에서 카드가 실제로 구워지고, **검토 PR 본문에서 카드 그림과 게시문을 보고 판단할 수 있게** 한다. 머지 후 게시는 Task 5가 `--build`에 이미 연결했다.

이 Task에서 처음으로 Task 3~6 코드가 GitHub에 올라간다. 올라간 다음 날부터 매일 수집이 새 코드로 돈다.

## 착수 전 확인한 결함 (Task 5 회귀)

**게시 워크플로가 승인일을 읽지 못하게 됐다 [확인].**

- `publish.yml`은 `pipeline.py --build`의 출력 줄 `site written: … (<날짜> 승인 스냅샷)`에서 `sed`로 날짜를 뽑아, 시트 적재 단계에 넘긴다.
- Task 5에서 이 줄을 `(<날짜> 승인 스냅샷, 카드 N일분)`으로 바꿨다. `sed` 식이 맞지 않아 날짜가 빈 값이 된다.
- 결과: 시트 적재 단계가 `data/raw//events.json`을 찾지 못해 **조용히 적재를 건너뛴다.** 게시는 계속되므로 실패로 드러나지 않는다.
- push 전이라 운영에는 영향이 없다.

**수정:** 사람이 읽는 출력 문장을 파싱하지 않는다. `build_site()`가 단계 출력(`GITHUB_OUTPUT`)에 `day`를 직접 쓰고, `publish.yml`은 그 값을 쓴다. 테스트로 고정한다.

## 건드리는 파일

| 파일 | 동작 |
|---|---|
| `docs/scripts/review-pr-script.md` | **신규(Step 0, 규칙 16).** 검토 PR 본문에 새로 들어가는 문안 |
| `publish/review_pr.py` | 신규. 검토 PR 본문 조립(검토 보고서 + 글 초안 + 카드 + 게시문 + 실패 사유 + 장수 경고) |
| `templates/review_pr.md.j2` | 신규. 위 본문의 새 절 |
| `.github/workflows/collect.yml` | 한글 글꼴 설치(pytest보다 먼저), 설치 글꼴 기록, 본문을 `publish.review_pr`로 조립, 제한 시간 15 → 25분 |
| `.github/workflows/publish.yml` | 승인일을 단계 출력에서 읽는다(회귀 수정) |
| `pipeline.py` | `build_site()`가 `day`를 단계 출력에 쓴다 |
| `publish/render_cards.py` | 레이아웃 검사 통과 시 최소 여백·최대 오른쪽 끝을 한 줄로 출력한다(CI 기록용) |
| `tests/test_review_pr.py` | 신규. 테스트 5개 |
| `tests/test_workflows.py` | 신규. 테스트 1개 |
| `tests/test_pipeline.py` | 테스트 1개 추가 |
| `docs/tasks/phase3/task-6-workflow.md` | 이 파일. 실행 후 결과를 덧붙인다 |
| `docs/plans/phase3-linkedin-cardnews.md`, `docs/phases/phase-3-linkedin.md`, `CLAUDE.md` | 규칙 7에 따라 갱신 |

**건드리지 않는 것:** 카드 문안·템플릿·데이터, 기존 검토 보고서(`review.md.j2`)와 글 초안 문안(D17 교체는 다른 대화), 문구 반려 루프(`revise-copy`, Task 7), 소개 카드(Task 8).

## 검토 PR 본문 구성

순서는 기존 두 절 뒤에 새 절 두 개를 붙인다. 카드는 E1인 날에만 붙는다.

| 순서 | 절 | 조건 | 비고 |
|---|---|---|---|
| 1 | 검토 보고서(`review.md`) | 항상 | 기존 |
| 2 | 글 초안(`post.md`) | E1 | 기존 |
| 3 | **카드뉴스 미리보기** | 카드가 구워진 날 | 장마다 이미지. 이미지 주소는 `raw.githubusercontent.com/<저장소>/<커밋 SHA>/data/raw/<날짜>/cards/NN-*.png`. 원본 PDF 링크, 머지 후 게시 주소, 10장 초과 경고 |
| 3' | **카드뉴스 생성 실패** | `card-errors.txt`가 있는 날 | 사유를 코드 블록으로 그대로 싣는다 |
| 4 | **LinkedIn 게시문** | `linkedin.md`가 있는 날 | 복사하기 쉽게 코드 블록으로 싣는다 |

**이미지 주소에 브랜치 이름이 아니라 커밋 SHA를 쓴다.** 검토 브랜치는 같은 날 다시 돌면 강제 push로 갱신된다. 브랜치 이름으로 걸면 캐시 때문에 이전 카드가 보일 수 있다(상위 계획 Task 6).

**본문 조립을 셸이 아니라 파이썬 모듈로 옮긴다.** 조건이 네 가지로 늘어 YAML 안의 셸로는 검증할 수 없다. `python -m publish.review_pr --day <날짜> --repo <저장소> --sha <SHA>`가 본문을 출력하고, 테스트가 모든 조건을 확인한다.

## Step 0 스크립트 초안 (규칙 16, 승인 대상)

아래는 초안이다. `/humanize-korean` 점검을 거쳐 `docs/scripts/review-pr-script.md`에 확정한다. 자리표시자는 `{…}`로 적는다.

| 위치 | 초안 |
|---|---|
| 카드 절 제목 | `## 카드뉴스 미리보기 · {장수}장` |
| 원본 PDF | `원본 PDF: [cards.pdf]({PDF 주소})` |
| 게시 주소 | `머지 후 게시 주소: {사이트 카드 주소}` |
| 10장 초과 경고 | `카드가 {장수}장으로 10장을 넘습니다. 게시 분량은 검토자가 판단합니다.` |
| 이미지 대체 텍스트 | `{순번}장 {장 이름}`. 장 이름은 카드 스크립트의 장 제목을 쓴다(표지, 단가 변동 내역, 플랫폼별 월 사용료, 월 사용료 변동 내역, 순위 변동, 마무리 안내) |
| 실패 절 제목 | `## 카드뉴스 생성 실패` |
| 실패 안내 | `카드 또는 게시문 생성이 실패했습니다. 검토 자료는 정상입니다.` |
| 게시문 절 제목 | `## LinkedIn 게시문` |
| 게시문 안내 | `LinkedIn에는 사람이 직접 게시합니다.` |

## 인터페이스

```python
# publish/review_pr.py
WARN_OVER = 10                                       # 규칙 18: 10장을 넘으면 경고
CARD_NAMES = {"cover": "표지", "price": "단가 변동 내역", "chart": "플랫폼별 월 사용료",
              "cost": "월 사용료 변동 내역", "rank": "순위 변동", "closing": "마무리 안내"}

build_body(day: str, repo: str, sha: str, root: Path = Path("data/raw"),
           site: str = "https://eugeejo-ui.github.io/consumption-insights") -> str
    # data/raw/<날짜>/의 review.md, post.md, cards/, card-errors.txt, linkedin.md를 읽어 본문을 만든다
    # python -m publish.review_pr --day --repo --sha → 표준 출력

# pipeline.py
build_site(day=None)                                  # 기존 + write_outputs(day=<승인일>)

# publish/render_cards.py
check_layout(report, cards) -> dict                   # 기존 검사 + {"min_gap": px, "max_right": px} 반환. bake가 한 줄 출력
```

**`collect.yml` 변경**

```yaml
- name: install Korean fonts            # pytest보다 먼저. 없으면 두부 글자 카드가 된다 [확인 2026-09-12]
  run: sudo apt-get update && sudo apt-get install -y --no-install-recommends fonts-noto-cjk && fc-list :lang=ko family | sort -u
- run: python -m pytest -q
...
- name: open or update review PR
  run: |
    …git commit…
    SHA=$(git rev-parse HEAD)
    python -m publish.review_pr --day "$DAY" --repo "$GITHUB_REPOSITORY" --sha "$SHA" > "$BODY"
```

## 단계

- [ ] **Step 0 검토 PR 본문 스크립트 (규칙 16).** 초안 작성 → `/humanize-korean` 점검 → **사용자 문안 승인.** 승인 전에는 Step 1로 넘어가지 않는다
- [ ] **Step 1** 테스트 7개를 먼저 쓰고 실패를 확인한다
- [ ] **Step 2** `publish/review_pr.py`와 `templates/review_pr.md.j2`를 구현한다
- [ ] **Step 3** `build_site()`의 `day` 단계 출력과 `publish.yml` 수정(회귀 수정)
- [ ] **Step 4** `collect.yml` 수정. `render_cards`의 레이아웃 요약 출력
- [ ] **Step 5** 전체 테스트 → 108개 통과. 로컬에서 Task 5 임시 폴더 산출물로 본문을 만들어 마크다운을 눈으로 확인한다
- [ ] **Step 6** 커밋 전 검사. **push할 전체 범위**(`origin/main..HEAD`, 현재 17개 커밋 + 이 Task)의 변경 내용에서 이메일·로컬 사용자 경로·개인 프로젝트 ID를 찾고, 커밋 작성자 이메일이 모두 noreply인지 확인한다. 커밋
- [ ] **Step 7 사용자 승인 요청 (규칙 4).** 아래 외부 행동 세 가지를 한 번에 여쭙고, 승인 전에는 실행하지 않는다
  1. `origin/main`을 받아 그 위로 올린 뒤(매일 봇 커밋이 쌓여 있다) main에 push. **push하면 `publish.yml`이 돌아 대시보드를 다시 배포한다**(내용 변화 없음)
  2. `collect.yml`을 시뮬레이션으로 수동 실행(`review/simulated` 검토 PR 생성)
  3. 확인이 끝난 시뮬레이션 PR을 닫고 브랜치 삭제
- [ ] **Step 8 CI 실측** (승인 후)
  - 글꼴 설치 시간, `fc-list` 결과에 `Noto Sans CJK KR`이 있는지(Task 4 조정안 6 [미확인] 해소)
  - pytest의 실제 굽기 테스트가 CI에서 **건너뛰지 않고 통과**하는지
  - 1단계 카드 굽기 시간, 레이아웃 요약(최소 여백)
  - PR 본문에 카드 5장이 보이는지. CI가 구운 PNG를 받아 두부 글자가 없는지 눈으로 확인한다
  - 게시 워크플로가 승인일을 읽는지(push로 돈 실행의 `log` 작업 기록)
  - 시뮬레이션 PR을 닫는다
- [ ] **Step 9** 이 파일에 실행 결과를 덧붙이고 관련 문서를 갱신한다. **보고하고 멈춘다**(규칙 10)

## 테스트 목록

**`tests/test_review_pr.py` (5개)** — Task 5의 가짜 굽기처럼 파일을 만들어 검증한다.

| # | 이름 | 확인하는 것 |
|---|---|---|
| 1 | `test_body_shows_review_post_cards_and_linkedin_in_order` | 검토 보고서 → 글 초안 → 카드 → 게시문 순서. 이미지 주소가 SHA로 고정되고 파일 순번대로다. PDF 링크와 머지 후 게시 주소가 있다 |
| 2 | `test_body_has_no_card_section_on_a_non_e1_day` | 카드·게시문 파일이 없는 날에는 두 절이 없다 |
| 3 | `test_card_failure_is_shown_with_its_reason` | `card-errors.txt`가 있으면 실패 절이 생기고 사유가 코드 블록으로 그대로 실린다. 카드 절은 없다 |
| 4 | `test_more_than_ten_cards_adds_a_warning` | 11장이면 경고 문장이 있고, 10장이면 없다 |
| 5 | `test_fixed_copy_matches_the_script` | 본문의 고정 문장이 `docs/scripts/review-pr-script.md` 확정 문안과 글자 단위로 같다 |

**`tests/test_workflows.py` (1개)**

| # | 이름 | 확인하는 것 |
|---|---|---|
| 6 | `test_collect_installs_korean_fonts_before_tests_and_uses_the_body_module` | `collect.yml`에서 `fonts-noto-cjk` 설치가 `pytest`보다 앞에 있고, 본문을 `publish.review_pr`로 만든다 |

**`tests/test_pipeline.py` (1개)**

| # | 이름 | 확인하는 것 |
|---|---|---|
| 7 | `test_build_writes_the_approved_day_to_the_step_output` | `--build`가 `GITHUB_OUTPUT`에 `day=<승인일>`을 쓴다(회귀 방지) |

**합계:** 101 → **108**

## 확인 방법 (증거)

| 확인 항목 | 방법 |
|---|---|
| 테스트 | 로컬 `pytest -q`, CI pytest 단계 기록(실제 굽기 테스트 통과·건너뜀 여부) |
| CI 글꼴 | `fc-list :lang=ko family` 출력 |
| CI 카드 품질 | 시뮬레이션 PR의 PNG를 받아 확인. 레이아웃 요약 줄 |
| PR 본문 | 시뮬레이션 PR 화면 |
| 회귀 수정 | push로 돈 `publish.yml` 실행의 승인일 값 |
| 시간 | 각 단계 소요 시간 |

## 위험

| 위험 | 대응 |
|---|---|
| push하면 매일 수집이 새 코드로 돈다. 실제 E1이 오면 CI가 카드를 굽는다 | 이 Task의 시뮬레이션으로 CI 굽기를 먼저 확인한다. 굽기가 실패해도 검토 PR은 열린다(Task 5) |
| 로컬과 CI 글꼴 차이로 CI에서만 레이아웃 검사에 걸린다 | 걸리면 카드 없이 사유가 PR에 보인다. 이 경우 멈추고 보고한 뒤 디자인 계획부터 고친다(규칙 10) |
| 글꼴 설치로 매일 수집 시간이 늘어난다 | 약 1~2분으로 추정한다 [가정]. 실측값을 기록한다. 제한 시간을 25분으로 늘린다 |
| 로컬 main이 `origin/main`보다 17개 커밋 앞서 있고, 그사이 봇 커밋이 쌓였다 | push 전에 받아서 그 위로 올린다. 봇은 `data/checks.csv`와 가격 지문 파일만 고치므로 충돌 가능성이 낮다. 충돌이 나면 멈추고 보고한다 |
| main 보호 규칙이 없어 잘못된 워크플로가 바로 반영된다 | 기존 결정·확인 대기 항목이다(저장소 보안 설정 4건). push 전 테스트와 YAML 문법 검사로 대신한다 |
| PR 본문의 이미지가 공개 저장소 원본 주소에 의존한다 | 공개 저장소라 인증 없이 보인다. 강제 push로 이전 SHA가 사라져도 본문은 매 실행 새 SHA로 갱신된다 |
| 시뮬레이션 카드는 게시 경로를 검증하지 못한다(승인되지 않으므로 복사되지 않는다) | 게시 복사는 Task 5 테스트와 로컬 실측으로 확인했다. 실제 게시는 Task 9 또는 첫 실제 E1에서 확인한다 |

## 상위 코드 계획과 달라지는 점

| 코드 계획 | 이 계획 | 이유 |
|---|---|---|
| 본문을 워크플로 셸에서 조립 | `publish/review_pr.py` 모듈 | 조건 4가지를 테스트로 검증한다 |
| PR 본문 문안 언급 없음 | Step 0 스크립트 단계 | 규칙 16. PR 본문도 사람이 읽는 자동 생성 문장이다 |
| `continue-on-error`로 카드 단계 분리 | 파이프라인이 실패를 흡수한다(Task 5) | 1단계가 이미 카드 실패를 잡는다. 워크플로에서 따로 분리할 필요가 없다 |
| 10장 초과 경고는 Task 3 | 이 Task | Task 3에서 옮겼다 |
| 회귀 수정 없음 | `publish.yml` 승인일 읽기 수정 | 계획 작성 중 발견한 Task 5 회귀 |
| 테스트: 워크플로 실측만 | +7 → 108 | 본문 조건, 워크플로 순서, 회귀를 코드로 고정한다 |

## 완료 기준

- 검토 PR 본문 문안이 승인됐다.
- 테스트 7개를 추가해 전체 108개가 통과한다.
- 사용자 승인 아래 push했고, 시뮬레이션 검토 PR에 CI가 구운 카드와 게시문이 보인다.
- CI 카드에 두부 글자가 없고 레이아웃 검사를 통과했다.
- 게시 워크플로가 승인일을 읽는다.
- 이 파일에 실행 결과가 덧붙고, 관련 문서가 갱신되고, 커밋됐다.
