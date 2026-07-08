---
type: project-dashboard
updated: 2026-06-29
---

# 🗂️ 프로젝트 전체 현황판

> 이 파일이 시스템의 두뇌입니다. 매주 월요일 업데이트하세요.

---

## ⚙️ 시스템 인프라 현황

| 구성 요소 | 상태 | 비고 |
|---|---|---|
| KNOT Vault (Obsidian) | ✅ 가동 중 | `따라해보자고/` 폴더 |
| GitHub 저장소 | ✅ 완료 | github.com/geonchicshin-rgb/ai-frontier |
| Obsidian Git 플러그인 | ✅ 완료 | Auto pull 30분, Pull on startup 켜짐 |
| GitHub Actions (인텔 수집) | ✅ 가동 중 | 매일 오전 8시 자동 실행, 6.29~7.8 보고서 생성 완료 |
| Cloudflare Pages (블로그) | ✅ 가동 중 | https://ai-frontier-eni.pages.dev |
| Google AdSense | ⬜ 신청 가능 | Cloudflare 연결 완료 — 포스트 1개 후 신청 |

---

## 📰 AI Frontier 블로그

**목표**: Karpathy · Anthropic 최신 정보 한/영 블로그 운영 → AdSense 수익

| 항목 | 현황 |
|---|---|
| 블로그 홈 | ✅ `blog/index.html` 완성 |
| 포스트 템플릿 | ✅ `_templates/blog-post-template.html` |
| 배포 URL | ✅ https://ai-frontier-eni.pages.dev |
| 총 발행 포스트 수 | 0 |
| 월간 방문자 | 0 |
| AdSense 월수익 | $0 |

### 포스트 파이프라인
→ 상세 현황: [[02_wiki/blog-posts/pipeline]]

---

## 🤖 에이전트 군단 현황

| 에이전트 | 역할 | 도구 | 상태 |
|---|---|---|---|
| Claude (오케스트레이터) | 작업 분배·품질 검증 | Cursor AI | ✅ 활성 |
| Codex (빌드 워커) | HTML/JS 유틸리티 빌드 | Cursor | ✅ 활성 |
| Gemini (콘텐츠 워커) | 카드뉴스·이미지 프롬프트 | Cursor / DALL-E | ✅ 활성 |
| Intel Collector (수집봇) | Karpathy·Anthropic RSS | GitHub Actions | ⬜ 설정 필요 |

---

## 📊 수익 채널 현황

| 채널 | 단계 | 월 목표 | 현재 |
|---|---|---|---|
| Google AdSense (블로그) | ⬜ 신청 전 | $100 | $0 |
| 메타 오리지널 보너스 | ⬜ 미시작 | $50 | $0 |
| Reddit → 블로그 유입 | ⬜ 미시작 | - | 0 클릭 |

---

## 📁 KNOT Vault 파일 현황

| 폴더 | 파일 수 | 용도 |
|---|---|---|
| `01_inbox/` | 0 | 일일 인텔 보고서 (GitHub Actions 자동 생성) |
| `02_wiki/blog-posts/` | 0 | 포스트 초안 |
| `02_wiki/ai-intel/` | 1 | AI 추적 소스 목록 |
| `02_wiki/02A_products/` | 0 | 유틸리티 웹 사양서 |
| `02_wiki/02B_social_assets/` | 0 | 소셜 성과 기록 |
| `_templates/` | 6 | 에이전트 주입·작업 양식 |
| `blog/` | 2 | 블로그 HTML 파일 |

---

## 🗓️ 이번 주 마스터 체크리스트

### 1회성 설정 (처음 한 번만)
- [x] GitHub 저장소 생성 및 코드 업로드 ✅ 2026-06-29
- [x] Obsidian Git 플러그인 설치 ✅ 2026-07-08
- [x] GitHub Actions 인텔 수집 첫 실행 확인 ✅ 2026-07-08
- [x] **Cloudflare Pages 연결 완료** ✅ 2026-07-08 → https://ai-frontier-eni.pages.dev
- [ ] 첫 번째 블로그 포스트 작성 (소재: nanoGPT → nanochat)

### 매일 반복
- [ ] `01_inbox/intel-오늘날짜` 확인 (자동 생성)
- [ ] 블로그 소재 1개 선택 → `_templates/content-brief` 작성
- [ ] Cursor에서 한/영 포스트 완성
- [ ] `blog/posts/` 저장 → Obsidian Git 자동 푸시

### 매주 월요일
- [ ] X 계정 수동 확인 (@karpathy, @AnthropicAI)
- [ ] [[_templates/weekly-intel-digest]] 작성
- [ ] PROJECT-STATUS.md 수치 업데이트
