# 🌐 AI Frontier — 운영 대시보드

---

## ⚡ 시스템 상태

| 구성 요소                 | 상태                                     |
| --------------------- | -------------------------------------- |
| KNOT Vault (Obsidian) | ✅ 가동 중                                 |
| GitHub 저장소            | ⬜ [[02_wiki/SETUP-GUIDE#step1\|설정 필요]] |
| Obsidian Git 자동 동기화   | ⬜ [[02_wiki/SETUP-GUIDE#step2\|설정 필요]] |
| GitHub Actions 인텔 수집  | ⬜ [[02_wiki/SETUP-GUIDE#step4\|설정 필요]] |
| Cloudflare Pages 블로그  | ⬜ [[02_wiki/SETUP-GUIDE#step3\|설정 필요]] |
| Google AdSense        | ⬜ 블로그 배포 후 신청                          |

---

## 📥 오늘의 인텔 보고서

> GitHub Actions가 매일 오전 8시에 자동 생성합니다.

[[01_inbox/]] 폴더에서 오늘 날짜 파일을 여세요.

---

## 📋 매일 워크플로우

```
① 01_inbox/intel-오늘날짜  열기 → 소재 선정
② _templates/content-brief 복사 → 02_wiki/blog-posts/ 에 초안 작성
③ Cursor에서 한/영 포스트 완성 + 이미지 생성
④ blog/posts/ 에 HTML 저장
⑤ blog/index.html 포스트 카드 추가
⑥ Obsidian Git이 자동 푸시 → Cloudflare 자동 배포
```

---

## 🗂️ 빠른 이동

### 운영 현황
- [[02_wiki/PROJECT-STATUS|📊 전체 프로젝트 현황판]]
- [[02_wiki/blog-posts/pipeline|📋 블로그 포스트 파이프라인]]
- [[02_wiki/ai-intel/sources|🔍 AI 인텔 추적 소스 목록]]

### 작업 양식 (Templates)
- [[_templates/content-brief|✍️ 포스트 초안 작성 양식]]
- [[_templates/daily-note|📅 일일 노트]]
- [[_templates/weekly-intel-digest|📊 주간 인텔 다이제스트]]
- [[_templates/gemini-shorts|🎴 카드뉴스 5장 생성 양식]]
- [[_templates/reddit-template|💬 Reddit 북미 침투 포맷]]

### 에이전트 시스템
- [[_templates/claude|🤖 카파시 4원칙 (AI 주입용)]]
- [[02_wiki/SETUP-GUIDE|🔧 전체 연동 설정 가이드]]

### 블로그
- `blog/index.html` — 블로그 홈 (브라우저로 열기)
- [[_templates/blog-post-template|📄 포스트 HTML 템플릿]]

---

## 💰 수익 현황

| 채널 | 이번 달 | 누적 |
|---|---|---|
| Google AdSense | $0 | $0 |
| 메타 보너스 | $0 | $0 |
| **합계** | **$0** | **$0** |

---

## 📌 다음 할 일

> [[02_wiki/SETUP-GUIDE]] 를 열고 STEP 1부터 순서대로 진행하세요. (약 30분)

- [ ] STEP 1 — GitHub Desktop으로 저장소 생성
- [ ] STEP 2 — Obsidian Git 플러그인 설치
- [ ] STEP 3 — Cloudflare Pages 블로그 배포
- [ ] STEP 4 — GitHub Actions 첫 실행 확인
- [ ] 첫 번째 블로그 포스트 작성
