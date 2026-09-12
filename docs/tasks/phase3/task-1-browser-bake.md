# Phase 3 · Task 1: 브라우저로 굽기 실측

| 항목 | 내용 |
|---|---|
| 상태 | **로컬 실측 완료. CI 실측은 push 승인 대기** (2026-09-12) |
| 상위 계획 | `docs/plans/phase3-linkedin-cardnews.md` Task 1, 결정 D8 |
| 담당 | C (사용자 확인 2회: 시험 카드 눈으로 확인, CI 실측 push 승인) |

## 목표

HTML을 **설치된 브라우저로 구워** 1080×1350 PNG와 PDF를 만드는 방식이 실제로 되는지 확인한다. **이 Task의 산출물은 판단 근거이지 카드가 아니다.** 여기서 막히면 뒤의 Task 전부가 무너지므로 코드를 많이 쓰기 전에 먼저 확인한다.

확인할 것은 네 가지다.

1. 로컬(Windows·Edge 또는 Chrome)에서 구워지는가
2. CI 서버(ubuntu-latest)에서 구워지는가
3. **한글이 네모(두부)로 나오지 않는가** — 양쪽 모두
4. 그라데이션·라운드·CSS 막대가 제대로 그려지는가

실패하면 **멈추고 보고한 뒤** Playwright 안으로 갈지 다시 묻는다. 혼자 대안을 밀어붙이지 않는다.

## 건드리는 파일

| 파일 | 동작 |
|---|---|
| `publish/browser.py` | 신규. 브라우저 탐색, 스크린샷, PDF |
| `tests/test_browser.py` | 신규. 테스트 3개 |
| `.github/workflows/probe-browser.yml` | 신규(임시). 확인 후 **삭제한다** |
| `docs/tasks/phase3/task-1-browser-bake.md` | 이 파일. 실행 후 결과를 덧붙인다 |
| `CLAUDE.md` | "확인된 사실"에 실측값을 `[확인]`으로 추가 |

시험용 HTML과 구운 이미지는 **스크래치 폴더**에 만든다. 저장소에 남기지 않는다.

## 인터페이스

```python
find_browser() -> str
    # 환경변수 BROWSER_BIN이 있고 그 파일이 있으면 그것을 쓴다.
    # 없으면 CANDIDATES를 순서대로 찾는다. 하나도 없으면 RuntimeError.

screenshot(html: Path, out: Path, width: int = 1080, height: int = 1350) -> Path
print_pdf(html: Path, out: Path) -> Path
```

호출은 임시 프로필(`--user-data-dir`)로 한다. **사용자의 브라우저 프로필과 로그인 세션을 건드리지 않기 위해서다.** 이 점은 규칙 9·12와도 맞닿아 있다.

## 단계

- [x] **Step 1** 테스트 3개를 먼저 쓴다(실패 확인)
- [x] **Step 2** `publish/browser.py`를 구현한다 → 테스트 3개 통과, 전체 60개 통과
- [x] **Step 3** 시험용 HTML 1장을 스크래치에 만든다
  - 담을 것: 한글 초대형 제목, 그라데이션 단어, 회색 본문, 라운드 카드, CSS 막대 4개, 상·하단 바
  - **외부 요청 0건**으로 만든다(글꼴은 시스템 스택)
- [x] **Step 4** 로컬에서 PNG와 PDF를 굽는다
  - PNG 크기를 PNG 헤더(IHDR)에서 직접 읽어 1080×1350인지 확인한다(Pillow를 쓰지 않는다)
  - PDF 쪽수를 바이트에서 확인한다
  - **사용자에게 PNG를 보내 눈으로 확인받는다**
- [x] **Step 5** CI 실측용 임시 워크플로를 만든다(작성 완료, push 대기)(`workflow_dispatch` 전용)
  - `google-chrome --version`, `chromium --version` 확인
  - `fc-list :lang=ko` 로 한글 글꼴 유무 확인
  - 같은 HTML을 굽고 아티팩트로 올린다
  - 글꼴이 없으면 `sudo apt-get install -y fonts-noto-cjk`를 넣고 다시 확인한다
  - **push는 외부로 나가는 행동이라 사용자 승인을 받는다**(규칙 4)
- [ ] **Step 6** 아티팩트를 받아 확인한다. 로컬 결과와 눈으로 비교한다
- [ ] **Step 7** 임시 워크플로를 삭제한다
- [ ] **Step 8** 실측값을 이 파일과 `CLAUDE.md`에 `[확인]`으로 적고 커밋한다

## 테스트 목록

| # | 이름 | 확인하는 것 |
|---|---|---|
| 1 | `test_env_var_wins` | `BROWSER_BIN`이 후보 목록보다 우선한다 |
| 2 | `test_no_browser_raises` | 후보가 없으면 `RuntimeError`가 나고, 메시지에 "브라우저"가 들어간다 |
| 3 | `test_bakes_a_png_of_the_right_size` | 실제로 구운 PNG가 1080×1350이다. **브라우저가 없는 환경에서는 건너뛴다**(`skipif`) |

**상위 코드 계획과 달라지는 점:** 계획서에는 테스트 2개(+2 → 59)로 적었으나 3개(+3 → 60)로 늘린다. 실제 굽기를 검증하는 테스트가 있어야 CI에서도 회귀를 잡을 수 있다. 브라우저가 없는 환경에서는 자동으로 건너뛰므로 다른 곳에 영향이 없다.

## 확인 방법 (증거)

| 확인 항목 | 방법 |
|---|---|
| PNG 크기 | PNG 헤더 16~24바이트를 `struct.unpack(">II", ...)`로 읽는다 |
| PDF 쪽수 | `/Type /Page` 개수를 센다 |
| 한글 표시 | **사람이 눈으로 본다.** 자동 판정은 하지 않는다(두부 글자도 픽셀은 그려진다) |
| CI 브라우저·글꼴 | 워크플로 로그의 `--version`과 `fc-list` 출력 |
| 그라데이션·막대 | 사람이 눈으로 본다 |

## 위험과 대비

| 위험 | 대비 |
|---|---|
| `--headless=new`를 지원하지 않는 버전 | `--headless`로 한 번 더 시도한다 |
| `--no-pdf-header-footer`를 지원하지 않는 버전 | `--print-to-pdf-no-header`로 한 번 더 시도한다 |
| 스크린샷이 흰 화면으로 나온다(렌더 전 촬영) | `--virtual-time-budget`을 늘리고 `--run-all-compositor-stages-before-draw`를 붙인다 |
| 기업 정책이나 보안 제품이 헤드리스 실행을 막는다 | Edge → Chrome 순서로 시도한다. 둘 다 막히면 **멈추고 보고한다** |
| CI 서버에 한글 글꼴이 없다 | `fonts-noto-cjk`를 설치한다. 설치가 필요하면 Task 5의 워크플로에도 넣는다 |
| 로컬과 CI의 글꼴이 달라 줄바꿈이 어긋난다 | 두 결과를 나란히 비교한다. 차이가 크면 Task 3에서 글자 수 상한을 보수적으로 잡는다 |
| 임시 워크플로를 지우지 않고 남긴다 | Step 7을 완료 기준에 넣는다 |

## 완료 기준

- 로컬에서 1080×1350 PNG와 카드 장수만큼의 PDF 쪽이 나오고, 한글과 그라데이션이 정상이다(사용자 확인).
- CI 서버에서도 같은 결과가 나온다.
- 테스트 60개가 통과한다.
- 임시 워크플로가 저장소에 남아 있지 않다.
- 실측값이 이 파일과 `CLAUDE.md`에 `[확인]` 표기로 남는다.

---

## 실행 결과

### 로컬 실측 (완료, 2026-09-12)

| 확인 항목 | 결과 |
|---|---|
| 브라우저 | Edge를 찾았다(`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`). Chrome은 설치돼 있지 않다 |
| PNG | 1080×1350 [확인] |
| PDF | 카드 한 장이 PDF 한 쪽이 된다. 5장 → 5쪽 [확인] |
| 한글 | 정상. Malgun Gothic으로 렌더링된다 [확인] |
| 그라데이션·라운드·CSS 막대 | 정상 [확인] |
| 옵션 | `--headless=new`와 `--no-pdf-header-footer`가 모두 동작한다 [확인] |
| 테스트 | 60개 통과 |

커밋: `8d24c48`

**계획과 달라진 점**
- 테스트를 2개가 아니라 3개 만들었다. 실제로 구운 PNG의 크기를 확인하는 테스트를 넣어야 회귀를 잡을 수 있다. 브라우저가 없는 환경에서는 건너뛴다.
- PDF 쪽수를 셀 때 `/Type /Pages` 노드까지 세어 5쪽을 6쪽으로 잘못 읽었다. 정규식을 `/Type\s*/Page(?![s])`로 고쳤다.

**Task 4로 넘기는 것**
- 104px 제목은 한 줄에 약 10자가 들어간다. 그 이상은 넘친다. 상한을 `docs/scripts/cards-script.md` 4절에 표로 고정했다.
- 내용이 적은 장은 아래쪽 여백이 크다. 본문 블록의 수직 위치 조정이 필요하다.

### CI 실측 (대기)

`.github/workflows/probe-browser.yml`을 만들어 두었다. push 승인을 받으면 실행한다. 확인 항목은 서버의 브라우저 유무, 한글 글꼴 유무, `fonts-noto-cjk` 설치 전후 비교다. 확인 후 워크플로를 삭제한다.
