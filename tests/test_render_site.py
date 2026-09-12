from model.tco import PLATFORMS, CostRow
from publish.render_site import render

COMPUTE = {"snowflake": 100.0, "databricks": 200.0, "redshift": 300.0, "bigquery": 400.0}   # 합계 110 < 210 < 310 < 410


def _render(tmp_path, workloads, prev_ranks=None):
    rows = [CostRow(sid, p, reg, COMPUTE[p], 10.0)
            for sid in workloads["scenarios"] for p in PLATFORMS for reg in ("us", "seoul")]
    t1_by_region = {
        "us": {"winners": {"W1": "redshift", "W2": "redshift", "W3": "redshift"},
               "robustness": {"W1": "민감", "W2": "민감", "W3": "민감"}, "supported": False},
        "seoul": {"winners": {"W1": "redshift", "W2": "redshift", "W3": "redshift"},
                  "robustness": {"W1": "견고", "W2": "견고", "W3": "견고"}, "supported": False},
    }
    return render(
        rows,
        premiums=[{"platform": "redshift", "service": "compute", "sku": "serverless-rpu",
                   "us": 0.375, "seoul": 0.438, "premium_pct": 16.8},
                  {"platform": "databricks", "service": "storage", "sku": "adls-hot-lrs",
                   "us": 0.0208, "seoul": 0.02, "premium_pct": -3.8}],
        t1_by_region=t1_by_region,
        t2={"spread_pp": 39.5, "supported": True},
        workloads=workloads, price_dates={"snowflake": "2026-09-12"}, built_on="2026-09-12",
        prev_ranks=prev_ranks, out_dir=tmp_path)


def test_render_writes_page_with_disclaimer_numbers_and_dates(tmp_path, workloads):
    out = _render(tmp_path, workloads)
    html = out.read_text(encoding="utf-8")
    assert out == tmp_path / "index.html"
    assert "모델로 추정한 값" in html
    assert "110" in html               # 합계 = 컴퓨트 100 + 스토리지 10
    assert "+16.8%" in html
    assert "2026-09-12" in html
    assert "http" not in html.split("<body")[0]        # 외부 요청 없음(폰트·차트 CDN 링크가 없다)


def test_render_shows_t1_for_both_regions(tmp_path, workloads):
    html = _render(tmp_path, workloads).read_text(encoding="utf-8")
    assert "T1 월 비용 1위는 워크로드마다 다르다 (미국 리전)" in html
    assert "T1 월 비용 1위는 워크로드마다 다르다 (서울 리전)" in html
    assert "W1 Redshift (민감)" in html   # 미국
    assert "W1 Redshift (견고)" in html   # 서울


def test_site_has_all_sections(tmp_path, workloads):
    html = _render(tmp_path, workloads).read_text(encoding="utf-8")
    for anchor in ("id=\"verdicts\"", "id=\"costs\"", "id=\"premium\"", "id=\"assumptions\""):
        assert anchor in html
    assert "consumption-insights" in html          # 사이드바 워드마크(타사 로고를 쓰지 않는다)
    assert "서울 프리미엄" in html and "가정 공개" in html


def test_site_has_a_panel_for_every_scenario_and_region(tmp_path, workloads):
    html = _render(tmp_path, workloads).read_text(encoding="utf-8")
    for sid in workloads["scenarios"]:
        for region in ("us", "seoul"):
            assert f'data-panel="{sid}|{region}"' in html


def test_rank_arrows_reflect_previous_snapshot(tmp_path, workloads):
    def rows(html):                                            # CSS 선택자가 아니라 순위 줄만 센다
        return [line for line in html.splitlines() if 'class="rank" data-delta=' in line]

    plain = rows(_render(tmp_path, workloads).read_text(encoding="utf-8"))
    assert plain and all('data-delta="none"' in line for line in plain)      # 비교할 승인 스냅샷이 없다

    prev = {"W1": {"us": ["databricks", "snowflake", "redshift", "bigquery"]}}
    changed = rows(_render(tmp_path, workloads, prev_ranks=prev).read_text(encoding="utf-8"))
    marks = [line.split('data-delta="')[1].split('"')[0] for line in changed]
    assert marks[:4] == ["up", "down", "flat", "flat"]    # 첫 카드(W1 미국): snowflake 2위→1위, databricks 1위→2위
    assert marks[4:8] == ["none"] * 4                     # 그다음 카드(W1 서울)는 이전 순위가 없다
