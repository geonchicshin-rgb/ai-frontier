---
type: pipeline-board
updated: 2026-06-29
---

# 📋 블로그 포스트 파이프라인

> 포스트가 아이디어에서 발행까지 어느 단계에 있는지 한눈에 확인합니다.

---

## 🟡 작성 중 (In Progress)

| 파일 | 카테고리 | 시작일 | 예상 발행일 |
|---|---|---|---|
| (없음 — 첫 포스트를 시작하세요) | | | |

---

## 🔵 검토 대기 (Review)

| 파일 | 카테고리 | 완성일 | 이슈 |
|---|---|---|---|
| | | | |

---

## ✅ 발행 완료 (Published)

| 포스트 제목 | 카테고리 | 발행일 | URL | 30일 조회수 |
|---|---|---|---|---|
| (첫 포스트를 발행하면 여기에 기록하세요) | | | | |

---

## 📌 소재 백로그 (아이디어 메모)

> intel_collector.py 보고서에서 발견한 소재를 여기에 쌓아두세요.

| 소재 요약 | 출처 | 발견일 | 우선순위 |
|---|---|---|---|
| | | | |

---

## 포스트 작성 체크리스트

새 포스트 시작 시 `_templates/content-brief.md` 를 복사해서 `02_wiki/blog-posts/` 에 저장:

```
파일명: {category}-{slug}-{yyyy-mm-dd}.md
예)    karpathy-llm-c-june-update-2026-06-29.md
       anthropic-claude-new-feature-2026-07-01.md
```

**단계별 작업**

1. `content-brief.md` 초안 작성 (Obsidian)
2. Cursor에 붙여넣고 → 한/영 포스트 HTML 완성 요청
3. 이미지 프롬프트로 헤더 이미지 생성
4. `blog/posts/포스트명.html` 저장
5. `blog/index.html` 포스트 카드 추가
6. `03_lint/lint_check.py` 실행 → 80점 이상 확인
7. Obsidian Git 자동 푸시 → Cloudflare Pages 자동 배포
8. 이 파일 '발행 완료' 테이블에 기록
