# Task 11: 변동 알림 (Phase 3 이후 운영 보강)

| 항목 | 내용 |
|---|---|
| 목적 | 가격이 바뀌어 검토 자료가 만들어지면 **사용자 메일로 알림이 가게 한다** |
| 계기 | 사용자 질문(2026-09-16): "변동이 있을 때마다 내 메일로 알림이 오는가" |
| 결정 | A안(담당자 지정)과 B안(저장소 구독)을 함께 적용한다. 2026-09-16 사용자 승인 |

## 배경: 지금은 알림이 가지 않는다 [확인]

| 확인한 것 | 결과 |
|---|---|
| 워크플로의 메일 발송 단계 | 없다. 알림 수단은 GitHub의 PR·Issue 알림뿐이다 |
| 저장소 구독자 수 | `subscribers_count: 0`. 소유자도 구독하지 않는다 |
| 검토 PR의 담당자·검토자 | 지정하지 않는다. 그래서 참여 알림이 생기지 않는다 |
| 최근 알림 기록 2건 | 모두 사람이 코멘트를 단 PR에 딸린 것이다(`reason: comment`) |
| 실제로 받은 메일 | `watch: All jobs have failed`. Actions **실패** 알림이며 구독과 무관한 경로다 |

정리하면 **실패는 알려 주고 정상 동작은 알려 주지 않는 상태**다.

## 목표

1. 봇이 검토 PR이나 알림 Issue를 열면 저장소 소유자가 담당자가 된다. 구독 설정과 무관하게 참여 알림이 발생한다.
2. 저장소를 구독해 두어 담당자 지정이 없는 활동도 알림 대상이 된다.

## 건드리는 파일

| 파일 | 바꾸는 것 |
|---|---|
| `.github/workflows/collect.yml` | 검토 PR 생성·갱신에 담당자를 지정한다 |
| `.github/workflows/watch.yml` | BigQuery 가격 페이지 변경 Issue, 수동 가격표 확인 Issue |
| `.github/workflows/publish.yml` | 시트 적재 실패 Issue |
| `.github/workflows/revise.yml` | 문구 재작성 요청 Issue |
| `tests/test_workflows.py` | 알림 지점을 빠뜨리지 않았는지 검사한다 |

## 인터페이스

- 계정 이름을 적지 않는다. `${{ github.repository_owner }}`를 단계 환경변수 `OWNER`로 받아 쓴다.
- 식(`${{ }}`)을 셸 명령에 직접 넣지 않는다. `revise.yml`은 기존 테스트가 이를 금지한다.
- 새 플래그: `gh pr create --assignee`, `gh pr edit --add-assignee`, `gh issue create --assignee`.

## 단계

1. 테스트를 먼저 쓴다. 알림이 생기는 다섯 지점에 담당자 지정이 있는지 검사한다.
2. 워크플로 네 개를 고친다.
3. 전체 테스트를 돌린다.
4. B안: 저장소 구독을 켠다. API로 되지 않으면 사용자가 웹에서 켠다.
5. 커밋하고 개인정보를 검사한다. push는 사용자 승인 뒤에 한다.

## 테스트

| 이름 | 확인 내용 |
|---|---|
| `test_bot_assigns_the_owner_so_notifications_reach_a_person` | 알림이 생기는 다섯 지점에 담당자 지정이 있다. 계정 이름을 적지 않고 `github.repository_owner`를 쓴다 |

기존 테스트 141개가 그대로 통과해야 한다. 특히 `revise.yml`의 셸 입력 금지 검사와 액션 SHA 고정 검사가 유지되어야 한다.

## 확인 방법

- 로컬: 테스트 통과, YAML 문법 통과.
- 원격: 다음 시뮬레이션 수집 실행에서 검토 PR의 담당자가 지정되는지 본다.
- 구독: `gh api repos/<소유자>/<저장소>` 의 `subscribers_count`가 1이 된다.

## 위험

| 위험 | 대응 |
|---|---|
| 담당자 지정 권한이 없어 명령이 실패한다 | 네 워크플로 모두 `issues: write`·`pull-requests: write`를 이미 가진다 [확인]. 실패하면 Actions 실패 알림으로 드러난다 |
| 이미 담당자로 지정된 PR을 갱신하면 알림이 다시 오지 않는다 | GitHub은 본문 수정으로 알림을 보내지 않는다. 검토 PR이 열린 채 며칠 뒤 새 변동이 겹치면 두 번째 알림이 없다. **한계로 기록한다**. 첫 알림은 정상적으로 가고, PR을 열면 최신 자료가 보인다 |
| 구독을 켜면 알림이 늘어난다 | 이 저장소의 Issue와 PR은 모두 봇이 만드는 운영 알림이다. 사람 협업자가 없다 |
| 계정 알림 설정에서 참여 메일이 꺼져 있다 | API로 읽을 수 없다 [미확인]. 사용자 확인에 맡긴다 |

## 완료 기준

- 알림이 생기는 다섯 지점에 담당자 지정이 들어간다.
- 테스트가 통과한다.
- 저장소 구독이 켜진다.
- 사용자에게 계정 알림 설정 확인 방법을 알린다.

---

# 실행 결과 (2026-09-16)

## 실제로 한 일

테스트를 먼저 쓰고 워크플로 네 개를 고쳤다. 알림이 생기는 다섯 지점 모두에 담당자를 지정한다.

| 파일 | 지점 | 바뀐 명령 |
|---|---|---|
| `collect.yml` | 검토 PR을 새로 열 때 | `gh pr create … --assignee "$OWNER"` |
| `collect.yml` | 열려 있는 검토 PR을 갱신할 때 | `gh pr edit … --add-assignee "$OWNER"` |
| `watch.yml` | BigQuery 가격 페이지 변경 Issue | `gh issue create --label price-watch --assignee "$OWNER"` |
| `watch.yml` | 수동 가격표 확인 요청 Issue | `gh issue create --label vendor-check --assignee "$OWNER"` |
| `publish.yml` | 시트 적재 실패 Issue | `gh issue create --assignee "$OWNER"` |
| `revise.yml` | 문구 재작성 요청 Issue | `gh issue create --label copy-revision --assignee "$OWNER"` |

`OWNER`는 `${{ github.repository_owner }}`를 환경변수로 받는다. 계정 이름을 워크플로에 적지 않고, 식을 셸 명령에 넣지 않는다.

## 확인한 값 [확인]

| 항목 | 값 |
|---|---|
| 테스트 | 141개 → **142개** 통과 |
| 저장소 구독 | `subscribed: true`, `ignored: false` |
| 구독자 수 | 0 → **1** |
| 기존 보안 검사 | 액션 SHA 고정, OIDC 범위, `revise.yml` 셸 입력 금지 모두 유지 |

B안은 API로 처리했다(`PUT /repos/{소유자}/{저장소}/subscription`). 웹에서 누를 필요가 없었다.

## 막혔던 것

- Bash heredoc 안의 파이썬 문자열에서 역슬래시가 한 겹 사라져 구문 오류가 났다. 역슬래시를 포함하지 않는 부분 문자열로 치환 대상을 바꿔 해결했다.
- **전체 테스트 첫 실행에서 `test_approved_change_publishes_cards_that_match_the_dashboard`가 1회 실패했다.** 카드 굽기 실패 1건으로 기록됐다. 같은 테스트를 단독으로 돌리면 통과하고, 전체를 다시 돌려도 142개가 모두 통과한다 [확인]. 워크플로 YAML 변경은 굽기 경로에 닿지 않으므로 이번 변경과 무관하다. 브라우저가 파일을 늦게 쓰는 기존 특성에서 온 간헐적 실패로 본다 [가정]. 재현되지 않아 원인을 좁히지 못했다. **다시 나타나면 굽기 대기 시간을 조사한다.**

## 계획과 달라진 점

없다. B안을 사용자가 웹에서 켜는 대신 API로 처리한 것이 유일한 차이다.

## 남는 한계

1. **열려 있는 검토 PR을 갱신할 때는 알림이 다시 가지 않는다.** GitHub은 본문 수정으로 알림을 보내지 않는다. 검토 PR을 열어 둔 채 며칠 뒤 새 변동이 겹치면 두 번째 알림이 없다. 첫 알림은 정상적으로 가므로 PR을 열면 최신 자료가 보인다.
2. **계정 알림 설정은 API로 읽을 수 없다** [미확인]. 참여 알림과 구독 알림의 메일 수신이 꺼져 있으면 담당자 지정과 구독 모두 효과가 없다. 사용자가 GitHub 알림 설정에서 확인한다.

## 다음 Task에 넘기는 것

- 다음 시뮬레이션 수집 실행에서 검토 PR 담당자가 실제로 지정되는지 본다.
- 첫 실제 가격 변동 때 메일 수신 여부를 확인 목록에 넣는다(`docs/tasks/phase3/task-9-e2e.md`).
