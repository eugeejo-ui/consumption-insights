# Phase 2: 자동 수집 + 변동 감지 + 승인 흐름 + 아카이브 게시

| 항목 | 내용 |
|---|---|
| 상태 | 대기 (Phase 1 게이트 이후) |
| 목표 | 매일 자동으로 가격을 모은다. 의미 있는 변동이 생기면 글 초안을 PR로 올리고, 사용자가 머지하면 GitHub Pages에 게시한다 |
| 선행 조건 | Phase 1 완료, 사용자의 GitHub 준비(2-0) |
| 코드 단위 계획 | 착수할 때 `docs/plans/phase2-*.md`로 작성하고 승인을 받는다 |

## 흐름
```
[매일 00:17 UTC, collect.yml]
수집 → 스냅샷 커밋 → 이전 값과 비교(diff.py)
                          ├ 변동 없음 → 끝
                          └ 변동 있음 → events.json → 템플릿 글 초안 → 숫자 일치 검사 → PR(needs-approval)
                                                                                      │
                                                                     [사용자가 PR 머지 = 승인]
                                                                                      │
                                                   publish.yml → 사이트·아카이브 빌드 → GitHub Pages
```

## 진행 과정
| 단계 | 작업 | 담당 | 산출물 | 완료 기준 |
|---|---|---|---|---|
| 2-0 | GitHub 준비: `gh auth refresh -s workflow`(브라우저 승인), 공개 저장소 생성, Actions 설정 2개(PR 생성 허용, 토큰 쓰기 권한), Pages 소스를 Actions로, Secret `SEC_USER_AGENT` | U | 원격 저장소 | 설정 5개 완료 |
| 2-0b | `.gitattributes`(`* text=auto eol=lf`) 검토 | C | `.gitattributes` | Windows와 CI의 줄바꿈 일치 |
| 2-1 | 매일 수집 워크플로 | C | `.github/workflows/collect.yml` | Actions 서버에서 AWS·Azure·SEC 호출 성공, 스냅샷 커밋 |
| 2-2 | 변동 감지 | C | `detect/diff.py`, `events.json` | 가짜 변동을 주입하면 이벤트가 생성되고, 변동이 없으면 이벤트가 없다 |
| 2-3 | 글 생성 | C | `templates/post_price_change.md.j2`, `publish/render_post.py` | 숫자 하나를 바꿔 넣으면 검사가 실패한다 |
| 2-4 | 초안 PR 생성 | C | `posts/` 초안, PR | 이벤트가 있으면 PR 1건이 생긴다 |
| 2-5 | 게시 워크플로 | C | `.github/workflows/publish.yml` | main에 push하면 Pages가 갱신된다 |
| 2-6 | 가격 확인 알림 | C | Issue 생성 로직 | 분기 알림이 생성되고, BigQuery 지문이 바뀌면 Issue가 열린다 |
| 2-7 | 종단 검증 | C+U | 검증 기록 | 사람이 머지했을 때 publish.yml이 실행된다(실측). 멱등성과 `--dry-run` 확인 |

## 이벤트 기준 (사전 고정, `config/thresholds.yaml`)
- **E1 가격 변동:** 어떤 시나리오든 월 비용이 ±1% 이상 바뀌거나 순위가 바뀌면 이벤트다. 사람이 수동 가격표를 고친 경우도 포함한다.
- **게시 빈도:** 같은 날 생긴 이벤트는 하나로 합치고, 하루 최대 1건만 게시한다.
- **게시 전 검사:** 글에 나오는 모든 숫자가 `events.json`에 있어야 한다. 하나라도 없으면 게시를 중단한다.

## 가격 확인 알림 (약관 준수)
| 대상 | 방식 | 이유 |
|---|---|---|
| Snowflake, Databricks | 분기 1회 "가격표 확인" Issue(공식 링크 + 체크리스트). 자동 접근은 하지 않는다 | 사이트 약관이 자동 모니터링을 금지한다 [확인] |
| BigQuery | 하루 1회 리전별 가격 문자열의 지문을 비교한다 | Google 약관은 robots.txt만 지키면 허용한다 [확인] |

## 사용자가 할 일
- 2-0의 GitHub 준비. 브라우저 승인과 설정 변경은 직접 해야 한다.
- 초안 PR을 검토하고 머지한다. 머지가 곧 게시 승인이다.
- 분기마다 Snowflake·Databricks 가격을 확인하고, 바뀌었으면 수동 가격표를 PR로 고친다.

## 위험과 대응 (Phase 0에서 확인한 사항)
| 위험 | 대응 |
|---|---|
| GITHUB_TOKEN으로 머지하면 다른 워크플로가 실행되지 않는다 | 사람이 머지하면 push로 트리거되는지 2-7에서 실측한다. 자동 모드(Phase 5)에서는 같은 실행 안에서 배포한다 |
| 공개 저장소는 60일 무활동이면 스케줄이 멈춘다 | 매일 스냅샷을 커밋하고, 재활성화 API를 보조 수단으로 둔다 |
| cron이 정각 혼잡으로 늦게 실행된다 | 00:17 UTC로 잡는다 |
| 새 저장소 기본값: 워크플로 PR 생성 금지, 토큰 읽기 전용 | 2-0에서 설정을 바꾼다 |
| gh 토큰에 `workflow` 권한이 없다 | `gh auth refresh -s workflow`를 실행하고, 사용자가 브라우저에서 승인한다 |
| 봇이 만든 PR의 CI는 승인이 필요하다(2026-06 변경) | 받아들인다 |
| 줄바꿈 CRLF/LF 불일치 | 2-0b에서 처리한다 |

## 완료 기준 (게이트)
- 2-7 검증을 모두 통과한다.
- 첫 실제 게시 전에 사용자가 확인한다.
- 위 두 가지가 끝나면 Phase 3을 결정하고 계획한다.
