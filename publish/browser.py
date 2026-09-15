"""설치된 Chromium 계열 브라우저(Edge·Chrome)를 명령줄로 호출해 HTML을 PNG·PDF로 굽는다.

새 파이썬 패키지를 쓰지 않으려는 선택이다(Phase 3 결정 D8).
호출은 언제나 임시 프로필로 한다. 사용자의 브라우저 프로필과 로그인 세션을 건드리지 않기 위해서다.
옵션 표기는 버전마다 달라서, 되는 조합을 찾을 때까지 차례로 시도한다.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import time
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
COMMON = ["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars",
          "--force-device-scale-factor=1", "--run-all-compositor-stages-before-draw",
          "--virtual-time-budget=5000"]
HEADLESS = ["--headless=new", "--headless"]          # 새 표기를 모르는 버전이 있다
PDF_HEADER_OFF = ["--no-pdf-header-footer", "--print-to-pdf-no-header"]
TIMEOUT = 120
FILE_WAIT = 60                                      # 브라우저 종료 뒤 파일이 쓰일 때까지 기다리는 상한(초)


def find_browser() -> str:
    """쓸 브라우저 경로. BROWSER_BIN이 가장 우선한다."""
    chosen = os.environ.get("BROWSER_BIN")
    if chosen and Path(chosen).exists():
        return chosen
    for path in CANDIDATES:
        if Path(path).exists():
            return path
    raise RuntimeError("브라우저를 찾지 못했다. Edge나 Chrome을 설치하거나 BROWSER_BIN에 경로를 지정한다.")


def wait_for_file(out: Path, timeout: float = FILE_WAIT) -> bool:
    """파일이 생기고 크기가 두 번 연속 같으면 다 쓰인 것으로 본다.

    Edge는 실행 파일이 먼저 종료 코드 0을 돌려주고, 실제 굽기는 분리된 하위 프로세스가 뒤늦게 끝낸다
    [확인 2026-09-14]. 종료 직후 파일을 확인하면 아직 없다.
    """
    deadline = time.monotonic() + timeout
    last = -1
    while time.monotonic() < deadline:
        size = out.stat().st_size if out.exists() else -1
        if size > 0 and size == last:
            return True
        last = size
        time.sleep(0.5)
    return False


def _attempt(args: list[str], out: Path) -> str | None:
    """한 번 실행하고 결과 파일이 다 쓰일 때까지 기다린다. 성공하면 None, 실패하면 사유 문자열."""
    # 프로필 폴더는 파일을 기다린 뒤에 지운다. 하위 프로세스가 아직 쓰는 중에 지우면 굽기가 깨진다.
    # Edge의 충돌 보고 프로세스는 그 뒤에도 프로필 안 파일을 잠시 잠근다. 삭제 실패는 굽기 실패가 아니다.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        try:
            subprocess.run([find_browser(), *COMMON, f"--user-data-dir={profile}", *args],
                           check=True, capture_output=True, timeout=TIMEOUT)
        except subprocess.CalledProcessError as exc:
            return f"종료 코드 {exc.returncode}: {exc.stderr.decode('utf-8', 'replace').strip()[:200]}"
        except subprocess.TimeoutExpired:
            return f"{TIMEOUT}초 안에 끝나지 않았다"
        if not wait_for_file(out):
            return f"{FILE_WAIT}초를 기다려도 파일이 생기지 않았다"
    return None


def _bake(out: Path, variants: list[list[str]], args: list[str]) -> Path:
    """되는 옵션 조합을 찾을 때까지 시도한다. 파일이 실제로 생겨야 성공으로 본다."""
    out.parent.mkdir(parents=True, exist_ok=True)
    reasons = []
    for headless in HEADLESS:
        for variant in variants:
            out.unlink(missing_ok=True)
            failure = _attempt([headless, *variant, *args], out)
            if failure is None:
                return out
            reasons.append(f"{headless} {' '.join(variant)}: {failure}")
    raise RuntimeError(f"{out.name}을(를) 만들지 못했다.\n" + "\n".join(reasons))


def screenshot(html: Path, out: Path, width: int = 1080, height: int = 1350) -> Path:
    # 출력 경로는 절대 경로로 넘긴다. Edge의 분리된 하위 프로세스는 작업 폴더가 달라 상대 경로 파일을 쓰지 못한다
    # [확인 2026-09-15, pipeline.py의 data/raw 상대 경로에서 60초 대기 후 실패].
    out = Path(out).resolve()
    return _bake(out, [[]], [f"--window-size={width},{height}", f"--screenshot={out}",
                             Path(html).resolve().as_uri()])


def print_pdf(html: Path, out: Path) -> Path:
    out = Path(out).resolve()
    return _bake(out, [[flag] for flag in PDF_HEADER_OFF],
                 [f"--print-to-pdf={out}", Path(html).resolve().as_uri()])


def dump_dom(html: Path) -> str:
    """페이지 스크립트가 실행된 뒤의 DOM을 표준 출력으로 받는다. 카드 레이아웃 측정값을 읽는 데 쓴다.

    Edge에서도 출력을 받는다(5회 모두, 최대 30KB) [확인 2026-09-15]. PDF 제목으로 받는 방식은 4,096자에서 잘린다.
    """
    reasons = []
    for headless in HEADLESS:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
            try:
                result = subprocess.run([find_browser(), *COMMON, f"--user-data-dir={profile}", headless, "--dump-dom",
                                         Path(html).resolve().as_uri()], capture_output=True, timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                reasons.append(f"{headless}: {TIMEOUT}초 안에 끝나지 않았다")
                continue
        dom = result.stdout.decode("utf-8", "replace")
        if result.returncode == 0 and dom.strip():
            return dom
        reasons.append(f"{headless}: 종료 코드 {result.returncode}, 출력 {len(dom)}자")
    raise RuntimeError("DOM을 받지 못했다.\n" + "\n".join(reasons))
