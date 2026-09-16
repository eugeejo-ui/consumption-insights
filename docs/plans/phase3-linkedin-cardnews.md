# Phase 3: LinkedIn 카드뉴스 자동 생성 Implementation Plan

> **상태: 승인 대기** (2026-09-12 작성). 승인 전에는 구현하지 않는다(규칙 1).
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 가격이 의미 있게 바뀐 날(E1) 카드뉴스 이미지와 LinkedIn 게시문을 자동으로 만든다. 검토 PR에서 카드를 미리 보고, 머지(컨펌)하면 사이트에 게시된다. **게시 버튼은 사람이 누른다**(LinkedIn 약관).

**Architecture:**
- `publish/card_data.py`가 `events.json`과 계산 결과를 카드 장별 데이터(사전 목록)로 바꾼다. **장수는 고정하지 않는다.** 변동 항목을 전부 실을 때까지 늘린다(규칙 18). 최소 4장이다. `가정과 산출 근거` 장은 만들지 않는다(D16).
- `templates/cards/cards.html.j2`가 한 파일 안에 모든 장을 그린다. 한 장은 1080×1350 블록이다. 디자인은 `docs/plans/phase3-card-design.md`를 따른다.
- `publish/browser.py`가 설치된 브라우저를 명령줄로 호출해 PNG와 PDF를 굽는다. **새 파이썬 패키지를 추가하지 않는다.**
- `publish/render_cards.py`가 위를 엮어 `data/raw/<날짜>/cards/`를 채운다.
- `publish/render_linkedin.py`가 게시문 `linkedin.md`를 만든다. 글 초안(`post.md`)과 달리 짧고, 아카이브 링크와 해시태그가 붙는다.
- 카드와 게시문의 모든 숫자는 `render_post.check_numbers`로 `events.json`과 대조한다. 어긋나면 중단한다.
- `collect.yml`이 검토 PR에 카드를 보여 주고, `publish.yml`이 머지 후 `site/cards/`로 옮겨 게시한다.

**Tech Stack:** Python 3.11, Jinja2, pytest, 설치된 Chromium 계열 브라우저(Edge·Chrome), GitHub Actions. **새 의존성 없음.**

**Spec:** `CLAUDE.md` Phase 3과 규칙 4·9·10·11·13·14·15·16·17, `docs/phases/phase-3-linkedin.md`, `docs/plans/phase3-card-design.md`

## 결정 (2026-09-12 사용자 확인)

| # | 결정 | 이유 | 대안 |
|---|---|---|---|
| D7 | 게시 방식은 **A안**이다. 카드와 게시문까지 자동으로 만들고, 업로드와 게시는 사람이 한다 | LinkedIn API 약관 3.1(26)과 사용자 약관 13번이 자동 게시를 금지한다 [확인]. 기존 A'안(공식 공유 링크)은 URL 하나만 공유하는 창이라 이미지 여러 장을 붙일 수 없다 [지식] | B 공식 API(회색지대 + 60일 토큰), C 제외 |
| D8 | 카드는 **설치된 브라우저를 직접 호출**해 굽는다(`--screenshot`, `--print-to-pdf`) | 새 파이썬 패키지가 없고, PNG와 PDF를 한 도구로 만든다. 임의의 디자인을 HTML/CSS로 재현할 수 있다 | Playwright + Chromium(확실하지만 로컬·CI에 100~150MB), Pillow 직접 그리기(재현도가 낮다) |
| D9 | 카드는 **수집 단계에서 만들어 검토 PR에 보여 주고**, 머지 후 사이트에 게시한다 | 사용자가 머지 전에 문구와 그림을 함께 확인한다. 게시(공개)는 컨펌 이후라 규칙 14를 지킨다 | 머지 후에만 생성(미리 볼 수 없다), 아티팩트로만 내려받기(폰에서 번거롭다) |
| D10 | 좌측 상단은 **프로젝트 이름만** 넣는다 | 사용자 결정. 카드 이미지에 개인 정보를 남기지 않는다 | 실명, 실명+프로젝트 이름 |
| D11 | 장수를 고정하지 않는다. **정기는 최소 4장, 소개는 4장**이다(→ D20으로 각각 5장) | 변동 항목을 전부 실어야 한다(D15). 고정하면 항목이 잘리거나 빈 장이 생긴다 | 고정 4장, 고정 5장 |
| D12 | 템플릿의 **사진 자리는 데이터 블록으로 대체**한다 | 쓸 사진이 없고 타사 이미지·상표를 쓰지 않는다(2026-09-12 결정) | 사진 구입·생성(비용과 저작권 부담) |
| D14 | 문구 반려는 검토 PR의 `revise-copy` 라벨로 받는다. 워크플로는 재작성 요청 Issue까지 만들고, 재작성은 Claude가 `/humanize-korean`으로 수행한다. 상한 3회 | `/humanize-korean`은 Claude 스킬이라 Actions 안에서 실행되지 않는다 [확인]. 전면 자동화는 **보안 점검 후 사용자가 기각했다** — 키를 쥔 작업에 외부 텍스트와 제3자 스크립트가 함께 들어간다 | Actions에서 Claude 실행(유출 위험), 수동 재작성(마찰이 크다) |
| D15 | **항목을 생략하지 않는다.** 한 장에 담기지 않으면 같은 종류의 장을 늘려 전부 싣는다(규칙 18). D13(5줄로 자르고 `외 N건`)은 폐기한다 | 카드뉴스의 목적은 정보 전달이다. `외 N건`은 읽는 사람을 대시보드로 보낼 뿐 정보를 주지 않는다 | 자르기(정보 누락), 글자 축소(가독성 저하) |
| D18 | 차트 장에 **미국 리전·서울 리전을 병기**한다. 대표로 고르는 것은 시나리오 하나다 | 리전 하나만 고르면 서울 리전이 구조적으로 빠진다. 한국어 독자에게 관련성이 높고, T2(서울 프리미엄)가 그림으로 드러난다. 장수는 늘지 않는다 | 리전마다 차트 1장(+1장), 서울 프리미엄 고정 장(+1장) |
| D20 | 모든 카드뉴스의 **마지막 장에 마무리 안내 장**을 둔다. 정기는 최소 5장, 소개는 5장이다(D11 갱신) | 사용자 결정(2026-09-15). 카드뉴스를 안내로 끝맺고, 카드에 싣지 않는 비교 전체와 산출 근거의 위치를 알린다. 변동 항목은 앞 장에 전부 싣는다 | 마무리 장 없음(하단 알약 주소만) |
| D21 | 소개 카드는 **로컬에서 굽고**, 사용자가 대화에서 실물을 승인한 뒤 push한다. 게시 워크플로가 `site/cards/intro/`로 복사한다 | 사용자 결정(2026-09-15, 권고안). 한 번 만드는 게시물이고 숫자는 이미 승인된 스냅샷에서 온다. 대화의 실물 승인이 체크포인트다 | CI 워크플로가 굽고 검토 PR로 확인(새 워크플로·PR 문안·반려 루프 수정이 필요) |
| D22 | 카드 글꼴 목록에 **`Noto Sans KR`을 `Malgun Gothic` 앞에** 넣는다 | 사용자 결정(2026-09-15, 권고안). 맑은 고딕에서 확정 표지 제목이 3줄(상한 2줄)로 넘치고 Noto Sans KR로는 2줄에 들어간다 [확인]. 로컬도 CI(Noto Sans CJK KR)와 같은 Noto 계열로 굽는다. CI 출력은 바뀌지 않는다 | 표지 제목 단축(문안 재승인, 글꼴 차이는 남는다) |
| D23 | 카드 PDF는 **구운 PNG를 한 쪽에 한 장씩 실어** 만든다. `bake()`는 이미지 수가 장수와 다르거나 소프트 마스크가 남은 PDF를 거부한다 | 사용자 결정(2026-09-15, A안). 카드 HTML을 바로 인쇄하면 그라데이션 강조 문구가 소프트 마스크로 기록되어 보기 프로그램에서 문구를 감싸는 테두리선이 보인다 [확인]. PNG와 PDF의 모습이 같아진다 | 강조 단색화(승인 디자인 변경), SVG 글자(템플릿·레이아웃 검사 대규모 수정) |
| D24 | 소개 카드에 **가설과 시나리오를 싣지 않는다.** 4장은 플랫폼별 현재 순위와 두 리전 월 사용료를 싣고, 각주 아래 작은 글자로 비교 기준을 밝힌다. 두 리전 순서가 다르면 생성을 멈춘다 | 사용자 결정(2026-09-16). 사전 정보가 없는 LinkedIn 독자에게 가설 기호는 뜻이 전달되지 않는다 | 가설 설명을 카드에 더하기(장수와 집중력 부담), 시나리오마다 한 장씩(같은 순서가 세 번 반복) |
| D25 | 소개 카드에 **리전 비교 두 종류**를 더한다(`서울 리전 단가 차이` 5개씩 두 장, `서울 리전 월 사용료` 한 장). 소개 카드는 8장이다 | 사용자 결정(2026-09-16, 권고안). 한국 독자에게 리전 차이가 가장 가까운 사실인데 카드에서 빠져 있었다. 단가 차이는 +35.7%에서 -3.8%까지 갈린다 [확인] | 컴퓨트 4개만 싣기(스토리지의 반례가 사라진다), 6개만 싣기(항목 3개 누락) |

## 한눈에 보기 (사용자용 요약)

| Task | 만드는 것 | 테스트(누적) | 사용자가 할 일 |
|---|---|---|---|
| 1 | **실측.** 브라우저로 PNG·PDF 굽기, 한글 표시, CI 서버 확인 | +5 → 62 (결함 수정 테스트 2개 포함) | — |
| 2 | **카드 스크립트 작성**(규칙 16). 확정 문안 + `/humanize-korean` 점검 | — | **문안 승인** |
| 3 | **완료** (2026-09-15, `9f50492`). 카드 데이터 `publish/card_data.py`(정기), 게시문 `publish/render_linkedin.py` | +17 → 79 | 보완 문안 승인 |
| 4 | **완료** (2026-09-15, `88174ca`). 카드 HTML 템플릿(디자인 적용) + 굽기 `publish/render_cards.py` | +13 → 92 | 카드 실물 확인(승인) |
| 5 | **완료** (2026-09-15, `b2c8576`). `pipeline.py` 연결(`--cards`), 1단계에서 자동 생성, 승인된 카드 사이트 복사 | +9 → 101 | — |
| 6 | **완료** (2026-09-15, `d72560e`). 워크플로: 검토 PR에 카드 표시, 머지 후 사이트 게시 | +7 → 108, CI 실측 | push·시뮬레이션 승인 |
| 7 | **완료** (2026-09-15, `5f8740f`). **문구 반려 재작성 루프**(규칙 16). `revise.yml` + 재작성 절차 + 게시 보류(`copy-hold.txt`) | +9 → 117, CI 실측 | 새 문안 승인, push·실측 승인, 반려 시 사유 코멘트 + 라벨 1개 |
| 8 | **완료** (2026-09-15, `cb2db9f`). 소개 카드 5장 + 소개 게시문, `pipeline.py --cards intro`(D21 로컬 굽기, D22 글꼴) | +10 → 127, 게시 확인 | 4장 보완 문안 승인, 카드 실물 승인, push 승인 |
| 9 | **완료** (2026-09-15, `935172d`). 종단 검증: 승인 경로 통합 테스트, 시트 중복 적재 수정, CI 시나리오(재수집·보류 유지·보류 중 머지 거부·미승인 카드 미게시) | +2 → 129, CI 실측 | push·CI 시나리오 승인 |
| 10 | **첫 게시.** 게시 전 수정 4건: 카드 PDF를 구운 PNG로 조립(D23, `a5af3a8`), 소개 4장을 플랫폼별 현재 순위로(D24), 게시문 도입 문단, 리전 비교 두 장 신설(D25) | +9 → 139 | 수정안·문안·실물 승인, push 승인, **LinkedIn에 직접 게시** |

## Global Constraints

- Windows + PowerShell이다. venv는 `.venv\Scripts\python.exe`를 직접 호출하고, 한글을 출력할 때는 `$env:PYTHONIOENCODING='utf-8'`을 설정한다.
- **LinkedIn에 자동으로 접근하거나 게시하지 않는다.** 브라우저 자동화로 우회하지 않는다(규칙 9). 코드에 LinkedIn API 호출을 넣지 않는다.
- 카드 HTML에 **외부 요청이 하나도 없어야 한다.** `<img>`, `<link>`, `@import`, `url()`을 쓰지 않는다. 글꼴은 시스템 글꼴 스택만 쓴다.
- 타사 로고와 원본 템플릿의 사진·일러스트를 쓰지 않는다. `_workspace/card-template/`의 파일을 저장소로 옮기지 않는다.
- 카드와 게시문의 모든 숫자는 `events.json`에 있어야 한다(표시 반올림 허용).
- **항목을 생략하지 않는다**(규칙 18). 한 장에 담기지 않으면 장을 늘린다. 누락 검사를 코드로 강제한다.
- 사용자에게 보이는 한국어는 격식 있는 문어체다(규칙 17). 문안은 규칙 16의 스크립트 단계를 거친다. 용어 고정: 채택·기각, 작성일, 미국 리전·서울 리전.
- **카드 문안에 한해 `월 사용료`를 쓴다**(D17). 게시문·대시보드·규칙 17의 `월 비용`은 다른 대화에서 바꾼다.
- 카드 생성이 실패해도 **검토 PR은 열려야 한다.** 카드는 부가물이고 검토를 막으면 안 된다.
- 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`을 붙인다. 한 번에 Task 하나만 하고 보고한 뒤 멈춘다(규칙 10).

## File Structure

```
publish/browser.py                 # Task 1: 브라우저 탐색, 스크린샷·PDF 호출
publish/card_data.py               # Task 3: events → 카드 장별 데이터 / Task 8: 소개 카드
publish/render_linkedin.py         # Task 3: 게시문
templates/post_linkedin.md.j2      # Task 3
templates/cards/cards.html.j2      # Task 4: 카드 HTML(모든 장)
publish/render_cards.py            # Task 4: HTML 생성 + 굽기
pipeline.py                        # Task 5: --cards 추가, 1단계 연결 / Task 6: --build에서 site/cards 복사
.github/workflows/collect.yml      # Task 6: 카드 생성 단계, PR 본문에 카드 표시
.github/workflows/publish.yml      # Task 6: (변경 없음. --build가 복사를 맡는다)
tests/test_browser.py              # Task 1
tests/test_card_data.py            # Task 3, 6
tests/test_render_linkedin.py      # Task 3
tests/test_render_cards.py         # Task 4
tests/test_pipeline.py             # Task 5: 단언 추가
```

## 산출물 폴더

```
data/raw/<날짜>/cards/
    cards.html        # 모든 장이 들어 있는 원본. 텍스트 변경이 git diff에 보인다
    01-cover.png … NN-rank.png
    cards.pdf         # 같은 장을 묶은 캐러셀용 문서
data/raw/<날짜>/linkedin.md        # 게시문
data/cards/intro/                  # 소개 카드(날짜와 무관). Task 8
site/cards/<날짜>/                 # 게시 후 복사본(빌드 산출물, 커밋하지 않는다)
site/cards/intro/
```

---

### Task 1: 브라우저로 굽기 실측 (`publish/browser.py`)

이 Task는 **되는지 확인하는 것이 목적**이다. 실패하면 멈추고 보고한 뒤 Playwright 안을 다시 여쭙는다.

**Files:**
- Create: `publish/browser.py`, `tests/test_browser.py`

**Interfaces:**
- `find_browser() -> str` — 실행 파일 경로. 환경변수 `BROWSER_BIN`이 있으면 그것을 먼저 쓴다. 없으면 후보를 순서대로 찾는다. 하나도 없으면 `RuntimeError`
- `screenshot(html: Path, out: Path, width: int = 1080, height: int = 1350) -> Path`
- `print_pdf(html: Path, out: Path) -> Path`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_browser.py`:
```python
import pytest

from publish import browser


def test_env_var_wins(monkeypatch, tmp_path):
    fake = tmp_path / "my-browser.exe"
    fake.write_text("")
    monkeypatch.setenv("BROWSER_BIN", str(fake))
    assert browser.find_browser() == str(fake)


def test_no_browser_raises(monkeypatch):
    monkeypatch.delenv("BROWSER_BIN", raising=False)
    monkeypatch.setattr(browser, "CANDIDATES", [])
    with pytest.raises(RuntimeError, match="브라우저"):
        browser.find_browser()
```

- [ ] **Step 2: 구현**

```python
"""설치된 Chromium 계열 브라우저를 명령줄로 호출해 HTML을 PNG·PDF로 굽는다.
새 파이썬 패키지를 쓰지 않기 위한 선택이다(결정 D8). 브라우저가 없으면 분명한 메시지로 실패한다."""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
]
COMMON = ["--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
          "--force-device-scale-factor=1", "--virtual-time-budget=3000"]


def find_browser() -> str:
    chosen = os.environ.get("BROWSER_BIN")
    if chosen and Path(chosen).exists():
        return chosen
    for path in CANDIDATES:
        if Path(path).exists():
            return path
    raise RuntimeError("브라우저를 찾지 못했다. Edge나 Chrome을 설치하거나 BROWSER_BIN에 경로를 지정한다.")


def _run(args: list[str]) -> None:
    with tempfile.TemporaryDirectory() as profile:          # 사용자 프로필을 건드리지 않는다
        subprocess.run([find_browser(), *COMMON, f"--user-data-dir={profile}", *args],
                       check=True, capture_output=True, timeout=120)


def screenshot(html: Path, out: Path, width: int = 1080, height: int = 1350) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    _run([f"--window-size={width},{height}", f"--screenshot={out}", Path(html).resolve().as_uri()])
    return out


def print_pdf(html: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    _run(["--no-pdf-header-footer", f"--print-to-pdf={out}", Path(html).resolve().as_uri()])
    return out
```

- [ ] **Step 3: 실제 실측 (로컬)**

임시 HTML 한 장(한글 제목 + 그라데이션 단어 + 막대 3개)을 스크래치 폴더에 만들고 굽는다.
- 확인: PNG가 정확히 1080×1350인가, 한글이 네모로 나오지 않는가, 그라데이션이 보이는가, PDF가 1장 나오는가
- `--no-pdf-header-footer`가 없는 버전이면 `--print-to-pdf-no-header`로 바꿔 다시 시도한다
- **결과를 이 문서와 `CLAUDE.md`의 "확인된 사실"에 [확인] 표기로 적는다**

- [ ] **Step 4: 실제 실측 (CI 서버)**

임시 워크플로(`workflow_dispatch` 전용)로 ubuntu-latest에서 같은 것을 굽고 아티팩트로 받는다.
- 확인: 브라우저가 preinstall 돼 있는가(`google-chrome --version`), 한글 글꼴이 있는가
- 없으면 `sudo apt-get install -y fonts-noto-cjk`를 넣고 다시 확인한다
- 확인 후 임시 워크플로는 지운다

- [ ] **Step 5: 커밋**

`feat: bake cards with the installed browser`

---

### Task 2: 카드 스크립트 작성 (규칙 16)

**이 Task에는 코드가 없다.** 사람이 읽을 문장을 먼저 확정한다. 문안을 확정하지 않은 채 템플릿을 만들면 어조가 어긋난 문장이 코드에 박힌 뒤에 발견된다.

**Files:** Create `docs/scripts/cards-script.md`, `docs/scripts/linkedin-post-script.md`

**담을 것**
- 소개 4장과 정기 카드의 **장별 확정 문안**
- 고정 문안과 **자리표시자**(`{작성일}`, `{플랫폼}`, `{전}`, `{후}`, `{변화율}`)를 구분해 표기
- 표지 제목 생성 규칙 세 가지 경우의 실제 문장
- 항목이 많은 날의 **장 분할 규칙과 쪽 표시**(`(1/2)`). 생략 문구는 쓰지 않는다(규칙 18)
- LinkedIn 게시문 전문
- 장 종류별 **제목 최대 글자 수**. Task 1에서 104px 제목이 카드 폭을 거의 채우는 것을 확인했다

**어조 규정 (규칙 16)**
- executive 보고체. 결론을 먼저, 근거를 뒤에 둔다.
- 구어체를 배제한다. 말 걸기, 감탄, 권유형 어미, 대화체 연결어를 쓰지 않는다.
- 한 문장에 한 가지 사실만 담는다.
- 용어 고정(규칙 17): 채택·기각, 작성일, 미국 리전·서울 리전, 월 비용이 낮은 순서.

- [ ] **Step 1** 초안을 쓴다
- [ ] **Step 2** `/humanize-korean`으로 점검하고 결과를 문서에 남긴다
- [ ] **Step 3** 시험 카드로 구워 글자가 넘치지 않는지 확인한다
- [ ] **Step 4** **사용자 승인.** 승인 전에는 Task 3으로 넘어가지 않는다
- [ ] **Step 5** 커밋 — `docs: fix the card script before automating it`

**완료 기준:** 모든 장의 문안이 확정되고, 구어체가 없으며, 사용자가 승인했다.

---

### Task 3: 카드 데이터와 게시문 (디자인과 무관한 부분)

> **완료 (2026-09-15).** 실제 설계와 실행 기록은 `docs/tasks/phase3/task-3-card-data-and-post.md`에 있다. 아래 초안과 달라진 점: `price_change_cards`에 `prev_rows` 인자 추가, `render_linkedin(events, workloads)`(카드에 의존하지 않음), 마무리 안내 장(D20)으로 장수 +1, 순위 배너는 조합마다 1개, 단가는 반올림하지 않음, 글자 수 검사 추가, 10장 초과 경고는 Task 6으로 이동, 테스트 +17 → 79. 아래 코드 초안은 이력으로 남긴다.

**Files:**
- Create: `publish/card_data.py`, `publish/render_linkedin.py`, `templates/post_linkedin.md.j2`, `tests/test_card_data.py`, `tests/test_render_linkedin.py`

**Interfaces:**
- `price_change_cards(events: dict, rows: list[CostRow], workloads: dict) -> list[dict]`
  - `events`를 **제자리에서 보강한다**: `events["display"] = {"price_change_count"}`
  - 각 장에 `group`(`price`|`cost`|`rank`), `page`(`(1/2)` 또는 `None`), `items`를 담는다
- `check_complete(cards: list[dict], events: dict) -> None` — 카드에 실린 항목 수와 `events`의 항목 수를 대조한다. 어긋나면 `ValueError`(규칙 18, D15)
  - 돌려주는 각 장: `{"kind", "eyebrow", "title", "lead", ...kind별 키}`
  - `title`은 `[{"text": str, "accent": bool}, ...]` — `accent`가 참인 덩어리에만 그라데이션을 입힌다
- `render_linkedin(events: dict, cards: list[dict]) -> str`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_card_data.py`:
```python
from detect.events import detect
from model.tco import PriceBook, estimate
from publish.card_data import price_change_cards

TH = {"e1_min_cost_change_pct": 1.0}


def _events(price_records, workloads, changed):
    from dataclasses import replace
    now = [replace(r, price_usd=changed[(r.platform, r.service, r.region)])
           if (r.platform, r.service, r.region) in changed else r for r in price_records]
    events = detect("2026-09-13", now, price_records, "2026-09-11", workloads, TH)
    return events, estimate(PriceBook(now), workloads)


def test_four_cards_when_ranking_is_unchanged(price_records, workloads):
    events, rows = _events(price_records, workloads, {("redshift", "compute", "us"): 0.40})
    cards = price_change_cards(events, rows, workloads)
    assert [c["kind"] for c in cards] == ["cover", "bullets", "chart", "bullets"]
    assert events["display"]["price_change_count"] == 1


def test_five_cards_when_ranking_changes(price_records, workloads):
    events, rows = _events(price_records, workloads, {("redshift", "compute", "us"): 0.80})
    cards = price_change_cards(events, rows, workloads)
    assert [c["kind"] for c in cards] == ["cover", "bullets", "chart", "bullets", "banners"]
    assert cards[0]["title"] == [{"text": "월 사용료 ", "accent": False},
                                 {"text": "순위 변동", "accent": True}]
    assert len(cards[4]["banners"]) == 2          # 미국 리전, 서울 리전


def test_every_price_change_is_carried_across_pages(price_records, workloads):
    """규칙 18: 항목을 생략하지 않는다. 5줄을 넘으면 장이 늘어난다."""
    changed = {(p, s, "us"): v for (p, s, v) in [
        ("redshift", "compute", 0.40), ("redshift", "storage", 0.03), ("bigquery", "compute", 0.07),
        ("bigquery", "storage", 0.03), ("bigquery", "scan", 7.0), ("snowflake", "compute", 3.3),
        ("databricks", "compute", 0.8)]}
    events, rows = _events(price_records, workloads, changed)
    cards = price_change_cards(events, rows, workloads)
    pages = [c for c in cards if c["kind"] == "bullets" and c["group"] == "price"]
    assert len(pages) == 2                                   # 7건 → 5 + 2
    assert sum(len(c["items"]) for c in pages) == len(events["price_changes"])
    assert [c["page"] for c in pages] == ["(1/2)", "(2/2)"]
    assert all("외 " not in (c.get("note") or "") for c in cards)   # 생략 문구가 없다


def test_missing_item_stops_generation(price_records, workloads):
    """누락 검사: 항목을 하나 빼면 중단한다."""
    from publish.card_data import check_complete
    events, rows = _events(price_records, workloads, {("redshift", "compute", "us"): 0.40})
    cards = price_change_cards(events, rows, workloads)
    cards[1]["items"] = cards[1]["items"][:-1]
    with pytest.raises(ValueError, match="누락"):
        check_complete(cards, events)


def test_chart_card_always_shows_both_regions(price_records, workloads):
    """D18: 변동이 미국 리전에만 있어도 차트에는 서울 리전이 함께 실린다."""
    events, rows = _events(price_records, workloads, {("redshift", "compute", "us"): 0.40})
    chart = next(c for c in price_change_cards(events, rows, workloads) if c["kind"] == "chart")
    assert set(chart["series"]) == {"us", "seoul"}
    assert all(len(chart["series"][r]) == 4 for r in ("us", "seoul"))
    assert events["display"]["chart"]["seoul"] == chart["series"]["seoul"]   # 숫자 검사가 통과하도록 기록한다


def test_platform_and_region_labels_follow_the_fixed_terms(price_records, workloads):
    events, rows = _events(price_records, workloads, {("redshift", "compute", "us"): 0.40})
    cards = price_change_cards(events, rows, workloads)
    assert "Redshift" in cards[1]["items"][0]["strong"]
    assert "미국 리전" in cards[1]["items"][0]["strong"]
```

`tests/test_render_linkedin.py`:
```python
import pytest

from publish.render_linkedin import ARCHIVE_URL, render_linkedin


def test_post_has_the_archive_link_and_stays_under_the_limit(sample_events, sample_cards):
    text = render_linkedin(sample_events, sample_cards)
    assert ARCHIVE_URL in text
    assert "#FinOps" in text
    assert len(text) <= 3000                      # LinkedIn 본문 한도


def test_a_number_that_is_not_in_events_is_rejected(sample_events, sample_cards):
    sample_cards[0]["lead"] = "월 사용료가 999.9% 올랐습니다"
    with pytest.raises(ValueError):
        render_linkedin(sample_events, sample_cards)
```

테스트 픽스처 `sample_events`, `sample_cards`를 `tests/conftest.py`에 추가한다. `price_records`·`workloads` 픽스처로 Redshift 미국 RPU를 0.80으로 올린 이벤트와 그 카드다. 카드 템플릿 테스트(Task 4)와 게시문 테스트가 같은 것을 쓴다.

- [ ] **Step 2: 실패 확인** → `ModuleNotFoundError`

- [ ] **Step 3: `publish/card_data.py` 구현**

- 표지 제목 규칙은 `docs/plans/phase3-card-design.md` 3-2를 따른다.
- `chart` 장은 `cost_changes`에서 변화율 절댓값이 가장 큰 항목의 **시나리오**를 고른다. **리전은 고르지 않고 미국 리전·서울 리전을 모두 싣는다**(D18). 장 데이터는 `{"kind": "chart", "scenario", "series": {"us": {플랫폼: 금액}, "seoul": {플랫폼: 금액}}}`이다. 막대 높이는 두 리전 전체의 최댓값 기준이다.
- **차트 금액을 `events["display"]["chart"]`에 기록한다.** 변동이 없는 플랫폼과 리전의 금액은 `cost_changes`에 없으므로, 기록하지 않으면 숫자 검사가 막는다. 금액은 달러 정수로 반올림해 기록하고 카드에도 같은 값을 쓴다
- `banners` 장은 `rank_changes`를 리전별로 묶는다. 순위가 바뀐 리전만 넣는다.
- 상수: `PER_PAGE = {"price": 5, "cost": 6, "rank": 2}` (디자인 계획 4-1절)
- **`가정과 산출 근거` 장을 만들지 않는다**(D16). 고지는 차트 장(`플랫폼별 월 사용료`)의 각주에 넣는다
- **카드 문안은 `월 사용료`를 쓴다**(D17). 게시문과 대시보드는 아직 `월 비용`이다
- 장수는 고정하지 않는다. 항목을 전부 실을 때까지 늘린다. 10장을 넘으면 경고를 남긴다

- [ ] **Step 4: 게시문 템플릿과 렌더러**

`templates/post_linkedin.md.j2` (초안. 문구는 `/humanize-korean`으로 점검한다):
```jinja
데이터 플랫폼 월 비용 변동 · {{ e.day }}

{{ e.compared_to }} 승인 가격과 비교해 단가 {{ e.display.price_change_count }}건이 바뀌었습니다.

{% for c in cards[1].bullets %}
▪ {{ c.strong }} {{ c.rest }}
{% endfor %}

{% if e.rank_changes %}
월 비용이 낮은 순서가 바뀌었습니다. 자세한 순서는 대시보드에 있습니다.
{% endif %}

네 플랫폼은 단위가 저마다 달라 단가만으로는 비교되지 않습니다. 같은 워크로드를 기준으로 월 비용을 환산해 비교했습니다. 약정 할인을 제외한 모델 추정이며, 가정과 계산 과정은 모두 공개돼 있습니다.

{{ archive_url }}

#데이터플랫폼 #클라우드비용 #FinOps #Snowflake #Databricks #BigQuery #Redshift
```

`publish/render_linkedin.py`는 `render_post.check_numbers`를 그대로 재사용해 검사한다.

- [ ] **Step 5: 테스트 통과 확인** → `.venv\Scripts\python.exe -m pytest -q`

- [ ] **Step 6: 커밋** — `feat: build card data and the LinkedIn post text`

---

### Task 4: 카드 HTML 템플릿과 굽기

> **완료 (2026-09-15).** 실제 설계와 실행 기록은 `docs/tasks/phase3/task-4-card-template.md`에 있다. 아래 초안과 달라진 점: 원본 대조 조정 6건(여백 48px, 알약 56px, 세로 가운데 정렬, 굵기 400·700, 글꼴 스택), 브라우저 실측 레이아웃 검사(`--dump-dom`), `render_html(..., only, measure)`, `bake(..., events)`, 테스트 +13 → 92. 아래 코드 초안은 이력으로 남긴다.

디자인은 **`docs/plans/phase3-card-design.md`를 그대로 따른다.** 이 Task에서 디자인을 새로 정하지 않는다.

**Files:**
- Create: `templates/cards/cards.html.j2`, `publish/render_cards.py`, `tests/test_render_cards.py`

**Interfaces:**
- `render_html(cards: list[dict], eyebrow: str) -> str`
- `bake(cards: list[dict], out_dir: Path, eyebrow: str) -> list[Path]` — `cards.html`, PNG 여러 장, `cards.pdf`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
import re

import pytest

from publish.render_cards import render_html


def test_no_external_requests(sample_cards):
    html = render_html(sample_cards, "가격 변동 리포트")
    assert "<img" not in html and "<link" not in html
    assert "@import" not in html and "url(" not in html


def test_every_card_is_1080x1350_and_has_the_fixed_bars(sample_cards):
    html = render_html(sample_cards, "가격 변동 리포트")
    assert html.count('class="card"') == len(sample_cards)
    assert html.count("CONSUMPTION INSIGHTS") == len(sample_cards)
    assert "--w:1080px" in html and "--h:1350px" in html
    assert "eugeejo-ui.github.io/consumption-insights" in html


def test_the_last_card_does_not_say_swipe(sample_cards):
    html = render_html(sample_cards, "가격 변동 리포트")
    assert html.count("넘기기") == len(sample_cards) - 1


def test_accent_is_applied_only_to_the_marked_part(sample_cards):
    html = render_html(sample_cards, "가격 변동 리포트")
    assert '<em class="accent">순위가 바뀌었습니다</em>' in html


def test_a_number_outside_events_is_rejected(sample_cards, sample_events):
    from publish.render_cards import check_cards
    sample_cards[0]["lead"] = "월 사용료 777% 변동"
    with pytest.raises(ValueError):
        check_cards(sample_cards, sample_events)
```

- [ ] **Step 2: 템플릿 구현**

- `:root`에 디자인 토큰을 둔다. 값은 디자인 계획 1-2·1-3 표를 쓴다.
- 한 장은 `.card{width:var(--w); height:var(--h); position:relative; overflow:hidden}`이다.
- 장 종류별 매크로: `cover`, `bullets`, `chart`, `banners`, (Task 8에서 `chips`, `flow` 추가)
- 막대는 대시보드와 같은 CSS 막대 문법을 쓴다(`.track` + `.fill`).
- `@media print`와 `@page{size:1080px 1350px; margin:0}`으로 PDF 한 장이 카드 한 장이 되게 한다.
- 스크린샷용으로는 `?only=<n>` 대신 **장마다 임시 HTML 파일을 하나씩** 쓴다. 브라우저 인자로 제어하는 것보다 단순하고 실패 원인을 찾기 쉽다.

- [ ] **Step 3: `publish/render_cards.py` 구현**

```python
def bake(cards, out_dir, eyebrow):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cards.html").write_text(render_html(cards, eyebrow), encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        for i, card in enumerate(cards, start=1):
            page = Path(tmp) / f"{i}.html"
            page.write_text(render_html([card], eyebrow, single=True), encoding="utf-8")
            browser.screenshot(page, out_dir / f"{i:02d}-{card['kind']}.png")
    browser.print_pdf(out_dir / "cards.html", out_dir / "cards.pdf")
```

- [ ] **Step 4: 실물 확인 (사용자 게이트)**

실제 승인 스냅샷에 시뮬레이션 변동을 넣어 카드를 굽고, **사용자에게 PNG와 PDF를 보여 준다.**
확인 항목: 글자가 넘치지 않는가, 한글 자간·행간이 어색하지 않은가, 원본 템플릿의 인상이 남아 있는가.
고칠 점이 나오면 **디자인 계획 문서를 먼저 고치고** 구현을 맞춘다(규칙 10).

- [ ] **Step 5: 커밋** — `feat: render the carousel cards from the user template`

---

### Task 5: `pipeline.py` 연결

> **완료 (2026-09-15).** 실제 설계와 실행 기록은 `docs/tasks/phase3/task-5-pipeline-cards.md`에 있다. 아래 초안과 달라진 점: 실패는 `card-errors.txt`와 단계 출력(`cards`, `card_count`)에 남긴다, 굽기 전 한글 글꼴 확인, 승인된 카드 복사를 이 Task에서 구현, 실측에서 찾은 상대 경로 결함 수정(`browser.py`), 테스트 +9 → 101. `--cards intro`는 Task 8로 미룬다.

**Files:** Modify `pipeline.py`, `tests/test_pipeline.py`

- [ ] **Step 1: 테스트 작성**
  - E1인 날 1단계를 돌리면 `cards/` 폴더와 `linkedin.md`가 생긴다(굽기는 가짜로 대체해 브라우저 없이 검증한다)
  - E1이 아닌 날에는 생기지 않는다
  - `--cards <날짜>`는 이미 있는 `events.json`으로 다시 굽고, 승인 여부를 바꾸지 않는다
  - 카드 굽기가 실패해도 `review.md`와 `events.json`은 남는다

- [ ] **Step 2: 구현**
  - `collect_and_review()`의 `if events["significant"]:` 블록에 카드와 게시문 생성을 넣는다.
  - 순서가 중요하다. `price_change_cards()`가 `events`를 보강하므로 **카드 데이터를 먼저 만들고 그 다음에 `events.json`을 쓴다**(D13).
  - 굽기는 `try/except`로 감싸고, 실패하면 경고만 출력한다. 검토 자료는 그대로 남는다.
  - `--cards DAY` 인자를 추가한다. `DAY`가 `intro`면 소개 카드를 굽는다(Task 8).
  - `build_site()`에서 `data/raw/<승인일>/cards/`와 `data/cards/intro/`를 `site/cards/`로 복사한다.

- [ ] **Step 3: 커밋** — `feat: make cards as part of the daily pipeline`

---

### Task 6: 워크플로 연결

> **완료 (2026-09-15).** 실제 설계와 실행 기록은 `docs/tasks/phase3/task-6-workflow.md`에 있다. 아래 초안과 달라진 점: 검토 PR 본문을 `publish/review_pr.py`로 조립(문안은 `docs/scripts/review-pr-script.md`), 10장 초과 경고를 이 Task에서 구현, Task 5 회귀(게시 워크플로의 승인일 파싱) 수정, 테스트 +7 → 108. CI 실측: 글꼴 설치 18초, 카드 5장 굽기 포함 1단계 10초, 두부 글자 없음.

**Files:** Modify `.github/workflows/collect.yml`

- [ ] **Step 1: 한글 글꼴 설치 (필수)**
  - `sudo apt-get install -y fonts-noto-cjk`를 **반드시** 넣는다. Task 1 실측에서 CI 서버의 한글 글꼴이 0개였다 [확인].
  - 없으면 굽기가 실패하지 않고 **두부 글자 카드가 조용히 만들어진다.** 이것이 이 Task에서 가장 위험한 지점이다.
  - 브라우저는 설치하지 않는다. Chrome 152가 미리 있다 [확인].

- [ ] **Step 2: PR 본문에 카드 표시**
  - 브랜치를 push한 뒤 `SHA=$(git rev-parse HEAD)`로 커밋 SHA를 얻는다.
  - 본문에 `![카드 N](https://raw.githubusercontent.com/<owner>/<repo>/$SHA/data/raw/$DAY/cards/NN-kind.png)`를 붙인다.
  - **브랜치 이름이 아니라 SHA를 쓴다.** `review/pending`은 force-push로 갱신돼 이미지가 캐시로 어긋날 수 있다.
  - 게시문(`linkedin.md`)도 본문 끝에 붙인다.

- [ ] **Step 3: 실패해도 검토가 막히지 않는지 확인**
  - 카드 생성 단계는 `continue-on-error: true`로 둔다. 파일이 없으면 이미지 줄을 넣지 않는다.

- [ ] **Step 4: 시뮬레이션 실행으로 실측** → PR에 카드가 보이는지 확인한 뒤 PR을 닫는다.

- [ ] **Step 5: 커밋** — `ci: show the carousel cards in the review PR`

---

### Task 7: 문구 반려 재작성 루프 (규칙 16)

> **실행 기록:** `docs/tasks/phase3/task-7-revise-loop.md`. 실행 계획에서 설계를 바꿨다: 고친 문안은 main에 올리고 수집 워크플로를 다시 돌려 PR을 갱신한다(검토 브랜치 커밋은 매일 강제 push로 사라진다). 게시 보류는 `copy-hold.txt` + `--confirm` 거부로 구현한다. 반려 사유는 권한 있는 사람의 코멘트만 싣는다.

**목적:** 사용자가 게시물 문구를 반려하면 자동으로 다듬어 다시 제출한다. 사용자가 할 일은 라벨 하나를 붙이는 것뿐이다.

**Files:**
- Create: `.github/workflows/revise.yml`, `docs/scripts/revise-loop.md`(재작성 절차서)
- Modify: `.github/workflows/collect.yml`(라벨 안내 문구), `tests/test_render_linkedin.py`(회차 표기 테스트)

**반려 채널**

| 사용자 행동 | 의미 | 결과 |
|---|---|---|
| PR 머지 | 승인 | 게시와 적재가 진행된다 |
| PR에 `revise-copy` 라벨 | **문구 반려** | 게시가 진행되지 않는다. 재작성 요청 Issue가 열린다 |
| PR 닫기 | 전면 반려 | 아무것도 진행되지 않는다 |

**흐름**

```
검토 PR ── revise-copy 라벨 ──→ [revise.yml] 재작성 요청 Issue 생성
                                        │  현재 문안 + PR 코멘트의 반려 사유 + 회차
                                        ▼
                        [Claude] /humanize-korean (반려 사유를 추가 지시로 투입)
                                        │
                        docs/scripts/ 갱신 → 카드·게시문 재생성 → 같은 PR 갱신
                                        │  라벨 제거, Issue 종료
                                        ▼
                                  사용자 재확인
```

**상한 3회.** 3회를 넘기면 자동 재작성을 멈추고 사람이 직접 문안을 고친다. 같은 지적이 세 번 반복되면 스킬로 풀리는 문제가 아니다. 회차는 Issue 제목(`문구 재작성 요청 <날짜> (N회차)`)과 `docs/scripts/`의 점검 기록으로 센다.

**한계 (명시):** `/humanize-korean`은 Claude 스킬이라 GitHub Actions 안에서 실행되지 않는다. 워크플로가 맡는 범위는 **반려 감지와 요청 생성까지**다. 재작성은 Claude 대화에서 수행한다. 전면 자동화는 Actions에 Anthropic API 키를 등록해야 가능하며, 이 프로젝트의 무키 방침과 충돌한다.

- [ ] **Step 1** `revise.yml` 작성. `pull_request.labeled` 이벤트에서 `revise-copy`만 받는다
  - Issue 본문: 대상 날짜, 회차, 현재 게시문 전문, 현재 카드 문안, PR 코멘트에서 수집한 반려 사유
  - 회차가 3을 넘으면 Issue 대신 `사람이 직접 수정 필요` 라벨을 붙이고 종료한다
- [ ] **Step 2** `docs/scripts/revise-loop.md` 작성. Claude가 따라야 할 재작성 절차와 금지 사항
  - 숫자와 자리표시자를 바꾸지 않는다
  - 반려 사유에서 요구하지 않은 부분은 손대지 않는다
  - 변경률이 30%를 넘으면 중단하고 보고한다
- [ ] **Step 3** 테스트 2개
  - 게시문에 회차 표기가 들어가고, 회차가 숫자 검사를 통과한다
  - 회차 4에서는 재작성을 시도하지 않는다
- [ ] **Step 4** 시뮬레이션 검증. 라벨을 붙여 Issue가 열리는지, 재작성 후 같은 PR이 갱신되는지 확인한다
- [ ] **Step 5** 커밋 — `ci: reopen the copy for revision when it is rejected`

**완료 기준:** 라벨을 붙이면 재작성 요청이 열린다. 재작성 후 같은 PR이 갱신된다. 3회를 넘기면 자동 재작성이 멈춘다.

---

### Task 8: 소개 카드 4장

> **실행 기록:** `docs/tasks/phase3/task-8-intro-cards.md`. 실행 계획에서 바꿨다: 5장(D20), 4장 문안 보완(리전별 T1, 채택·기각 설명), 로컬에서 굽고 실물 승인 후 push(D21), 글꼴 목록에 Noto Sans KR(D22), 테스트 +10 → 127.

**Files:** Modify `publish/card_data.py`, `templates/cards/cards.html.j2`, `tests/test_card_data.py`

- [ ] **Step 1: 테스트 작성**
  - `intro_cards(analysis, day)`가 4장을 돌려주고 종류가 `["cover", "chips", "flow", "bullets"]`이다
  - 4장의 판정 문구가 **채택 / 기각**을 쓴다(규칙 17). "지지"라는 낱말이 들어가면 실패한다
  - 시나리오별 1위가 최신 승인 스냅샷의 계산 결과와 같다
  - 소개 카드에는 `events.json`이 없으므로, 숫자 검사는 **계산 결과로 만든 사전**을 기준으로 한다

- [ ] **Step 2: 구현**
  - 문안은 디자인 계획 3-1 표를 따른다. 고정 문장과 자동으로 채우는 숫자를 분리한다.
  - `chips`, `flow` 매크로를 템플릿에 추가한다.

- [ ] **Step 3: 굽고 사용자에게 보여 준다.** 문구를 고칠 곳이 있으면 반영한다.

- [ ] **Step 4: 커밋** — `feat: add the five intro cards`

---

### Task 9: 종단 검증

> **실행 기록:** `docs/tasks/phase3/task-9-e2e.md`. 실행 계획에서 바꿨다: 승인된 카드 게시는 로컬·CI 통합 테스트로 확인(시뮬레이션은 승인되지 않는다), 보류 유지·보류 중 머지 거부를 CI에서 확인, 시트 중복 적재 결함 수정, 폰 저장 확인은 3-10으로, 첫 실제 변동 확인 목록을 남겼다.

- [ ] 시뮬레이션 변동 주입 → 검토 PR에 카드 5장과 게시문이 보인다
- [ ] PR을 닫으면 아무것도 진행되지 않는다
- [ ] 같은 날 다시 돌리면 같은 PR이 갱신되고 카드가 새 SHA로 바뀐다
- [ ] 머지하면 `site/cards/<날짜>/`가 게시되고 폰 브라우저에서 이미지를 저장할 수 있다
- [ ] 카드에 쓰인 숫자가 대시보드의 값과 일치한다
- [ ] 시뮬레이션 스냅샷은 승인되지 않는다(기존 방어가 그대로 작동한다)
- [ ] 정리: 시뮬레이션 스냅샷 폴더를 main에서 지운다

---

### Task 10: 첫 게시 (사용자)

- [ ] 소개 카드 4장을 굽는다(`pipeline.py --cards intro`)
- [ ] 사용자가 게시된 주소에서 이미지 또는 PDF를 받는다
- [ ] **사용자가 LinkedIn에서 직접 게시한다.** Claude는 게시하지 않는다
- [ ] 게시 결과를 확인하고 `CLAUDE.md` 진행 로그에 적는다

## 완료 기준 (Phase 3 게이트)

- E1 이벤트에서 카드와 게시문이 자동으로 만들어진다.
- 카드의 모든 숫자가 `events.json`과 일치한다(자동 검사).
- 검토 PR에서 카드를 미리 볼 수 있고, 머지하면 게시된다.
- 사용자가 첫 게시를 완료한다.
