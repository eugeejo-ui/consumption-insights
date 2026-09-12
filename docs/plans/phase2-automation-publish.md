# Phase 2: 자동 수집 + 변동 감지 + 검토 PR Implementation Plan (2-5a 전까지)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 매일 가격을 수집해 이전 승인 스냅샷과 비교한다. 단가가 바뀌면 검토 PR(스냅샷 + 검토 보고서 + 글 초안)을 올리고 멈춘다. 이 계획은 **대시보드를 만들기 전(2-5a)** 까지만 다룬다.

**Architecture:**
- `detect/events.py`가 오늘 가격과 이전 승인 스냅샷을 비교해 `events.json` 내용을 만든다. 들어가는 것은 단가 변화, 월 비용 ±1% 이상 변화, 순위 변화다.
- `publish/render_post.py`가 E1 이벤트로 글 초안을 만든다. 글에 나온 숫자가 모두 `events.json`에 있어야 통과한다.
- `pipeline.py` 1단계는 결과에 따라 갈라진다.
  - 변화 없음: `data/checks.csv`에 한 줄만 기록한다.
  - 변화 있음: 스냅샷, `review.md`, `events.json`, `post.md`를 쓰고 멈춘다.
- GitHub Actions `collect.yml`이 1단계를 돌린다. 변화가 있으면 `review/pending` 브랜치로 검토 PR을 열거나 갱신한다.
- `publish/sheets_log.py`는 컨펌 뒤 적재할 모듈이다. 이 계획에서는 만들고 테스트만 한다. 실제 연결은 2-5에서 한다.

**Tech Stack:** Python 3.11, requests, PyYAML, Jinja2, plotly, pytest, google-auth(신규), GitHub Actions(`actions/checkout@v7`, `actions/setup-python@v7`)

**Spec:** `CLAUDE.md` Phase 2와 규칙 13·14, `docs/phases/phase-2-automation-publish.md`, `docs/plans/phase1-tco-dashboard.md`(Task 8b)

**진행 현황:** Task 1 완료(`5dcad55`, 38 passed), Task 2 완료(`72723d5`, 40 passed), Task 3 완료(`9a46707`, 44 passed), Task 4 완료(`802c126`, 47 passed, google-auth 2.58.0). Task 5 진행 중.
- Task 5 사전 준비: 작성자 이름 공개 확인, 저장소 생성 완료. `workflow` 권한과 Actions 설정 2개는 남았다.
- Task 5 Step 1~4 완료: `.gitattributes`(재정규화 변경 없음), `collect.yml`, YAML 확인, 전체 기록 개인정보 검사
- Task 5 완료(2026-09-12): push, 실제 실행(변화 없음 → checks.csv 봇 커밋), 시뮬레이션 2회(PR 생성 → 같은 PR 갱신) → PR 닫기(반려 흐름)
- 2-5a 디자인 게이트 통과(2026-09-12): 계획 `docs/plans/phase2-5a-dashboard-design.md` 승인
- Task 6 완료(2026-09-12): 템플릿 기반 대시보드. CSS 막대, 시스템 글꼴, JS 필터. Plotly 제거. 테스트 50개
- Task 7 완료(2026-09-12): Pages 설정, `publish.yml`, `pipeline.py --build`, 매일 스케줄 활성화. 게시 주소는 https://eugeejo-ui.github.io/consumption-insights/ 다. 테스트 51개
- Task 8 완료(2026-09-12): `detect/price_watch.py`, `watch.yml`. BigQuery 지문 비교 + 수동 가격표 90일 알림. 테스트 55개
- Task 9 완료(2026-09-12): 머지 → 게시 트리거 실측, 시뮬레이션 스냅샷 차단 확인, `--dry-run` 추가. 테스트 56개
- **Phase 2의 코드 작업은 끝났다. 남은 것은 사용자의 2-0c 준비와 시트 적재 확인뿐이다.**
- Task 4 Step 6(실제 기준선 적재, 선택)은 2-0c 전이라 2-7로 미뤘다.
- Task 3 Step 5(실제 실행): 오늘(2026-09-11)은 승인 스냅샷이 있어 같은 날 재수집 가드가 막았다. 그래서 `data/checks.csv`는 아직 없다. 파일을 쓰지 않은 실제 수집·비교에서는 18행이 승인본과 같았다.

## 결정 (2026-09-11 사용자 승인: 계획 승인, D1~D3 모두 추천안)
| # | 결정 | 추천 | 이유 | 대안 |
|---|---|---|---|---|
| D1 | 변화 없는 날 처리 | 스냅샷 폴더를 만들지 않는다. `data/checks.csv`에 한 줄(날짜, 결과, 비교 기준일)을 적어 main에 커밋한다 | 매일 커밋이 생겨서 공개 저장소의 "60일 무활동 시 스케줄 중지"를 막는다 [확인]. "매일 확인했다"는 기록이 남는다. 같은 18행 스냅샷이 매일 쌓이지 않는다 | B 아무것도 커밋하지 않음(조용하지만 60일 문제가 있고 기록이 없다). C 매일 전체 스냅샷 커밋(가장 자세하지만 같은 내용이 매일 쌓인다) |
| D2 | 검토 PR을 여는 기준 | **단가가 하나라도 바뀌면** 검토 PR을 연다. **글 초안은 E1**(월 비용 ±1% 이상 또는 순위 변화)일 때만 만든다 | 기존 문서는 "E1이면 PR"이었다. 그러면 작은 변화는 사람이 보지 못한 채 넘어가고, 비교 기준(승인 가격)이 오래된 채로 남는다 | E1일 때만 PR(PR 수는 줄지만 작은 변화가 검토 없이 쌓인다) |
| D3 | 매일 스케줄을 켜는 시점 | Task 5에서는 **수동 실행(workflow_dispatch)만** 한다. 매일 스케줄은 게시 워크플로(2-5)가 생긴 뒤 켠다 | 게시 워크플로가 없을 때 PR을 머지하면 승인 기록(`approved.txt`)이 생기지 않아 비교 기준이 꼬인다 | 지금 켜기(열린 PR은 2-5 전까지 머지하지 않고 둔다) |

## 한눈에 보기 (사용자용 요약)
| Task | 만드는 것 | 테스트(누적) | 사용자가 할 일 |
|---|---|---|---|
| 1 | 변동 감지 `detect/events.py`, E1 기준값(`e1_min_cost_change_pct: 1.0`) | +5, 기존 1개 보강 → 38 | — |
| 2 | 글 초안 `publish/render_post.py`와 템플릿, 숫자 일치 검사 | +2 → 40 | 글 문장 톤 확인(선택) |
| 3 | `pipeline.py` 1단계 개편: 변화 없음/있음 분기, `events.json`, `post.md`, `checks.csv`, `--simulate`, Actions 출력 | +4 → 44 | — |
| 4 | Google Sheets 적재 모듈 `publish/sheets_log.py`(아직 연결하지 않음) | +3 → 47 | (선택) 2-0c 준비 후 기준선 1회 적재 확인 |
| 5 | GitHub 연결: `.gitattributes`, `collect.yml`, 첫 push, 수동 실행 2회(실제, 시뮬레이션) | 워크플로 실측 | **2-0 준비**: 작성자 이름 공개 확인, `gh auth refresh -s workflow`, 공개 저장소, Actions 설정 2개, push 승인 |
| **멈춤** | **2-5a 대시보드 디자인 게이트** | — | 마음에 드는 대시보드 템플릿 전달 |

Task 6 이후(디자인 적용, `publish.yml`, 알림, 종단 검증)는 2-5a에서 템플릿을 받은 뒤 별도 계획으로 쓴다(맨 아래 개요 참고).

## Global Constraints
- Windows + PowerShell이다. venv는 `.venv\Scripts\python.exe`를 직접 호출하고, 한글을 출력할 때는 `$env:PYTHONIOENCODING='utf-8'`을 설정한다.
- 공개 저장소를 전제한다. `GOOGLE_SA_KEY`, `PRICE_SHEET_ID`는 환경변수나 GitHub Secret으로만 받는다. 키 내용은 출력하거나 파일로 남기지 않는다. 커밋 전 검사 패턴에 `"private_key"`를 추가한다.
- snowflake.com, databricks.com에는 자동으로 접근하지 않는다. 두 플랫폼 가격은 사람이 확인한 CSV에서만 읽는다.
- 규칙 14를 따른다. 게시, 시트 적재, 사이트 생성은 컨펌(PR 머지) 뒤에만 한다. **시뮬레이션 스냅샷은 절대 승인하지 않는다**(코드로 막는다).
- 저장소 생성, 저장소 설정 변경, push는 외부로 나가는 행동이라 매번 사용자 확인을 받는다(규칙 4). 사용자가 일괄 허용하면 그 범위를 따른다.
- 비교 기준은 항상 **이전 승인 스냅샷**(`approved.txt`가 있는 날짜)이다. 월 비용은 비교하는 양쪽 모두 현재 `workloads.yaml`로 계산한다.
- 글 초안의 모든 숫자는 `events.json`에 있어야 한다(표시 반올림 허용).
- 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`을 붙인다. 한 번에 Task 하나만 하고 보고한 뒤 멈춘다(규칙 10).

## File Structure
```
config/thresholds.yaml             # Task 1: e1_min_cost_change_pct 추가
detect/__init__.py                 # Task 1
detect/events.py                   # Task 1: 단가·월 비용·순위 변화 → events.json 내용
publish/review_report.py           # Task 1: latest_approved_day 추가 / Task 3: 글 초안 여부 표시
publish/render_post.py             # Task 2: 글 초안 + 숫자 일치 검사
templates/post_price_change.md.j2  # Task 2
pipeline.py                        # Task 3: 변화 없음/있음 분기, --simulate, Actions 출력
templates/review.md.j2             # Task 3: PR 컨펌·반려 안내, 글 초안 여부
data/checks.csv                    # Task 3 이후 생성: 매일 확인 기록 (day,result,compared_to)
publish/sheets_log.py              # Task 4: Sheets values.append (컨펌 뒤 사용)
requirements.txt, .gitignore       # Task 4: google-auth, /secrets/
.gitattributes                     # Task 5: * text=auto eol=lf
.github/workflows/collect.yml      # Task 5
tests/test_events.py               # Task 1
tests/test_render_post.py          # Task 2
tests/test_pipeline.py             # Task 3 (기존 파일 보강)
tests/test_sheets_log.py           # Task 4
```
- 기존 문서의 `detect/diff.py`는 `detect/events.py`로 이름을 바꾼다(만드는 결과물이 `events.json`이라서).

## data/raw/<날짜>/ 폴더 (변화가 있는 날만 생긴다)
| 파일 | 만드는 곳 | 내용 |
|---|---|---|
| `aws.csv`, `azure.csv`, `manual.csv` | 1단계 | 수집 가격 스냅샷 |
| `review.md` | 1단계 | 검토 보고서(PR 본문이 된다) |
| `events.json` | 1단계 | 단가 변화, 월 비용 변화, 순위 변화, 상태(`first`/`changed`), E1 여부 |
| `post.md` | 1단계, E1일 때만 | 글 초안(숫자 일치 검사 통과본) |
| `approved.txt` | 2단계(컨펌 뒤) | 승인 시각. Phase 2에서는 `publish.yml`이 기록한다(Task 7) |

---

### Task 1: 변동 감지 (`detect/events.py`)

**Files:**
- Create: `detect/__init__.py`(빈 파일), `detect/events.py`, `tests/test_events.py`
- Modify: `config/thresholds.yaml`, `publish/review_report.py`(`latest_approved_day` 추가), `tests/test_review_report.py`(단언 1줄 추가)

**Interfaces:**
- Consumes: `price_changes(current, previous) -> list[dict] | None`(Task 8b), `estimate`, `ranking`, `PriceBook`(model/tco.py), `REGIONS`
- Produces:
  - `latest_approved_day(day: str, root: Path = Path("data/raw")) -> str | None`
  - `detect(day: str, records: list[PriceRecord], previous: list[PriceRecord] | None, compared_to: str | None, workloads: dict, thresholds: dict) -> dict`
  - 반환 키: `day`, `compared_to`, `min_cost_change_pct`, `status`(`"first"|"unchanged"|"changed"`), `price_changes`(first이면 None), `cost_changes`, `rank_changes`, `significant`(bool)
  - `cost_changes` 원소: `{"scenario", "region", "platform", "before", "after", "change_pct"}`(금액은 소수 둘째 자리 반올림, 변동률은 첫째 자리)
  - `rank_changes` 원소: `{"scenario", "region", "before": [플랫폼...], "after": [플랫폼...]}`

- [ ] **Step 1: 판정 기준 추가 (데이터를 보기 전에 고정, 규칙 5)**

`config/thresholds.yaml` 끝에 추가:
```yaml
e1_min_cost_change_pct: 1.0  # E1: 어떤 시나리오·리전·플랫폼이든 월 비용이 ±1% 이상 바뀌면 글 초안을 만든다 (Phase 2 착수 전 고정)
```

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/test_events.py`:
```python
from dataclasses import replace

from detect.events import detect

TH = {"e1_min_cost_change_pct": 1.0}


def _with(records, platform, service, region, price):
    return [replace(r, price_usd=price) if (r.platform, r.service, r.region) == (platform, service, region) else r
            for r in records]


def test_same_prices_are_unchanged(price_records, workloads):
    ev = detect("2026-09-12", price_records, price_records, "2026-09-11", workloads, TH)
    assert ev["status"] == "unchanged" and ev["price_changes"] == [] and not ev["significant"]


def test_no_approved_snapshot_is_first(price_records, workloads):
    ev = detect("2026-09-12", price_records, None, None, workloads, TH)
    assert ev["status"] == "first" and ev["price_changes"] is None and not ev["significant"]


def test_small_price_change_needs_review_but_no_post(price_records, workloads):
    now = _with(price_records, "bigquery", "storage", "us", 0.0201)        # +0.5%: 월 비용 변화는 1% 미만
    ev = detect("2026-09-12", now, price_records, "2026-09-11", workloads, TH)
    assert ev["status"] == "changed" and len(ev["price_changes"]) == 1
    assert ev["cost_changes"] == [] and ev["rank_changes"] == [] and not ev["significant"]


def test_cost_change_over_threshold_is_an_event(price_records, workloads):
    now = _with(price_records, "redshift", "compute", "us", 0.40)          # 0.375 → 0.40
    ev = detect("2026-09-12", now, price_records, "2026-09-11", workloads, TH)
    assert [(c["scenario"], c["region"], c["platform"], c["before"], c["after"], c["change_pct"])
            for c in ev["cost_changes"]] == [
        ("W1", "us", "redshift", 900.0, 944.0, 4.9),
        ("W2", "us", "redshift", 600.0, 624.0, 4.0),
        ("W3", "us", "redshift", 360.0, 368.0, 2.2),
    ]
    assert ev["rank_changes"] == [] and ev["significant"] and ev["compared_to"] == "2026-09-11"


def test_rank_change_is_an_event(price_records, workloads):
    now = _with(price_records, "redshift", "compute", "us", 0.80)          # W1 미국 Redshift 900 → 1,648
    ev = detect("2026-09-12", now, price_records, "2026-09-11", workloads, TH)
    assert ev["rank_changes"][0] == {
        "scenario": "W1", "region": "us",
        "before": ["redshift", "bigquery", "snowflake", "databricks"],
        "after": ["bigquery", "snowflake", "redshift", "databricks"],
    }
    assert {(r["scenario"], r["region"]) for r in ev["rank_changes"]} == {("W1", "us"), ("W2", "us"), ("W3", "us")}
```
손계산(로직 검증용 가격, `tests/conftest.py`):
- Redshift 미국 W1 = 8 RPU × 220h × 단가 + 스토리지 240
  - 단가 0.375 → 660 + 240 = **900**
  - 단가 0.40 → 704 + 240 = **944** (+4.9%)
  - 단가 0.80 → 1,408 + 240 = **1,648**
- 같은 조건의 다른 플랫폼(W1 미국): BigQuery 1,320 + 186.26 = **1,506**, Snowflake **1,550**, Databricks **2,056**
- 그래서 Redshift 단가가 0.80이 되면 W1 미국 순위가 바뀐다: Redshift > BigQuery > Snowflake > Databricks → BigQuery > Snowflake > Redshift > Databricks

`tests/test_review_report.py`의 `test_review_lists_changes_against_previous_snapshot`에 추가(import에 `latest_approved_day` 포함):
```python
    assert latest_approved_day("2026-09-11", root=tmp_path) == "2026-09-09"   # 반려(승인 기록 없음)된 09-10은 건너뛴다
```

- [ ] **Step 3: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_events.py tests/test_review_report.py -q`
Expected: FAIL (`ModuleNotFoundError: detect`, `ImportError: latest_approved_day`)

- [ ] **Step 4: 구현**

`publish/review_report.py`의 `previous_snapshot`을 아래 두 함수로 바꾼다:
```python
def latest_approved_day(day: str, root: Path = Path("data/raw")) -> str | None:
    """day보다 앞선 가장 최근의 **승인된** 스냅샷 날짜. 승인 기록이 없는(반려된) 날은 건너뛴다."""
    root = Path(root)
    if not root.exists():
        return None
    approved = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name < day and (p / APPROVED_FILE).exists())
    return approved[-1] if approved else None


def previous_snapshot(day: str, root: Path = Path("data/raw")) -> list[PriceRecord] | None:
    """latest_approved_day의 스냅샷을 읽는다. 승인된 스냅샷이 없으면 None."""
    prev = latest_approved_day(day, root)
    if prev is None:
        return None
    return [r for csv_path in sorted((Path(root) / prev).glob("*.csv")) for r in read_snapshot(csv_path)]
```

`detect/events.py`:
```python
"""E1 변동 감지(Phase 2-2). 오늘 가격을 이전 승인 스냅샷과 비교해 events.json 내용을 만든다.
월 비용은 양쪽 모두 현재 workloads.yaml로 계산한다. 가정이 아니라 가격이 바뀐 효과만 보기 위해서다."""
from __future__ import annotations

from common.schema import REGIONS, PriceRecord
from model.tco import CostRow, PriceBook, estimate, ranking
from publish.review_report import price_changes


def cost_changes(now: list[CostRow], prev: list[CostRow], min_pct: float) -> list[dict]:
    before = {(r.scenario, r.region, r.platform): r.total_usd for r in prev}
    out = []
    for r in now:
        b = before[(r.scenario, r.region, r.platform)]
        pct = round((r.total_usd / b - 1) * 100, 1)
        if abs(pct) >= min_pct:
            out.append({"scenario": r.scenario, "region": r.region, "platform": r.platform,
                        "before": round(b, 2), "after": round(r.total_usd, 2), "change_pct": pct})
    return out


def rank_changes(now: list[CostRow], prev: list[CostRow], scenarios) -> list[dict]:
    out = []
    for sid in scenarios:
        for region in REGIONS:
            b, a = ranking(prev, sid, region), ranking(now, sid, region)
            if a != b:
                out.append({"scenario": sid, "region": region, "before": b, "after": a})
    return out


def detect(day: str, records: list[PriceRecord], previous: list[PriceRecord] | None, compared_to: str | None,
           workloads: dict, thresholds: dict) -> dict:
    min_pct = thresholds["e1_min_cost_change_pct"]
    events = {"day": day, "compared_to": compared_to, "min_cost_change_pct": min_pct,
              "price_changes": price_changes(records, previous), "cost_changes": [], "rank_changes": []}
    if previous is None:
        events["status"] = "first"
    elif not events["price_changes"]:
        events["status"] = "unchanged"
    else:
        events["status"] = "changed"
        now, prev = estimate(PriceBook(records), workloads), estimate(PriceBook(previous), workloads)
        events["cost_changes"] = cost_changes(now, prev, min_pct)
        events["rank_changes"] = rank_changes(now, prev, workloads["scenarios"])
    events["significant"] = bool(events["cost_changes"] or events["rank_changes"])
    return events
```

- [ ] **Step 5: 통과 확인**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: `38 passed`

- [ ] **Step 6: 커밋** (개인정보 검사 → 커밋 → `git ls-files detect` 확인)
```bash
git add config/thresholds.yaml detect publish/review_report.py tests/test_events.py tests/test_review_report.py
git commit -m "feat: detect price, cost and ranking changes against the last approved snapshot" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: 글 초안 (`publish/render_post.py`)

**Files:**
- Create: `publish/render_post.py`, `templates/post_price_change.md.j2`, `tests/test_render_post.py`

**Interfaces:**
- Consumes: `detect(...)` 결과(Task 1), `REGION_LABELS`(publish/review_report.py)
- Produces:
  - `render_post(events: dict) -> str`: 글을 만들고 숫자 검사를 통과해야 돌려준다.
  - `check_numbers(post: str, events: dict) -> None`: 글의 숫자가 `events.json`에 없으면 `ValueError`
  - `PLATFORM_LABELS: dict[str, str]`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_render_post.py`:
```python
from dataclasses import replace

import pytest

from detect.events import detect
from publish.render_post import check_numbers, render_post


def _events(price_records, workloads):
    now = [replace(r, price_usd=0.80) if (r.platform, r.service, r.region) == ("redshift", "compute", "us") else r
           for r in price_records]
    return detect("2026-09-12", now, price_records, "2026-09-11", workloads, {"e1_min_cost_change_pct": 1.0})


def test_post_lists_price_cost_and_rank_changes(price_records, workloads):
    post = render_post(_events(price_records, workloads))
    assert "Redshift serverless-rpu (미국): $0.375 → $0.8 (+113.3%)" in post
    assert "W1 미국 Redshift: $900 → $1,648 (+83.1%)" in post
    assert "W1 미국: Redshift > BigQuery > Snowflake > Databricks → BigQuery > Snowflake > Redshift > Databricks" in post


def test_number_check_rejects_numbers_missing_from_events(price_records, workloads):
    events = _events(price_records, workloads)
    post = render_post(events)
    check_numbers(post, events)                                       # 그대로면 통과
    with pytest.raises(ValueError, match="1,658"):
        check_numbers(post.replace("$1,648", "$1,658"), events)        # 숫자 하나를 바꾸면 게시를 막는다
```

- [ ] **Step 2: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_render_post.py -q`
Expected: FAIL (`ModuleNotFoundError: publish.render_post`)

- [ ] **Step 3: 구현**

`templates/post_price_change.md.j2` (고정 문장에는 숫자를 쓰지 않는다. 숫자는 모두 events에서 온다):
```
# 데이터 플랫폼 월 비용 변동 · {{ e.day }}

{{ e.compared_to }} 승인 가격과 비교해 바뀐 단가와 그 영향입니다. 플랫폼 간 비교는 가정 기반 모델 추정입니다.

## 바뀐 단가
{% for c in e.price_changes %}
- {{ c.platform|platform }} {{ c.sku }} ({{ c.region|region }}): {{ c.before|price }} → {{ c.after|price }}{{ c.change_pct|pct }}
{% endfor %}
{% if e.cost_changes %}

## 월 비용이 ±{{ e.min_cost_change_pct|num }}% 이상 바뀐 조합
{% for c in e.cost_changes %}
- {{ c.scenario }} {{ c.region|region }} {{ c.platform|platform }}: {{ c.before|usd0 }} → {{ c.after|usd0 }}{{ c.change_pct|pct }}
{% endfor %}
{% endif %}
{% if e.rank_changes %}

## 순위 변화 (싼 순서)
{% for r in e.rank_changes %}
- {{ r.scenario }} {{ r.region|region }}: {{ r.before|order }} → {{ r.after|order }}
{% endfor %}
{% endif %}

---
가정과 계산 방법은 대시보드의 "가정 공개"에 있습니다. 이 글은 템플릿으로 자동 생성했고, 게시 전에 사람이 검토합니다.
```

`publish/render_post.py`:
```python
"""E1 이벤트 글 초안(Phase 2-3). 템플릿 문장에 events.json 값만 넣는다.
게시 전 검사: 글에 나온 모든 숫자가 events.json에 있어야 한다(표시 반올림 허용). 없으면 ValueError."""
from __future__ import annotations

import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from publish.review_report import REGION_LABELS

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
PLATFORM_LABELS = {"snowflake": "Snowflake", "databricks": "Databricks", "redshift": "Redshift", "bigquery": "BigQuery"}
NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")   # W1 같은 식별자 속 숫자는 제외한다


def _price(v: float | None) -> str:
    return "없음" if v is None else "$" + f"{v:.6f}".rstrip("0").rstrip(".")


def check_numbers(post: str, events: dict) -> None:
    allowed = [float(t.replace(",", "")) for t in NUMBER.findall(json.dumps(events, ensure_ascii=False))]
    for token in NUMBER.findall(post):
        value = float(token.replace(",", ""))
        decimals = len(token.split(".")[1]) if "." in token else 0
        if not any(round(a, decimals) == value for a in allowed):
            raise ValueError(f"글의 숫자 {token}이(가) events.json에 없다")


def render_post(events: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES), trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    env.filters.update(
        platform=PLATFORM_LABELS.get, region=REGION_LABELS.get, price=_price,
        usd0=lambda v: f"${v:,.0f}", pct=lambda v: "" if v is None else f" ({v:+.1f}%)",
        num=lambda v: f"{v:g}", order=lambda ps: " > ".join(PLATFORM_LABELS[p] for p in ps))
    post = env.get_template("post_price_change.md.j2").render(e=events)
    check_numbers(post, events)
    return post
```

- [ ] **Step 4: 통과 확인**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: `40 passed`

- [ ] **Step 5: 커밋**
```bash
git add publish/render_post.py templates/post_price_change.md.j2 tests/test_render_post.py
git commit -m "feat: price change post draft with number consistency check" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: `pipeline.py` 1단계 개편

**Files:**
- Modify: `pipeline.py`, `publish/review_report.py`(`build_review`에 `significant` 인자), `templates/review.md.j2`, `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `detect`(Task 1), `render_post`(Task 2), `latest_approved_day`, `previous_snapshot`, `build_review`
- Produces:
  - `pipeline.main([])` / `main(["--simulate"])` → `Path`
    - 변화 없음: `data/checks.csv`
    - 변화 있음·첫 스냅샷: `data/raw/<날짜>/review.md`
  - `pipeline.main(["--confirm", DAY])` → `site/index.html`. 시뮬레이션 스냅샷이면 `SystemExit`
  - `record_check(day, result, compared_to, path=CHECKS) -> Path`: 같은 날 다시 실행하면 그 줄을 덮어쓴다.
  - 환경변수 `GITHUB_OUTPUT`이 있으면 `day`, `status`, `significant`를 쓴다(Task 5 워크플로가 읽는다).
  - `build_review(..., significant: bool | None = None)`: 요약에 "글 초안(E1): 있음/없음" 줄을 넣는다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_pipeline.py` 맨 위에 추가:
```python
import datetime as dt
import json
from dataclasses import replace

TODAY = dt.date.today().isoformat()


@pytest.fixture(autouse=True)
def _no_github_output(monkeypatch):
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)   # CI 안에서 테스트가 실제 단계 출력에 쓰지 않게 한다


def _approved(records, day="2000-01-01"):
    write_snapshot(records, day, "all")
    Path(f"data/raw/{day}/approved.txt").write_text("approved", encoding="utf-8")
```

기존 `test_default_run_stops_after_review` 끝에 추가:
```python
    events = json.loads((out.parent / "events.json").read_text(encoding="utf-8"))
    assert events["status"] == "first" and not (out.parent / "post.md").exists()
```

새 테스트 4개:
```python
def test_unchanged_run_only_records_the_check(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _approved(price_records)
    gh_out = tmp_path / "gh_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(gh_out))

    out = pipeline.main([])

    assert out == Path("data/checks.csv")
    assert f"{TODAY},unchanged,2000-01-01" in out.read_text(encoding="utf-8")
    assert not Path("data/raw", TODAY).exists()                  # 변화가 없으면 스냅샷을 만들지 않는다
    assert "status=unchanged" in gh_out.read_text(encoding="utf-8")
    pipeline.main([])                                            # 같은 날 다시 실행해도 한 줄만 남는다
    assert out.read_text(encoding="utf-8").count(TODAY) == 1


def test_changed_run_writes_events_post_and_review(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _approved([replace(r, price_usd=0.30) if (r.platform, r.service, r.region) == ("redshift", "compute", "us") else r
               for r in price_records])

    out = pipeline.main([])

    events = json.loads((out.parent / "events.json").read_text(encoding="utf-8"))
    assert events["status"] == "changed" and events["significant"] and events["compared_to"] == "2000-01-01"
    assert "$0.3 → $0.375 (+25.0%)" in (out.parent / "post.md").read_text(encoding="utf-8")
    assert "글 초안(E1): 있음" in out.read_text(encoding="utf-8")
    assert f"{TODAY},review,2000-01-01" in Path("data/checks.csv").read_text(encoding="utf-8")


def test_simulated_snapshot_is_marked_and_cannot_be_confirmed(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _approved(price_records)

    out = pipeline.main(["--simulate"])

    assert out.read_text(encoding="utf-8").startswith("> **시뮬레이션:**")
    assert not Path("data/checks.csv").exists()                  # 시뮬레이션은 매일 확인 기록에 남기지 않는다
    with pytest.raises(SystemExit, match="시뮬레이션"):
        pipeline.main(["--confirm", TODAY])
    assert not Path("data/raw", TODAY, "approved.txt").exists()


def test_rerun_after_same_day_approval_is_refused(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _approved(price_records, day=TODAY)

    with pytest.raises(SystemExit, match="이미 승인"):
        pipeline.main([])
```

- [ ] **Step 2: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_pipeline.py -q`
Expected: 새 테스트 4개와 보강한 기존 테스트 1개가 FAIL(`events.json` 없음, `--simulate` 인자 없음 등)

- [ ] **Step 3: 구현**

`templates/review.md.j2`의 머리 안내와 요약을 바꾼다:
```
> **파이프라인은 여기서 멈춰 있습니다.** 아래 내용을 확인하고 판단해 주세요.
> - **컨펌:** GitHub 검토 PR이면 **Merge**. 로컬이면 `.venv\Scripts\python.exe pipeline.py --confirm {{ day }}` → 화면 생성, 승인 기록(`approved.txt`) → 스냅샷 커밋
> - **반려:** GitHub 검토 PR이면 **Close**. 로컬이면 `data/raw/{{ day }}/` 폴더를 커밋하지 말고 지운 뒤, 원인을 고쳐 `pipeline.py`를 다시 실행

## 1. 요약
- 수집 가격: {{ records|length }}행{{ counts_text }}
- 이전 승인 스냅샷 대비: {{ changes_summary }}
{% if significant is not none %}
- 글 초안(E1): {{ "있음 (post.md)" if significant else "없음 (월 비용 변화가 기준 미만이고 순위 변화도 없다)" }}
{% endif %}
```
(요약의 T1·T2 줄과 나머지 섹션은 그대로 둔다.)

`publish/review_report.py`의 `build_review`에 인자 `significant: bool | None = None`을 추가하고, `render(...)` 호출에 `significant=significant`를 넘긴다.

`pipeline.py` 전체:
```python
"""파이프라인. 중간 검토 체크포인트(CLAUDE.md 규칙 14)가 있는 2단계 구조다.

1단계  .venv\\Scripts\\python.exe pipeline.py [--simulate]
       수집 → 이전 승인 스냅샷과 비교
       · 변화 없음: data/checks.csv에 한 줄 기록하고 끝낸다(스냅샷을 만들지 않는다)
       · 변화 있음(또는 첫 스냅샷): 스냅샷, review.md, events.json, (E1이면) post.md → 멈춤
2단계  .venv\\Scripts\\python.exe pipeline.py --confirm <날짜>
       사용자가 검토 보고서를 컨펌한 뒤 실행한다. 사이트 생성 + 승인 기록(approved.txt)
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
from dataclasses import replace
from pathlib import Path

import yaml

from collectors import aws_prices, azure_prices, manual_prices
from common.schema import REGIONS, PriceRecord, read_snapshot, write_snapshot
from detect.events import detect
from model.tco import PriceBook, estimate, seoul_premiums, t1_verdict, t2_verdict
from publish.render_post import render_post
from publish.render_site import render
from publish.review_report import (APPROVED_FILE, REVIEW_FILE, build_review, latest_approved_day,
                                   previous_snapshot)

RAW = Path("data/raw")
CHECKS = Path("data/checks.csv")
EVENTS_FILE = "events.json"
POST_FILE = "post.md"
SIMULATED = ("redshift", "compute", "us")     # --simulate: 이 단가만 5% 올려 검토 PR 흐름을 검증한다
SIMULATED_TAG = " (simulated)"
SIMULATION_NOTICE = "> **시뮬레이션:** 검증용 가짜 변동(Redshift 미국 RPU +5%)이다. 머지하지 말고 닫는다.\n\n"


def load_yaml(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def analyze(records: list[PriceRecord]) -> dict:
    workloads = load_yaml("data/manual/workloads.yaml")
    thresholds = load_yaml("config/thresholds.yaml")
    book = PriceBook(records)
    premiums = seoul_premiums(records)
    return {
        "workloads": workloads,
        "thresholds": thresholds,
        "rows": estimate(book, workloads),
        "premiums": premiums,
        "t1_by_region": {region: t1_verdict(book, workloads, thresholds["t1_sensitivity"], region) for region in REGIONS},
        "t2": t2_verdict(premiums, thresholds["t2_min_spread_pp"]),
    }


def record_check(day: str, result: str, compared_to: str | None, path: Path = CHECKS) -> Path:
    """매일 확인 기록(day,result,compared_to). 같은 날 다시 실행하면 그 줄을 덮어쓴다."""
    rows = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r["day"] != day]
    rows.append({"day": day, "result": result, "compared_to": compared_to or ""})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["day", "result", "compared_to"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["day"]))
    return path


def write_outputs(**values: str) -> None:
    """GitHub Actions 단계 출력(GITHUB_OUTPUT). 로컬에서는 아무것도 하지 않는다."""
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as f:
            f.writelines(f"{k}={v}\n" for k, v in values.items())


def simulate_change(records: list[PriceRecord], factor: float = 1.05) -> list[PriceRecord]:
    return [replace(r, price_usd=round(r.price_usd * factor, 6), source=r.source + SIMULATED_TAG)
            if (r.platform, r.service, r.region) == SIMULATED else r for r in records]


def collect_and_review(simulate: bool = False) -> Path:
    """1단계: 변화가 있으면 검토 자료까지만 만들고 멈춘다. 화면 생성과 커밋은 컨펌 이후에 한다."""
    day = dt.date.today().isoformat()
    if (RAW / day / APPROVED_FILE).exists():
        raise SystemExit(f"{day} 스냅샷은 이미 승인됐다. 같은 날 다시 수집하지 않는다.")
    # 세 수집기가 모두 성공한 뒤에만 쓴다(수동 가격표 게이트에서 멈추면 아무것도 남기지 않는다).
    collected = {
        "aws": aws_prices.collect(day),
        "azure": azure_prices.collect(day),
        "manual": manual_prices.collect(),
    }
    if simulate:
        collected["aws"] = simulate_change(collected["aws"])
    records = [r for recs in collected.values() for r in recs]
    result = analyze(records)
    compared_to = latest_approved_day(day, RAW)
    events = detect(day, records, previous_snapshot(day, RAW), compared_to, result["workloads"], result["thresholds"])
    write_outputs(day=day, status=events["status"], significant=str(events["significant"]).lower())

    if events["status"] == "unchanged":
        out = record_check(day, "unchanged", compared_to)
        print(f"변화 없음({compared_to} 승인 스냅샷과 같다). 기록: {out}")
        return out

    for name, recs in collected.items():
        write_snapshot(recs, day, name, root=RAW)
    folder = RAW / day
    review = folder / REVIEW_FILE
    text = build_review(day, records, events["price_changes"], result["rows"], result["t1_by_region"], result["t2"],
                        counts={name: len(recs) for name, recs in collected.items()},
                        significant=events["significant"])
    review.write_text((SIMULATION_NOTICE if simulate else "") + text, encoding="utf-8")
    (folder / EVENTS_FILE).write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if events["significant"]:
        (folder / POST_FILE).write_text(render_post(events), encoding="utf-8")
    if not simulate:
        record_check(day, "review", compared_to)
    print(f"검토 보고서: {review}")
    print(f"검토 후 컨펌: 검토 PR Merge, 또는 로컬에서 .venv\\Scripts\\python.exe pipeline.py --confirm {day}")
    return review


def confirm(day: str) -> Path:
    """2단계: 검토 보고서가 있는 스냅샷만 반영한다. 사이트를 만들고 승인 기록을 남긴다."""
    snapshot = RAW / day
    if not (snapshot / REVIEW_FILE).exists():
        raise SystemExit(f"{snapshot / REVIEW_FILE}가 없다. 검토 보고서가 없는 스냅샷은 반영하지 않는다(먼저 pipeline.py 실행).")
    records = [r for p in sorted(snapshot.glob("*.csv")) for r in read_snapshot(p)]
    if any(r.source.endswith(SIMULATED_TAG) for r in records):
        raise SystemExit(f"{day}는 시뮬레이션 스냅샷이다. 반영하지 않는다.")
    result = analyze(records)
    price_dates: dict[str, str] = {}
    for r in records:
        price_dates[r.platform] = max(price_dates.get(r.platform, ""), r.fetched_at)
    out = render(result["rows"], result["premiums"], result["t1_by_region"], result["t2"], result["workloads"],
                 price_dates, built_on=day)
    (snapshot / APPROVED_FILE).write_text(f"approved_at: {dt.datetime.now().isoformat(timespec='seconds')}\n",
                                          encoding="utf-8")
    print(f"site written: {out}")
    return out


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="1단계: 수집·비교·검토 자료 작성 후 멈춤 / 2단계: --confirm으로 반영")
    parser.add_argument("--confirm", metavar="DAY", help="검토 보고서를 컨펌한 스냅샷(DAY)으로 사이트를 만든다")
    parser.add_argument("--simulate", action="store_true", help="검증용 가짜 변동을 넣는다(검토 PR 흐름 확인용, 머지 금지)")
    args = parser.parse_args(argv)
    return confirm(args.confirm) if args.confirm else collect_and_review(simulate=args.simulate)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 통과 확인**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: `44 passed`

- [ ] **Step 5: 실제 실행 1회 (로컬)**

Run: `$env:PYTHONIOENCODING='utf-8'; .venv\Scripts\python.exe pipeline.py`
Expected: 오늘 가격이 2026-09-11 승인본과 같으면 `변화 없음(2026-09-11 ...)`이 나오고 `data/checks.csv`가 생긴다. 다르면 검토 보고서가 생긴다. 이 경우 사용자에게 보고하고 멈춘다(규칙 14).

- [ ] **Step 6: 커밋** (`data/checks.csv`도 함께 커밋한다. 변화가 있어 스냅샷이 생겼으면 그 폴더는 컨펌 전이라 커밋하지 않는다)
```bash
git add pipeline.py publish/review_report.py templates/review.md.j2 tests/test_pipeline.py data/checks.csv
git commit -m "feat: skip unchanged days, write events and post drafts for review, add simulation mode" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Google Sheets 적재 모듈 (`publish/sheets_log.py`, 연결은 2-5에서)

**Files:**
- Create: `publish/sheets_log.py`, `tests/test_sheets_log.py`
- Modify: `requirements.txt`(`google-auth>=2.30`), `.gitignore`(`/secrets/`)

**Interfaces:**
- Consumes: `events.json`(Task 3), `read_snapshot`
- Produces:
  - `rows_from_events(events: dict, commit_url: str = "") -> list[list]`: 단가 변화 1건이 한 행이다.
  - `baseline_rows(day: str, records: list[PriceRecord], commit_url: str = "") -> list[list]`: 머리글 + 현재 단가(기준선). 처음 연결할 때 한 번 쓴다.
  - `append_rows(rows: list[list], sheet_id: str, session) -> int`: 첫 번째 시트 탭의 `A:J`에 덧붙인다. 행이 없으면 호출하지 않는다.
  - `session_from_env()`: `GOOGLE_SA_KEY`(JSON 문자열)로 `AuthorizedSession`을 만든다.
  - CLI: `python -m publish.sheets_log --events data/raw/<날짜>/events.json` 또는 `--baseline <승인 날짜>`, 선택 인자 `--commit-url`

- [ ] **Step 1: 의존성**

`requirements.txt`에 `google-auth>=2.30`을 추가하고 `.venv\Scripts\python.exe -m pip install -r requirements.txt`를 실행한다. 설치된 버전은 CLAUDE.md 5절에 기록한다. `.gitignore`에 `/secrets/`를 추가한다(키 파일은 저장소 밖에 두는 것이 원칙이고, 이것은 실수 방지용이다).

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/test_sheets_log.py`:
```python
from publish.sheets_log import HEADER, append_rows, baseline_rows, rows_from_events


class FakeResponse:
    def __init__(self, n):
        self.n = n

    def raise_for_status(self):
        pass

    def json(self):
        return {"updates": {"updatedRows": self.n}}


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, **kw):
        self.calls.append((url, kw))
        return FakeResponse(len(kw["json"]["values"]))


def test_rows_from_events_one_row_per_price_change():
    events = {"day": "2026-09-12", "compared_to": "2026-09-11", "price_changes": [
        {"platform": "redshift", "service": "compute", "sku": "serverless-rpu", "region": "us",
         "before": 0.375, "after": 0.4, "change_pct": 6.7}]}
    assert rows_from_events(events, "https://example.invalid/commit/abc") == [
        ["2026-09-12", "2026-09-11", "redshift", "compute", "serverless-rpu", "us", 0.375, 0.4, 6.7,
         "https://example.invalid/commit/abc"]]


def test_append_posts_raw_values_to_first_sheet():
    s = FakeSession()
    assert append_rows([["a", 1]], "SHEET_ID", s) == 1
    url, kw = s.calls[0]
    assert url == "https://sheets.googleapis.com/v4/spreadsheets/SHEET_ID/values/A%3AJ:append"
    assert kw["params"] == {"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}
    assert kw["json"] == {"values": [["a", 1]]}
    assert append_rows([], "SHEET_ID", s) == 0 and len(s.calls) == 1   # 적재할 행이 없으면 호출하지 않는다


def test_baseline_starts_with_header_and_lists_every_price(price_records):
    rows = baseline_rows("2026-09-11", price_records)
    assert rows[0] == HEADER and len(rows) == 1 + len(price_records)
    assert rows[1][:2] == ["2026-09-11", "기준선"] and rows[1][6] == ""
```

- [ ] **Step 3: 실패 확인**

Run: `.venv\Scripts\python.exe -m pytest tests/test_sheets_log.py -q`
Expected: FAIL (`ModuleNotFoundError: publish.sheets_log`)

- [ ] **Step 4: 구현**

`publish/sheets_log.py`:
```python
"""컨펌(검토 PR 머지) 뒤 가격 변동 이력을 사용자의 비공개 Google 스프레드시트에 쌓는다(Phase 2-2b).
- 인증: 서비스 계정 키 JSON(환경변수 GOOGLE_SA_KEY, GitHub Secret). 키 내용은 출력하거나 파일로 남기지 않는다.
- 시트: 환경변수 PRICE_SHEET_ID. 첫 번째 시트 탭의 A:J 열에 행을 덧붙인다.
- 정본은 Git의 CSV 스냅샷이고, 시트는 사용자가 보는 기록장이다."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import quote

from common.schema import PriceRecord, read_snapshot

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
APPEND_URL = "https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range}:append"
RANGE = "A:J"
HEADER = ["감지일", "비교 기준일", "플랫폼", "항목", "SKU", "리전", "이전 단가", "새 단가", "변동률(%)", "커밋"]


def _blank(v):
    return "" if v is None else v


def rows_from_events(events: dict, commit_url: str = "") -> list[list]:
    return [[events["day"], _blank(events["compared_to"]), c["platform"], c["service"], c["sku"], c["region"],
             _blank(c["before"]), _blank(c["after"]), _blank(c["change_pct"]), commit_url]
            for c in events["price_changes"] or []]


def baseline_rows(day: str, records: list[PriceRecord], commit_url: str = "") -> list[list]:
    ordered = sorted(records, key=lambda r: (r.platform, r.service, r.sku, r.region))
    return [HEADER] + [[day, "기준선", r.platform, r.service, r.sku, r.region, "", r.price_usd, "", commit_url]
                       for r in ordered]


def append_rows(rows: list[list], sheet_id: str, session) -> int:
    if not rows:
        return 0
    url = APPEND_URL.format(sheet_id=quote(sheet_id, safe=""), range=quote(RANGE, safe=""))
    resp = session.post(url, params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
                        json={"values": rows}, timeout=30)
    resp.raise_for_status()
    return resp.json()["updates"]["updatedRows"]


def session_from_env():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2 import service_account

    info = json.loads(os.environ["GOOGLE_SA_KEY"])
    return AuthorizedSession(service_account.Credentials.from_service_account_info(info, scopes=SCOPES))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="승인된 가격 변동을 Google 스프레드시트에 적재한다")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--events", type=Path, help="승인된 스냅샷의 events.json")
    group.add_argument("--baseline", metavar="DAY", help="처음 한 번: 승인 스냅샷 DAY의 단가를 기준선으로 기록")
    parser.add_argument("--commit-url", default="")
    args = parser.parse_args(argv)
    if args.events:
        rows = rows_from_events(json.loads(args.events.read_text(encoding="utf-8")), args.commit_url)
    else:
        folder = Path("data/raw") / args.baseline
        if not (folder / "approved.txt").exists():
            raise SystemExit(f"{args.baseline}는 승인된 스냅샷이 아니다.")
        records = [r for p in sorted(folder.glob("*.csv")) for r in read_snapshot(p)]
        rows = baseline_rows(args.baseline, records, args.commit_url)
    n = append_rows(rows, os.environ["PRICE_SHEET_ID"], session_from_env())
    print(f"시트에 {n}행을 추가했다.")
    return n


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 통과 확인**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: `47 passed`

- [ ] **Step 6: (선택, 사용자 2-0c가 끝난 경우만) 실제 기준선 1회 적재**
- 사용자가 자기 PowerShell에서 환경변수 두 개를 직접 설정한다. Claude는 키를 보지 않는다.
  - `$env:GOOGLE_SA_KEY = Get-Content <키 파일 경로> -Raw`
  - `$env:PRICE_SHEET_ID = '<시트ID>'`
- 같은 창에서 `.venv\Scripts\python.exe -m publish.sheets_log --baseline 2026-09-11`을 실행한다.
- 시트에 머리글 1행 + 18행이 추가되면 된다. 2-0c가 아직이면 이 단계는 2-7로 미룬다.

- [ ] **Step 7: 커밋** (개인정보 검사에 `"private_key"` 패턴을 포함한다)
```bash
git add publish/sheets_log.py tests/test_sheets_log.py requirements.txt .gitignore
git commit -m "feat: append approved price changes to a Google Sheet via service account" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: GitHub 연결 + 수집 워크플로 (`collect.yml`)

**Files:**
- Create: `.gitattributes`, `.github/workflows/collect.yml`

**Interfaces:**
- Consumes: `pipeline.py`의 `GITHUB_OUTPUT` 출력 `day`, `status`(`unchanged`/`changed`/`first`), `significant`, `data/raw/<날짜>/review.md`, `post.md`, `data/checks.csv`
- Produces:
  - main에 봇 커밋 `chore: price check <날짜> (<결과>)`
  - 변화가 있으면 PR `review/pending → main`
    - 제목: `가격 검토 <날짜>`
    - 본문: `review.md`, 그리고 글 초안이 있으면 `post.md`
  - 시뮬레이션은 `review/simulated` 브랜치, 제목 `[시뮬레이션·머지 금지] …`

**사전 준비 (2-0, 사용자. Claude는 명령을 안내하고 확인을 받은 뒤에만 실행한다)**
1. **작성자 이름 공개 확인(규칙 11):** 지금까지의 커밋에 전역 설정의 작성자 이름이 들어 있다. push하면 공개된다. Claude가 `git log --format='%an' | sort -u` 결과를 보여 주면, 사용자가 공개해도 되는지 답한다. 바꾸려면 push 전에 이력을 다시 써야 한다.
2. **`gh auth refresh -s workflow`:** 사용자가 브라우저에서 승인한다. 워크플로 파일을 push하려면 이 권한이 필요하다 [확인: 현재 토큰에 없음].
3. **공개 저장소 생성:** 사용자가 웹에서 만들거나, 승인하면 Claude가 `gh repo create <이름> --public --source . --remote origin`을 실행한다(push는 하지 않는다).
4. **Actions 설정 2개:** Settings > Actions > General에서 "Read and write permissions"와 "Allow GitHub Actions to create and approve pull requests"를 켠다. 사용자가 웹에서 하거나, 승인하면 Claude가 아래 명령을 실행한다.
   ```
   gh api -X PUT repos/<owner>/<repo>/actions/permissions/workflow -f default_workflow_permissions=write -F can_approve_pull_request_reviews=true
   ```
5. Secret `SEC_USER_AGENT`는 Phase 4(SEC 수집)에서 등록한다. Pages 소스 설정은 2-5에서 한다.

- [ ] **Step 1: `.gitattributes` (2-0b)**
```
* text=auto eol=lf
```
Run: `git add --renormalize .` → `git status`
Expected: 저장소 안의 파일은 이미 LF라서 내용 변경이 없거나 거의 없다. 변경이 있으면 목록을 보고 확인한 뒤 커밋한다.

- [ ] **Step 2: `.github/workflows/collect.yml`**
```yaml
name: collect
# 매일 가격 수집 → 이전 승인 스냅샷과 비교 → 변화가 있으면 검토 PR을 올리고 멈춘다(CLAUDE.md 규칙 14).
# 매일 스케줄은 게시 워크플로(2-5)가 준비된 뒤에 켠다(결정 D3). 그 전에는 수동 실행만 한다.
on:
  workflow_dispatch:
    inputs:
      simulate:
        description: "검증용 가짜 변동(Redshift 미국 RPU +5%). 이 PR은 머지하지 말고 닫는다"
        type: boolean
        default: false
  # schedule:
  #   - cron: "17 0 * * *"   # 00:17 UTC = 09:17 KST, 정각 혼잡 회피 (2-5 이후 활성화)

permissions:
  contents: write
  pull-requests: write

concurrency:
  group: collect
  cancel-in-progress: false

jobs:
  collect:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    env:
      PYTHONIOENCODING: utf-8
      SIMULATE: ${{ inputs.simulate && 'true' || 'false' }}
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.11"
          cache: pip
      - run: pip install -r requirements.txt
      - run: python -m pytest -q
      - name: git identity
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
      - id: run
        run: python pipeline.py $([ "$SIMULATE" = "true" ] && echo --simulate)
      - name: record daily check on main
        if: env.SIMULATE != 'true'
        run: |
          git add data/checks.csv
          git diff --cached --quiet || git commit -m "chore: price check ${{ steps.run.outputs.day }} (${{ steps.run.outputs.status }})"
          git push origin HEAD:main
      - name: close stale review PR when prices match the approved snapshot
        if: steps.run.outputs.status == 'unchanged'
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          if [ "$(gh pr view review/pending --json state -q .state 2>/dev/null)" = "OPEN" ]; then
            gh pr close review/pending --delete-branch --comment "가격이 승인 스냅샷과 같아져 검토할 것이 없다."
          fi
      - name: open or update review PR
        if: steps.run.outputs.status != 'unchanged'
        env:
          GH_TOKEN: ${{ github.token }}
          DAY: ${{ steps.run.outputs.day }}
        run: |
          BRANCH=review/pending
          TITLE="가격 검토 $DAY"
          if [ "$SIMULATE" = "true" ]; then BRANCH=review/simulated; TITLE="[시뮬레이션·머지 금지] $TITLE"; fi
          git switch -c "$BRANCH"
          git add "data/raw/$DAY"
          git commit -m "review: price snapshot $DAY"
          git push --force origin "$BRANCH"
          BODY="$RUNNER_TEMP/body.md"
          cat "data/raw/$DAY/review.md" > "$BODY"
          if [ -f "data/raw/$DAY/post.md" ]; then
            printf '\n---\n## 글 초안 (post.md)\n\n' >> "$BODY"
            cat "data/raw/$DAY/post.md" >> "$BODY"
          fi
          if [ "$(gh pr view "$BRANCH" --json state -q .state 2>/dev/null)" = "OPEN" ]; then
            gh pr edit "$BRANCH" --title "$TITLE" --body-file "$BODY"
          else
            gh pr create --base main --head "$BRANCH" --title "$TITLE" --body-file "$BODY"
          fi
```
- 설계 메모
  - 매일 확인 기록(`checks.csv`)은 항상 main에 먼저 커밋한다. 검토 브랜치는 그 위에서 새 날짜 폴더만 더한다. 그래서 검토 PR과 main이 충돌하지 않는다.
  - 대기 중인 검토 PR은 항상 하나다(`review/pending`을 강제로 갱신한다). 아직 머지하지 않은 날의 변화도 "마지막 승인본 대비"로 다시 계산되므로, 최신 날짜 하나만 보면 된다.
  - GITHUB_TOKEN으로 한 push와 PR은 다른 워크플로를 트리거하지 않는다. 그래서 봇 커밋이 게시를 일으키지 않는다. 게시는 사람이 머지할 때만 일어난다(2-5에서 실측한다).

- [ ] **Step 3: 로컬 점검**
- `.venv\Scripts\python.exe -c "import yaml; yaml.safe_load(open('.github/workflows/collect.yml', encoding='utf-8'))"`로 문법을 확인한다.
- `.venv\Scripts\python.exe -m pytest -q`의 결과는 47 passed여야 한다.

- [ ] **Step 4: push 전 전체 이력 개인정보 검사**
- 모든 커밋의 내용(`git log -p --all`)에서 아래 패턴을 찾는다. 결과는 0건이어야 한다. 커밋 작성자 이메일은 noreply 주소 두 종류만 있어야 한다.
  - 이메일 주소(`noreply@anthropic.com`과 GitHub noreply 주소는 제외)
  - `C:\Users\`
  - 개인 프로젝트 ID 패턴
  - `"private_key"`

- [ ] **Step 5: 커밋 → (사용자 승인 후) push**
```bash
git add .gitattributes .github/workflows/collect.yml
git commit -m "ci: daily price collection workflow that opens a review PR on changes" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
git push -u origin main
```

- [ ] **Step 6: 실제 실행 1회**
- **UTC 2026-09-12 이후에 실행한다.** 그 전에는 승인 스냅샷(2026-09-11)이 있어 같은 날 재수집 가드에 걸려 실패한다(Task 3에서 확인).
- `gh workflow run collect.yml`을 실행하고, `gh run watch`로 끝까지 지켜본다.
- 결과는 둘 중 하나다.
  - 가격이 2026-09-11 승인본과 같으면 main에 `chore: price check <날짜> (unchanged)` 커밋이 생기고 PR은 없다. Actions 서버에서 AWS·Azure 호출이 되는 것도 여기서 확인된다.
  - 실제 가격이 바뀌었으면 검토 PR이 생긴다. 사용자에게 보고하고, 머지하지 않고 둔다(D3: 2-5 전까지는 머지하지 않는다).

- [ ] **Step 7: 시뮬레이션으로 검토 PR 흐름 확인**
1. `gh workflow run collect.yml -f simulate=true`를 실행한다. PR `[시뮬레이션·머지 금지] 가격 검토 <날짜>`가 생기고, 본문에 검토 보고서와 글 초안이 있어야 한다.
2. 한 번 더 실행한다. 새 PR이 생기지 않고 같은 PR이 갱신돼야 한다.
3. 사용자가 PR을 **Close**한다(반려 흐름). main에는 아무 변화가 없어야 한다. `data/checks.csv`에도 시뮬레이션 기록이 남지 않아야 한다.

- [ ] **Step 8: 문서 갱신 → 커밋 → push(승인 후) → 보고하고 멈춘다**
- `git pull`로 봇 커밋을 받는다.
- CLAUDE.md와 phase-2 진행계획을 갱신한다.
- 다음은 **2-5a 디자인 게이트**다. 대시보드를 만들기 전에 멈추고 사용자 템플릿을 기다린다.

---

## 멈춤: 2-5a 대시보드 디자인 게이트 (규칙 13)
- 사용자가 마음에 드는 대시보드 템플릿을 준다.
- Claude는 그 템플릿의 레이아웃, 색, 타이포, 차트 스타일을 분석해 디자인 적용 계획을 쓰고, 승인을 받는다.

## 2-5a 이후 개요 (템플릿을 받은 뒤 별도 계획으로 상세화한다)
| Task | 내용 |
|---|---|
| 6 | 템플릿 기반 대시보드 디자인 적용(`templates/site/`, `publish/render_site.py`). 가격 변동 글 아카이브 페이지 포함 |
| 7 | `publish.yml`(사람이 검토 PR을 머지해 main에 push되면 실행) |
|   | - 새 스냅샷마다 `pipeline.py --confirm <날짜>` 실행 → `approved.txt`를 봇이 커밋(GITHUB_TOKEN이라 재실행 루프가 없다) |
|   | - Pages 배포 |
|   | - `sheets_log --events` 적재. 실패하면 Issue를 연다 |
|   | - Pages 소스 설정(사용자) → 매일 스케줄 활성화(D3) |
| 8 | 가격 확인 알림(2-6): 분기 1회 Snowflake·Databricks 확인 Issue, BigQuery 가격 문자열 지문 비교 |
| 9 | 종단 검증(2-7) |
|   | - 사람이 머지했을 때 `publish.yml`이 트리거되는지 실측 |
|   | - 반려하면 아무것도 진행되지 않는지 |
|   | - 멱등성, 시트 적재 |
|   | - 첫 실제 게시 전에 사용자가 확인 |
