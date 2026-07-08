# 03_drafts — Obsidian 검수 대기 초안

이 폴더에는 AI Frontier 블로그의 **검수 대기 초안**이 저장됩니다.  
매일 오전 8시 30분 경 GitHub Actions가 자동 생성하며, Obsidian Git을 통해 동기화됩니다.

---

## 검수 절차 (약 10분)

| 단계 | 작업 | 위치 |
|---|---|---|
| 1 | 이 폴더의 최신 `.md` 파일 열기 | Obsidian |
| 2 | `VERIFY:` 항목 사실 확인 | 브라우저 + 원본 소스 |
| 3 | HTML 파일로 레이아웃 확인 | `blog/drafts/*.html` |
| 4 | 승인 시 → HTML을 `blog/posts/` 로 이동 | Finder / Obsidian |
| 5 | `blog/index.html` 에 포스트 카드 추가 | Obsidian / 코드 에디터 |
| 6 | `04_published/index.md` 에 한 줄 기록 | Obsidian |
| 7 | Obsidian Git → Commit & Push | Obsidian Git 플러그인 |

---

## 초안 파일 frontmatter 구조

```yaml
---
status: draft           # draft → approved (검수 완료 후 변경)
date: 2026-01-01
slug: post-url-slug
title: "포스트 제목"
description: "메타 설명 (155자 이하)"
category: anthropic | karpathy | news | tools
source_url: "https://원본링크"
html_draft: "blog/drafts/2026-01-01-post-url-slug.html"
editor_notes:
  - "VERIFY: 확인이 필요한 주장"
  - "개선된 내용"
generated_by:
  stage1: "Gemini gemini-3.5-flash"
  stage2: "Claude claude-sonnet-4-6"
---
```

---

## 폐기 기준

- 인텔 소스가 2주 이상 오래된 뉴스인 경우
- VERIFY 항목 사실 확인 결과 틀린 내용이 핵심인 경우
- 더 나은 토픽의 초안이 있어 우선순위가 밀린 경우

폐기 시 파일명 앞에 `REJECTED-` 접두사를 붙이거나 삭제하세요.
