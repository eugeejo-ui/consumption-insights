# 과제 4-1 · CI 한글 글꼴과 줄바꿈

| 항목 | 내용 |
|---|---|
| 단계 | [Phase 4 CI 렌더링 정합](README.md) |
| 기간 | 2026-09-15 |
| 원본 기록 | `docs/tasks/phase3/task-5-pipeline-cards.md`(글꼴 확인), `docs/tasks/phase3/task-6-workflow.md`(글꼴 설치, CI 실측), `CLAUDE.md` 확인된 사실 |
| 코드 | `publish/render_cards.py`(`korean_font_available`, `bake` 첫 단계), `.github/workflows/collect.yml`(install Korean fonts 단계), `tests/test_workflows.py` |

## 세부 계획

**목표:** CI에서 굽는 정기 카드가 로컬에서 승인한 디자인과 같은 품질이 되게 한다.

| 위험 | 근거 | 대응 계획 |
|---|---|---|
| CI에 한글 글꼴이 없어 두부 글자 카드가 된다 | CI `fc-list :lang=ko` 0개, 설치 전 굽기에서 모든 한글이 두부 글자 [확인 2026-09-12] | ① 굽기 전에 한글 글꼴을 확인하고, 없으면 굽지 않고 실패로 기록한다(3-5). ② 워크플로에 `fonts-noto-cjk` 설치를 **pytest보다 먼저** 둔다(3-6) |
| 레이아웃 검사가 두부 글자를 잡지 못한다 | 두부 글자도 폭과 줄 수는 정상으로 잰다 | ①이 브라우저를 부르기 전에 막는다 |
| 글꼴 목록 끝의 `Noto Sans CJK KR`이 라틴 글자까지 그리는지 | Task 4 조정안 6 [미확인] | CI 산출물로 확인한다 |
| CI 글꼴에서 리드가 늘어 각주·알약과 겹친다 | 2-2 인계 | 레이아웃 검사가 CI에서도 돈다. 요약(가장 좁은 여백)을 기록한다 |
| 카드 실패가 검토 자료를 막는다 | 카드는 부가물이다 | 굽기 실패는 `card-errors.txt`에 남기고 검토 PR은 그대로 연다 |

## 결과

### 글꼴 확인 (3-5)

- `korean_font_available()`: Windows·macOS는 참(맑은 고딕·Apple SD Gothic Neo 기본 탑재 [지식]), Linux는 `fc-list :lang=ko` 결과가 비어 있지 않을 때만 참.
- `bake()`가 맨 먼저 확인하고, 없으면 `한글 글꼴이 없다. 두부 글자 카드를 만들지 않는다(fonts-noto-cjk 설치 필요)`로 멈춘다.
- 글꼴 없음을 흉내 낸 실행에서 검토 자료는 그대로 남고, 카드 폴더는 만들어지지 않고, 사유가 `card-errors.txt`에 남았다 [확인].
- 실제 굽기 테스트는 브라우저나 한글 글꼴이 없으면 건너뛴다.

### 글꼴 설치 (3-6)

```yaml
- name: install Korean fonts   # pytest와 1단계보다 먼저
  run: |
    sudo apt-get update
    sudo apt-get install -y --no-install-recommends fonts-noto-cjk
    fc-list :lang=ko family | sort -u
```

순서는 테스트로 고정했다(글꼴 설치가 pytest와 `pipeline.py`보다 앞).

### CI 실측 [확인] (실행 34931680729, 시뮬레이션 검토 PR #4)

| 항목 | 결과 |
|---|---|
| 글꼴 설치 | 18초. `fc-list`에 `Noto Sans CJK KR`이 있다 |
| pytest | 실제 굽기 테스트 포함 통과 |
| 카드 5장 굽기 | 1단계 10초. `레이아웃 검사 통과: 5장, 가장 좁은 여백 151px, 가장 오른쪽 글자 끝 1028/1032px` |
| 두부 글자 | 없음. **한글과 라틴 글자 모두 Noto 계열**로 그려졌다(조정안 6 해소) |
| 줄바꿈 차이 | 차트 장 리드와 마무리 장 리드가 로컬(맑은 고딕)은 두 줄, CI(Noto Sans CJK)는 한 줄. **CI 한글 글자 폭이 더 좁다** |
| `1028/1032px` | 넘침이 아니다. 마무리 장 리드 한 줄이 본문 폭을 꽉 채운 값이다 |
| 사소한 차이 | Noto의 가운뎃점(`·`) 앞뒤 여백이 맑은 고딕보다 넓다. 읽기에는 지장이 없다 |

## 계획과 달라진 점

| 계획 | 실제 | 이유 |
|---|---|---|
| 레이아웃 검사는 통과·실패만 | 통과 시 요약을 돌려주고 한 줄 출력한다 | CI 기록에서 여유(가장 좁은 여백, 가장 오른쪽 글자 끝)를 확인한다 |
| 글꼴 설치는 카드를 굽는 1단계 앞 | pytest보다도 앞 | CI pytest의 실제 굽기 테스트가 두부 글자로 돌지 않게 한다 |

## 남긴 것

- 게시 워크플로(`publish.yml`)에는 글꼴을 설치하지 않는다. 사이트에는 수집 단계에서 구운 카드를 복사만 한다. 그래서 그 CI의 실제 굽기 테스트는 건너뛴다(설계대로).
- 로컬 미리보기(맑은 고딕)와 게시물(Noto)의 줄바꿈이 다르다는 문제가 남았다(→ 5-2).
