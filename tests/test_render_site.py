from model.tco import PLATFORMS, CostRow
from publish.render_site import render


def _render(tmp_path, workloads):
    rows = [CostRow(sid, p, reg, 100.0, 10.0) for sid in workloads["scenarios"] for p in PLATFORMS for reg in ("us", "seoul")]
    t1_by_region = {
        "us": {"winners": {"W1": "redshift", "W2": "redshift", "W3": "redshift"},
               "robustness": {"W1": "민감", "W2": "민감", "W3": "민감"}, "supported": False},
        "seoul": {"winners": {"W1": "redshift", "W2": "redshift", "W3": "redshift"},
                  "robustness": {"W1": "견고", "W2": "견고", "W3": "견고"}, "supported": False},
    }
    return render(
        rows,
        premiums=[{"platform": "redshift", "service": "compute", "sku": "serverless-rpu",
                   "us": 0.375, "seoul": 0.438, "premium_pct": 16.8}],
        t1_by_region=t1_by_region,
        t2={"spread_pp": 39.5, "supported": True},
        workloads=workloads, price_dates={"snowflake": "2026-09-12"}, built_on="2026-09-12", out_dir=tmp_path)


def test_render_writes_page_with_disclaimer_numbers_and_dates(tmp_path, workloads):
    out = _render(tmp_path, workloads)
    html = out.read_text(encoding="utf-8")
    assert out == tmp_path / "index.html"
    assert "모델 추정" in html
    assert "110.00" in html            # 합계 = 컴퓨트 100 + 스토리지 10
    assert "+16.8%" in html
    assert "2026-09-12" in html
    assert "cdn.plot.ly" in html


def test_render_shows_t1_for_both_regions(tmp_path, workloads):
    html = _render(tmp_path, workloads).read_text(encoding="utf-8")
    assert "T1 월 비용 1위는 워크로드마다 다르다 (미국)" in html
    assert "T1 월 비용 1위는 워크로드마다 다르다 (서울)" in html
    assert "W1: redshift (민감)" in html   # 미국
    assert "W1: redshift (견고)" in html   # 서울
