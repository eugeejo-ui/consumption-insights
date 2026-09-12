import struct

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
