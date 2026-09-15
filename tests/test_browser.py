import struct
from pathlib import Path

import pytest

from publish import browser

HTML = """<!doctype html><meta charset="utf-8">
<style>html,body{margin:0}div{width:1080px;height:1350px;background:#F6F5F3}</style>
<div>한글</div>"""


def _has_browser() -> bool:
    try:
        browser.find_browser()
    except RuntimeError:
        return False
    return True


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


@pytest.mark.skipif(not _has_browser(), reason="설치된 브라우저가 없다")
def test_bakes_a_png_of_the_right_size(tmp_path):
    page = tmp_path / "card.html"
    page.write_text(HTML, encoding="utf-8")
    out = browser.screenshot(page, tmp_path / "card.png")
    header = out.read_bytes()[16:24]
    assert struct.unpack(">II", header) == (1080, 1350)


def test_waits_for_a_file_written_after_the_browser_exits(tmp_path):
    """브라우저가 먼저 종료하고 파일은 하위 프로세스가 뒤늦게 쓴다(Edge 실측, 2026-09-14)."""
    import threading
    import time

    out = tmp_path / "late.png"

    def write_later():
        time.sleep(1.2)
        out.write_bytes(b"x" * 64)

    threading.Thread(target=write_later).start()
    assert browser.wait_for_file(out, timeout=10) is True


def test_gives_up_when_the_file_never_appears(tmp_path):
    assert browser.wait_for_file(tmp_path / "never.png", timeout=1) is False


def test_output_paths_are_passed_to_the_browser_as_absolute(tmp_path, monkeypatch):
    """Edge의 하위 프로세스는 작업 폴더가 달라 상대 경로 파일을 쓰지 못한다(2026-09-15 실측).
    파이프라인은 data/raw 상대 경로로 굽는다."""
    monkeypatch.chdir(tmp_path)
    seen = []
    monkeypatch.setattr(browser, "_bake", lambda out, variants, args: seen.append((out, args)) or out)

    browser.screenshot(Path("card.html"), Path("data/raw/day/cards/01-cover.png"))
    browser.print_pdf(Path("card.html"), Path("data/raw/day/cards/cards.pdf"))

    for out, args in seen:
        assert out.is_absolute()
        flag = next(a for a in args if a.startswith(("--screenshot=", "--print-to-pdf=")))
        assert Path(flag.split("=", 1)[1]) == tmp_path / out.relative_to(tmp_path)
