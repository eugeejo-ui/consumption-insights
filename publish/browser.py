"""설치된 Chromium 계열 브라우저(Edge·Chrome)를 명령줄로 호출해 HTML을 PNG·PDF로 굽는다.

새 파이썬 패키지를 쓰지 않으려는 선택이다(Phase 3 결정 D8).
호출은 언제나 임시 프로필로 한다. 사용자의 브라우저 프로필과 로그인 세션을 건드리지 않기 위해서다.
옵션 표기는 버전마다 달라서, 되는 조합을 찾을 때까지 차례로 시도한다.
"""
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
COMMON = ["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars",
          "--force-device-scale-factor=1", "--run-all-compositor-stages-before-draw",
          "--virtual-time-budget=5000"]
HEADLESS = ["--headless=new", "--headless"]          # 새 표기를 모르는 버전이 있다
PDF_HEADER_OFF = ["--no-pdf-header-footer", "--print-to-pdf-no-header"]
TIMEOUT = 120


def find_browser() -> str:
    """쓸 브라우저 경로. BROWSER_BIN이 가장 우선한다."""
    chosen = os.environ.get("BROWSER_BIN")
    if chosen and Path(chosen).exists():
        return chosen
    for path in CANDIDATES:
        if Path(path).exists():
            return path
    raise RuntimeError("브라우저를 찾지 못했다. Edge나 Chrome을 설치하거나 BROWSER_BIN에 경로를 지정한다.")


def _attempt(args: list[str]) -> str | None:
    """한 번 실행한다. 성공하면 None, 실패하면 사유 문자열."""
    with tempfile.TemporaryDirectory() as profile:
        try:
            subprocess.run([find_browser(), *COMMON, f"--user-data-dir={profile}", *args],
                           check=True, capture_output=True, timeout=TIMEOUT)
        except subprocess.CalledProcessError as exc:
            return f"종료 코드 {exc.returncode}: {exc.stderr.decode('utf-8', 'replace').strip()[:200]}"
        except subprocess.TimeoutExpired:
            return f"{TIMEOUT}초 안에 끝나지 않았다"
    return None


def _bake(out: Path, variants: list[list[str]], args: list[str]) -> Path:
    """되는 옵션 조합을 찾을 때까지 시도한다. 파일이 실제로 생겨야 성공으로 본다."""
    out.parent.mkdir(parents=True, exist_ok=True)
    reasons = []
    for headless in HEADLESS:
        for variant in variants:
            out.unlink(missing_ok=True)
            failure = _attempt([headless, *variant, *args])
            if failure is None and out.exists() and out.stat().st_size > 0:
                return out
            reasons.append(f"{headless} {' '.join(variant)}: {failure or '파일이 생기지 않았다'}")
    raise RuntimeError(f"{out.name}을(를) 만들지 못했다.\n" + "\n".join(reasons))


def screenshot(html: Path, out: Path, width: int = 1080, height: int = 1350) -> Path:
    out = Path(out)
    return _bake(out, [[]], [f"--window-size={width},{height}", f"--screenshot={out}",
                             Path(html).resolve().as_uri()])


def print_pdf(html: Path, out: Path) -> Path:
    out = Path(out)
    return _bake(out, [[flag] for flag in PDF_HEADER_OFF],
                 [f"--print-to-pdf={out}", Path(html).resolve().as_uri()])
