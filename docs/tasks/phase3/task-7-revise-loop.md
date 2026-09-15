# Phase 3 · Task 7: 문구 반려 재작성 루프

| 항목 | 내용 |
|---|---|
| 상태 | **완료** (2026-09-15, `5f8740f`, 테스트 117개). 계획·새 문안·push·실측 모두 승인받아 진행했다 |
| 상위 계획 | `docs/plans/phase3-linkedin-cardnews.md` Task 7, 결정 D14, 규칙 4·14·16 |
| 담당 | C (사용자 확인 3회: 계획 승인, **새 문안 승인**, **push·실측 승인**) |

## 목표

사용자가 검토 PR에서 **카드뉴스나 LinkedIn 게시문의 문구만 반려**할 수 있게 한다. 라벨 하나를 붙이면 재작성 요청이 열리고, 문구가 고쳐질 때까지 게시되지 않는다. 재작성은 Claude가 대화에서 `/humanize-korean`으로 수행하고, 같은 검토 PR이 새 문구로 갱신된다.

| 사용자 행동 | 의미 | 결과 |
|---|---|---|
| PR 머지 | 승인 | 게시와 적재가 진행된다(기존) |
| PR에 `revise-copy` 라벨 + 코멘트로 사유 | **문구 반려** | 재작성 요청 Issue가 열리고, 게시가 막힌다 |
| PR 닫기 | 전면 반려 | 아무것도 진행되지 않는다(기존) |

**반려 대상 문구:** 카드뉴스(`docs/scripts/cards-script.md`)와 LinkedIn 게시문(`docs/scripts/linkedin-post-script.md`)의 고정 문안이다. 숫자와 자리표시자는 데이터에서 오므로 대상이 아니다. 검토 보고서·글 초안 문안은 D17 교체와 겹치므로 이 루프에서 다루지 않는다.

## 설계 판단

### 1. 고친 문안은 main에 올리고, 검토 PR은 수집 워크플로를 다시 돌려 갱신한다

문안은 스냅샷 데이터가 아니라 코드(`publish/card_data.py`의 문자열, `templates/post_linkedin.md.j2`)에 있다. 두 가지 방법을 비교했다.

| 방법 | 문제 |
|---|---|
| 검토 브랜치에만 문안 수정을 커밋 | 매일 수집이 검토 브랜치를 main에서 다시 만들어 강제 push한다(`collect.yml`). **머지 전에 다음 날 수집이 돌면 고친 문안이 사라진다** |
| **main에 문안 수정을 올리고 수집 워크플로를 수동 실행** | 기존 흐름을 그대로 쓴다. 수집 워크플로가 새 문안으로 카드를 CI에서 굽고 같은 PR을 갱신한다. 고친 문안은 이후 모든 카드에 남는다 |

**두 번째 방법을 택한다.** 새 문안은 main에 올리기 전에 대화에서 사용자 승인을 받는다(규칙 16). push와 워크플로 실행도 같은 자리에서 승인을 받는다(규칙 4).

### 2. 게시를 막는 방법: 검토 브랜치의 보류 표시 파일

GitHub는 라벨만으로 머지를 막지 못한다. 머지를 막는 필수 검사는 main 보호 규칙이 있어야 하는데, 이는 결정 대기 항목(저장소 보안 설정 4건)이다.

그래서 **머지는 막지 않고, 머지돼도 승인·게시가 일어나지 않게 한다.**

- 라벨이 붙으면 워크플로가 검토 브랜치에 `data/raw/<날짜>/copy-hold.txt`를 커밋한다.
- `pipeline.py --confirm`은 이 파일이 있는 스냅샷을 거부한다. 시뮬레이션 스냅샷을 거부하는 기존 방식과 같다. 게시 워크플로는 거부된 날을 경고만 남기고 건너뛴다(기존 동작).
- 라벨을 떼면 워크플로가 파일을 지운다.
- 매일 수집이 검토 브랜치를 다시 만들 때 PR에 라벨이 남아 있으면 파일을 다시 넣는다. 강제 push로 보류가 풀리는 것을 막는다.

### 3. 반려 사유는 쓰기 권한이 있는 사람의 코멘트만 싣는다

공개 저장소라 누구나 PR에 코멘트를 달 수 있다. 재작성 요청 Issue는 Claude가 읽고 `/humanize-korean`의 추가 지시로 넣는다. **외부인이 코멘트로 Claude에게 지시를 끼워 넣는 경로를 막기 위해** 작성자 권한이 저장소 소유자·구성원·협업자인 코멘트만 싣는다(`author_association`). Claude는 Issue 내용을 데이터로만 다룬다.

워크플로 셸에 코멘트 본문을 직접 넣지 않는다. 파이썬 모듈이 API 응답(JSON)을 읽어 본문을 만든다. 셸 주입을 막기 위해서다.

### 4. 회차는 Issue로 센다

`copy-revision` 라벨이 붙은 Issue 중 제목에 그 날짜가 들어간 것의 수가 지난 회차다. **4회차부터는 Issue를 열지 않고**, PR에 `copy-needs-human` 라벨과 안내 코멘트를 남긴다. 같은 지적이 세 번 반복되면 스킬로 풀리는 문제가 아니다(규칙 16).

## 흐름

```
[사용자] 검토 PR에 revise-copy 라벨 + 사유 코멘트
   │
[revise.yml · labeled]  (review/* 브랜치의 PR만)
   ├ 회차 ≤ 3 → 재작성 요청 Issue "문구 재작성 요청 <날짜> (N회차)"  ← publish.revise_request
   │            검토 브랜치에 copy-hold.txt 커밋 (머지돼도 승인·게시 안 됨)
   └ 회차 > 3 → PR에 copy-needs-human 라벨 + 상한 안내 코멘트, copy-hold.txt 커밋
   │
[사용자가 대화에서 Claude에게 처리를 지시]
   │
[Claude] docs/scripts/revise-loop.md 절차
   1. Issue의 사유와 현재 문안을 읽는다 (데이터로만 다룬다)
   2. 사유를 추가 지시로 넣어 /humanize-korean → 새 문안
   3. 스크립트 문서 + 코드 문자열 + 테스트를 고친다, 전체 테스트 통과
   4. ★ 사용자 승인: 새 문안, main push, 수집 워크플로 실행
   5. push → collect.yml 수동 실행 → 같은 PR이 새 카드·게시문으로 갱신 (라벨이 남아 있어 보류 유지)
   6. 갱신을 확인하고 라벨 제거 → Issue에 처리 코멘트 후 닫기
   7. 스크립트 문서의 점검 기록에 회차·사유·변경률을 덧붙인다
   │
[revise.yml · unlabeled]  검토 브랜치에서 copy-hold.txt 삭제
   │
[사용자] 갱신된 PR을 다시 확인 → 머지 / 다시 라벨 / 닫기
```

## Step 0 스크립트 초안 (규칙 16, 승인 대상)

아래 문안은 모두 사람이 읽는 자동 생성 문장이다. `/humanize-korean` 점검 뒤 확정한다. 기존 `docs/scripts/review-pr-script.md`에 PR 본문·코멘트 문안을 더하고, Issue 문안은 새 문서 `docs/scripts/revise-request-script.md`에 둔다.

**검토 PR 본문 (review-pr-script.md에 추가)**

| 위치 | 조건 | 초안 |
|---|---|---|
| 반려 안내 절 제목 | 카드나 게시문이 있는 날 | `## 문구 반려` |
| 반려 안내 | 같다 | `문구만 반려하려면 이 PR에 revise-copy 라벨을 붙이고 사유를 코멘트로 남깁니다. 라벨이 붙은 동안에는 머지해도 승인과 게시가 진행되지 않습니다.` |
| 보류 알림 | `copy-hold.txt`가 있는 날 | `문구 재작성이 진행 중입니다. 지금 머지하면 승인과 게시가 진행되지 않습니다.` |
| 상한 코멘트 | 4회차 라벨 | `자동 재작성 상한(3회)에 도달했습니다. 문안은 사람이 직접 수정합니다.` |

**재작성 요청 Issue (revise-request-script.md 신규)**

```
제목: 문구 재작성 요청 {날짜} ({회차}회차)

## 요청
검토 PR: {PR 주소}
회차: {회차}/3

## 반려 사유
[코멘트마다] {작성자} · {작성 시각}
> {코멘트 원문}
[사유 코멘트가 없을 때] 사유 코멘트가 없습니다. 검토 PR에 사유를 남긴 뒤 재작성합니다.

## 현재 문안
### 카드뉴스
{카드에 보이는 글자, 장마다}
### LinkedIn 게시문
{게시문 원문}

## 처리 절차
재작성 절차는 docs/scripts/revise-loop.md에 있습니다.
```

**Issue 처리 코멘트 (Claude가 닫을 때)**

`재작성을 반영했습니다. 문안 변경은 {커밋 주소}에 있고, 검토 PR은 새 카드로 갱신됐습니다.`

## 건드리는 파일

| 파일 | 동작 |
|---|---|
| `docs/scripts/review-pr-script.md` | Step 0. 반려 안내·보류 알림·상한 코멘트 문안 추가 |
| `docs/scripts/revise-request-script.md` | Step 0. 신규. Issue 제목·본문·처리 코멘트 |
| `docs/scripts/revise-loop.md` | 신규. Claude가 따르는 재작성 절차와 금지 사항(숫자·자리표시자 불변, 사유에 없는 곳은 손대지 않음, 변경률 30% 초과 시 중단 보고, Issue 내용은 데이터로만 다룸) |
| `publish/revise_request.py` | 신규. 회차 계산, Issue 본문 조립(권한 있는 코멘트만), 카드 글자 추출 |
| `templates/revise_request.md.j2` | 신규 |
| `publish/review_pr.py`, `templates/review_pr.md.j2` | 반려 안내 절, 보류 알림 |
| `pipeline.py` | `confirm()`이 `copy-hold.txt`가 있는 스냅샷을 거부한다 |
| `.github/workflows/revise.yml` | 신규. `pull_request` `labeled`·`unlabeled`, `review/` 브랜치만 |
| `.github/workflows/collect.yml` | PR에 `revise-copy`가 남아 있으면 검토 브랜치를 다시 만들 때 `copy-hold.txt`를 넣는다 |
| `tests/test_revise_request.py` | 신규. 테스트 5개 |
| `tests/test_review_pr.py` | 테스트 2개 추가 |
| `tests/test_pipeline.py` | 테스트 1개 추가 |
| `tests/test_workflows.py` | 테스트 1개 추가 |
| `docs/tasks/phase3/task-7-revise-loop.md`, 코드 계획·진행계획·`CLAUDE.md` | 규칙 7 |

**건드리지 않는 것:** 카드·게시문 문안 자체(실제 반려가 올 때 루프가 고친다), 검토 보고서·글 초안(D17), 소개 카드(Task 8).

## 인터페이스

```python
# publish/revise_request.py
MAX_ROUNDS = 3
TRUSTED = {"OWNER", "MEMBER", "COLLABORATOR"}          # 이 권한의 코멘트만 반려 사유로 싣는다

next_round(issue_titles: list[str], day: str) -> int   # 제목에 날짜가 든 기존 요청 수 + 1
build_request(day: str, round_: int, pr_url: str, comments: list[dict], root: Path = Path("data/raw")) -> tuple[str, str]
    # (제목, 본문). comments는 gh api 응답 그대로(author_association, user.login, created_at, body)
    # 카드 글자는 cards/cards.html의 보이는 글자(render_cards.visible_text), 게시문은 linkedin.md
# python -m publish.revise_request --day --round --pr-url --comments <json 파일> → 제목 첫 줄 + 본문

# pipeline.py
COPY_HOLD_FILE = "copy-hold.txt"
confirm(day)                                             # 기존 + copy-hold.txt가 있으면 SystemExit("문구 재작성 중")
```

**`revise.yml` 골격**

```yaml
on:
  pull_request:
    types: [labeled, unlabeled]
permissions: {contents: write, issues: write, pull-requests: write}
jobs:
  revise:
    if: github.event.label.name == 'revise-copy' && startsWith(github.head_ref, 'review/')
        && github.event.pull_request.head.repo.full_name == github.repository
    # labeled: 라벨 준비 → 회차 계산 → (≤3) Issue 생성 / (>3) copy-needs-human + 코멘트 → copy-hold.txt 커밋·push
    # unlabeled: copy-hold.txt 삭제 커밋·push
    # 코멘트·제목 같은 사용자 입력은 셸 식(${{ }})에 넣지 않고 gh api JSON을 파이썬이 읽는다
```

## 단계

- [x] **Step 0 스크립트 (규칙 16).** 위 초안 작성 → `/humanize-korean` 점검 → **사용자 문안 승인.** 승인 전에는 Step 1로 넘어가지 않는다
  - 2026-09-15 작성·점검 완료, **2026-09-15 사용자 승인.** `docs/scripts/review-pr-script.md` 5~7절, `docs/scripts/revise-request-script.md` 신규. run `2026-09-15-003` light, 변경률 0.0%, 게이트 exit 0. 스킬 제안 4건 중 1건 반영(처리 코멘트 능동 통일, 반영본 변경률 0.3%)
  - **초안에서 달라진 점**
    | 초안 | 스크립트 | 이유 |
    |---|---|---|
    | `라벨을 붙이고 사유를 코멘트로 남깁니다` | `사유를 코멘트로 남긴 뒤 이 PR에 revise-copy 라벨을 붙입니다` | 워크플로는 라벨이 붙는 순간의 코멘트를 읽는다. 순서가 반대면 사유 없는 요청이 열린다 |
    | 반려 안내 2문장 | 3문장. `숫자와 항목은 데이터에서 오므로 반려 대상이 아닙니다.` 추가 | 반려 채널의 범위를 밝힌다(목표 절의 반려 대상과 같다) |
    | 보류 알림 위치 미정 | 본문 맨 위 경고 블록, 요청 주소 줄 추가. 라벨을 붙이거나 뗄 때 워크플로가 본문을 다시 만든다 | 머지 전에 보여야 한다. 본문을 다시 만들지 않으면 라벨을 뗀 뒤에도 알림이 남는다 |
    | 사유 줄 `{작성자} · {작성 시각}` | `{작성 시각}`만 | 권한 있는 사람의 코멘트만 싣으므로 작성자 구분이 필요 없다. 기록되는 개인 식별 정보를 줄인다(규칙 11) |
    | 모든 권한 있는 코멘트 | 2회차부터 직전 요청 이후 코멘트만 | 이미 반영한 사유가 다시 실리지 않게 한다 |
    | 처리 코멘트 1문장(`…에 있고, …갱신됐습니다`) | 2문장 + `문안 변경`·`변경률` 라벨 줄 | 한 문장에 사실 하나(규칙 16). 회차별 변경률 기록(규칙 16)을 Issue에도 남긴다 |
- [x] **Step 1** 테스트 9개를 먼저 쓰고 실패를 확인한다
- [x] **Step 2** `publish/revise_request.py`, 템플릿
- [x] **Step 3** `confirm()` 보류 거부, `review_pr` 반려 안내·보류 알림
- [x] **Step 4** `revise.yml`, `collect.yml` 보류 유지
- [x] **Step 5** `docs/scripts/revise-loop.md`(Claude 절차서)
- [x] **Step 6** 전체 테스트 → 117개 통과. 개인정보 검사, 커밋
- [x] **Step 7 사용자 승인 요청 (규칙 4).** 아래 외부 행동을 한 번에 여쭙는다
  1. main push
  2. 수집 워크플로 시뮬레이션 실행(`review/simulated` PR)
  3. 그 PR에 `revise-copy` 라벨과 시험용 사유 코멘트 달기 → Issue 생성·`copy-hold.txt` 커밋 확인
  4. 라벨 제거 → `copy-hold.txt` 삭제 확인
  5. 시험 Issue와 시뮬레이션 PR 닫기, 브랜치 삭제
- [x] **Step 8 CI 실측** (승인 후). 위 3·4의 결과, Issue 본문의 사유·현재 문안, 워크플로 소요 시간. 재작성 자체(Claude 절차)는 실제 반려가 올 때 수행한다
- [x] **Step 9** 실행 결과 기록, 문서 갱신. **보고하고 멈춘다**(규칙 10)

## 테스트 목록

**`tests/test_revise_request.py` (5개)**

| # | 이름 | 확인하는 것 |
|---|---|---|
| 1 | `test_round_counts_previous_requests_for_the_same_day` | 같은 날짜의 기존 요청 2건 → 3회차. 다른 날짜의 요청은 세지 않는다 |
| 2 | `test_request_carries_reasons_and_the_current_copy` | 제목 `문구 재작성 요청 <날짜> (N회차)`, 사유 코멘트 원문, 카드 글자, 게시문 원문, PR 주소가 본문에 있다 |
| 3 | `test_only_trusted_comments_become_reasons` | `NONE`·`CONTRIBUTOR` 권한 코멘트와 봇 코멘트는 싣지 않는다 |
| 4 | `test_request_without_reasons_says_so` | 사유 코멘트가 없으면 안내 문장이 들어간다 |
| 5 | `test_request_copy_matches_the_script` | 고정 문장이 `revise-request-script.md`와 글자 단위로 같다 |

**`tests/test_review_pr.py` (2개 추가)**

| # | 이름 | 확인하는 것 |
|---|---|---|
| 6 | `test_body_explains_how_to_reject_the_copy` | 카드나 게시문이 있는 날 반려 안내 절이 있고, 없는 날에는 없다 |
| 7 | `test_body_warns_while_the_copy_is_on_hold` | `copy-hold.txt`가 있으면 보류 알림이 있다 |

**`tests/test_pipeline.py` (1개 추가)**

| # | 이름 | 확인하는 것 |
|---|---|---|
| 8 | `test_confirm_refuses_a_snapshot_on_copy_hold` | `copy-hold.txt`가 있으면 `--confirm`이 거부하고 `approved.txt`를 만들지 않는다 |

**`tests/test_workflows.py` (1개 추가)**

| # | 이름 | 확인하는 것 |
|---|---|---|
| 9 | `test_revise_workflow_is_scoped_and_never_puts_comments_in_the_shell` | `revise.yml`이 `revise-copy`·`review/`·같은 저장소로 한정되고, `github.event.comment`·`pull_request.body` 같은 사용자 입력을 `${{ }}`로 셸에 넣지 않는다. `collect.yml`이 라벨이 있으면 보류 파일을 넣는다 |

**합계:** 108 → **117**

## 확인 방법 (증거)

| 확인 항목 | 방법 |
|---|---|
| 테스트 | 로컬 `pytest -q`, CI pytest 단계 |
| 반려 흐름 | 시뮬레이션 PR에 라벨을 붙여 생긴 Issue 본문과 `copy-hold.txt` 커밋 |
| 보류 해제 | 라벨 제거 뒤 `copy-hold.txt` 삭제 커밋 |
| 게시 차단 | `confirm` 거부 테스트. 실제 머지는 하지 않는다(시뮬레이션 스냅샷은 원래 승인되지 않아 CI 머지로는 구분이 안 된다) |

## 위험

| 위험 | 대응 |
|---|---|
| 라벨이 붙은 PR을 머지할 수 있다 | 막지는 못한다. 머지돼도 `copy-hold.txt` 때문에 승인·게시가 일어나지 않는다. 다음 수집이 새 검토 PR을 연다 |
| 매일 수집이 검토 브랜치를 강제 push해 보류 파일이 사라진다 | `collect.yml`이 라벨을 확인해 다시 넣는다(테스트 9) |
| 외부인이 PR 코멘트로 재작성 지시를 끼워 넣는다 | 권한 있는 코멘트만 싣는다(테스트 3). Claude는 Issue 내용을 데이터로 다룬다(절차서에 명시) |
| 코멘트 본문이 셸에서 실행된다 | 사용자 입력을 `${{ }}`로 셸에 넣지 않는다(테스트 9) |
| 문안을 고치면 이후 모든 카드에 반영된다 | 의도한 동작이다. 문안은 하나의 정본(스크립트)을 따른다. main에 올리기 전에 사용자 승인을 받는다 |
| 문안 수정이 카드 레이아웃을 깨뜨린다 | 수집 워크플로 재실행이 CI에서 레이아웃 검사를 돈다. 실패하면 PR 본문에 사유가 보인다(Task 6) |
| `pull_request` 이벤트는 PR 브랜치의 워크플로 파일로 돈다 | 검토 브랜치는 main에서 만들어지므로 main의 `revise.yml`과 같다. main에 올린 뒤 만든 PR부터 동작한다 |
| 3회를 넘기면 자동 재작성이 멈춘다 | 규칙 16의 설계다. 사람이 문안을 고친다 |

## 상위 코드 계획과 달라지는 점

| 코드 계획 | 이 계획 | 이유 |
|---|---|---|
| 재작성 후 검토 브랜치에 커밋해 같은 PR 갱신 | main에 문안 커밋 → 수집 워크플로 재실행으로 PR 갱신 | 매일 수집이 검토 브랜치를 강제 push해 브랜치 커밋이 사라진다(설계 판단 1) |
| "라벨이 붙으면 게시는 진행되지 않는다"의 구현 방법 없음 | `copy-hold.txt` + `confirm` 거부 | main 보호 규칙 없이 게시를 막는다(설계 판단 2) |
| 반려 사유 = PR 코멘트 | 권한 있는 사람의 코멘트만 | 공개 저장소의 지시 주입 경로를 막는다(설계 판단 3) |
| 테스트 "게시문에 회차 표기" | 없음 | 회차는 Issue와 점검 기록에 남긴다. 공개 게시문에 내부 회차를 적을 이유가 없다 |
| 테스트 +2 → 110 | +9 → 117 | 보류, 권한 필터, 셸 주입 방지를 검증한다 |

## 완료 기준

- 새 문안(PR 안내·Issue·코멘트)이 승인됐다.
- 테스트 9개를 추가해 전체 117개가 통과한다.
- 사용자 승인 아래 push했고, 시뮬레이션 PR에서 라벨 → Issue·보류 파일 생성, 라벨 제거 → 보류 파일 삭제를 확인했다.
- `docs/scripts/revise-loop.md`에 Claude 재작성 절차가 있다.
- 이 파일에 실행 결과가 덧붙고, 관련 문서가 갱신되고, 커밋됐다.

## 실행 결과 (Step 0~6, 2026-09-15)

> Step 0~6은 로컬 구현 기록이다. push와 CI 실측 결과는 아래 `실행 결과 (Step 7~9)`에 있다.

### 한 일

- **Step 0.** 새 문안을 작성해 `/humanize-korean`으로 점검했다(run `2026-09-15-003`, light, 변경률 0.0%, 게이트 exit 0). 제안 4건 중 1건을 반영했다. 사용자가 승인했다. 초안과 달라진 점은 Step 0 항목의 표에 있다.
- **Step 1.** 테스트 9개를 먼저 썼다. 구현 전 실행에서 4개가 단언 실패, 5개(`test_revise_request.py`)가 모듈 없음으로 실패했다 [확인].
- **Step 2.** `publish/revise_request.py`와 `templates/revise_request.md.j2`. 검토 날짜 찾기, 기존 요청으로 회차 계산, 권한 있는 코멘트만 사유로 싣기, 장마다 보이는 글자 추출, 처리 코멘트, `gh api --paginate` 응답 읽기.
- **Step 3.** `pipeline.py confirm()`이 `copy-hold.txt`가 있는 스냅샷을 거부한다. `publish/review_pr.py`가 보류 알림(`templates/review_pr_hold.md.j2`)을 본문 맨 위에, 문구 반려 절을 맨 끝에 붙인다.
- **Step 4.** `.github/workflows/revise.yml` 신규. `collect.yml`은 `revise-copy` 라벨을 만들고, 라벨이 남은 PR을 다시 만들 때 보류 파일을 넣는다. `publish.yml`의 거부 경고 문장에 문구 재작성 중을 더했다.
- **Step 5.** `docs/scripts/revise-loop.md`. 시작 조건, 사유 대응, 재작성 조건, 승인, 반영, 기록, 금지 사항.
- **Step 6.** 전체 테스트 **117개 통과** [확인]. 로컬 커밋.

### 실측 [확인]

- Task 5 시험 굽기의 실제 카드 5장과 게시문으로 요청 Issue 본문을 만들었다. 2회차 제목, 권한 없는 코멘트 제외, CRLF 코멘트의 줄 단위 인용, 장마다 보이는 글자, 게시문 원문이 모두 맞게 나왔다.
- 같은 실측에서 결함 1건을 찾아 고쳤다. 강조 태그(`<em>`)를 공백으로 바꿔 `전체 비교는 대시보드 에 있습니다`로 나왔다. 강조 태그는 공백 없이 지우고, 테스트에 단언을 더했다.
- 보류 파일이 있는 날의 검토 PR 본문은 경고 블록 → 검토 보고서 순서이고, 맨 끝에 문구 반려 절이 있다.

### 계획과 달라진 점

| 계획 | 실제 | 이유 |
|---|---|---|
| `next_round(issue_titles, day)` | `previous_requests(issues, day)` + `pending_day(root)` | 2회차부터 직전 요청 이후 코멘트만 싣기 위해 요청의 생성 시각이 필요하다. 검토 날짜는 PR 제목(사람이 고칠 수 있다) 대신 검토 브랜치의 파일로 찾는다 |
| 카드 글자는 `render_cards.visible_text` | `revise_request.card_texts` | `visible_text`는 줄 구분이 사라져 요청 Issue에서 읽기 어렵다. 블록 태그 단위로 줄을 나눈다 |
| `revise.yml`은 Issue·보류 파일까지 | 라벨을 붙이거나 뗄 때 PR 본문도 다시 만든다 | 보류 알림이 본문에 있으므로 본문을 다시 만들지 않으면 실제 상태와 어긋난다 |
| 보류 알림 템플릿은 `review_pr.md.j2` 안 | 별도 `templates/review_pr_hold.md.j2` | 알림은 검토 보고서 앞에, 나머지 절은 뒤에 붙는다 |
| `collect.yml`에 라벨 안내만 | 라벨 생성(`revise-copy`)과 보류 유지, `issues: write` 권한 추가 | 라벨이 저장소에 있어야 검토자가 붙일 수 있다. 권한을 명시하면 적지 않은 권한은 없어져 Issue 조회에 필요하다 |
| 라벨 설명 문구 | 설명 없이 색만 지정 | 라벨 설명도 사람이 읽는 문장이라 승인 문안이 필요하다(규칙 16). 이번 범위에 넣지 않았다 |

### 남은 위험 (CI 실측에서 확인)

- 사용자 계정으로 붙인 라벨이 `pull_request` `labeled` 실행을 만드는지 [미확인]. GITHUB_TOKEN이 만든 PR이라도 라벨을 붙인 주체가 사람이면 실행된다고 본다 [지식].
- `gh api --paginate` 출력 형식과 `gh issue create`가 표준 출력에 주소를 내는지 [지식]. 모듈은 이어 붙은 JSON 배열을 모두 읽는다.
- 같은 PR에서 수집 워크플로와 `revise.yml`이 동시에 검토 브랜치에 push하면 한쪽이 거부될 수 있다. 사람이 라벨을 붙이는 시각과 매일 수집(00:17 UTC)이 겹칠 때만 생긴다. 거부되면 라벨을 다시 붙인다.
- `collect.yml`이 보류를 유지할 때 넣는 요청 주소는 열린 `copy-revision` Issue 중 가장 최근 것이다. 검토 PR이 둘(정기·시뮬레이션) 동시에 반려되면 다른 PR의 요청 주소가 들어갈 수 있다. 보류 자체는 유지된다.

## 실행 결과 (Step 7~9, 2026-09-15)

### 한 일

사용자 승인("승인한다 ㄱㄱ") 아래 다섯 가지 외부 행동을 했다.

1. **main push.** 로컬 커밋 4개(`53d2464`, `7824239`, `5f8740f` 포함). 원격에 새 커밋이 없어 리베이스 없이 올렸고 해시가 바뀌지 않았다. 게시 워크플로가 push로 돌아 성공했다.
2. **시뮬레이션 수집 실행** (실행 34934793788, 65초, 성공). 검토 PR #5가 생겼다. 본문 맨 끝에 문구 반려 절이 있고, 저장소에 `revise-copy` 라벨이 만들어졌다.
3. **사유 코멘트 + 라벨** (실행 34934908620, 21초, 성공). 사용자 계정으로 시험 사유 코멘트를 남기고 `revise-copy`를 붙였다.
4. **라벨 제거** (실행 34934975510, 16초, 성공).
5. **정리.** 시험 Issue #6을 닫고(not planned), PR #5를 닫고 `review/simulated` 브랜치를 지웠다. 열린 PR·열린 요청 Issue·`review/` 브랜치가 모두 0건이다.

### 실측 [확인]

| 확인 항목 | 결과 |
|---|---|
| 사람이 붙인 라벨이 `pull_request` `labeled` 실행을 만드는가 | **만든다.** GITHUB_TOKEN이 만든 PR이어도 라벨을 붙인 주체가 사람이면 실행된다. 라벨 제거(`unlabeled`)도 같다 |
| 요청 Issue | #6 `문구 재작성 요청 2026-09-15 (1회차)`, 라벨 `copy-revision`. 사유 코멘트 원문과 작성 시각, 카드 5장의 장별 글자, 게시문 원문, 절차서 링크가 실렸다. `전체 비교는 대시보드에 있습니다`가 공백 없이 나왔다(Step 6에서 고친 결함) |
| 보류 파일 | 검토 브랜치에 `review: hold copy 2026-09-15 (round 1)` 커밋. `copy-hold.txt` 내용은 요청 Issue 주소다. `gh issue create`가 표준 출력에 주소를 낸다 |
| PR 본문 | 맨 위에 경고 블록과 `재작성 요청: …/issues/6`. 그 아래 시뮬레이션 안내와 검토 보고서가 이어진다 |
| 보류 해제 | `review: release copy hold 2026-09-15` 커밋, `copy-hold.txt` 404, 본문 맨 위 경고 블록이 사라졌다 |
| `gh api --paginate` 응답 | 모듈이 읽었다(코멘트 1쪽, 요청 Issue 0건 → 1회차) |

### 확인하지 못한 것

| 항목 | 이유 | 대신 확인한 것 |
|---|---|---|
| 라벨이 남은 PR을 매일 수집이 다시 만들 때 보류 파일을 다시 넣는가 | 수집 워크플로를 한 번 더 돌려야 한다. 승인 범위(시뮬레이션 1회)를 넘는다 | 워크플로 테스트(보류 파일을 커밋 전에 넣는다)와 셸 문법 검사. 실제 반려가 매일 수집과 겹치는 날 확인한다 |
| 4회차(상한) 흐름 | 요청 Issue를 세 번 더 만들어야 한다 | `test_round_counts_previous_requests_for_the_pending_day`, 상한 코멘트 스크립트 대조 테스트 |
| 머지했을 때 게시가 막히는가 | 시뮬레이션 스냅샷은 원래 승인되지 않아 CI 머지로는 구분이 안 된다(계획대로 머지하지 않았다) | `test_confirm_refuses_a_snapshot_on_copy_hold` |

### 막혔던 것

- 없음. CI 세 실행이 모두 첫 시도에 성공했다.

### 다음 Task에 넘기는 것

- **닫힌 시험 Issue #6도 회차에 들어간다.** 회차는 `copy-revision` 라벨과 제목의 날짜로 센다. 2026-09-15 날짜의 실제 검토 PR이 반려되면 2회차로 시작한다. 실제로 이 날짜에 다시 수집될 가능성은 낮다(매일 수집은 다음 날짜로 돈다).
- 문구 재작성은 실제 반려가 들어오면 `docs/scripts/revise-loop.md`대로 수행한다.
- 3-8 소개 카드는 문구 반려 절을 그대로 쓴다(카드나 게시문이 있는 날 출력).
