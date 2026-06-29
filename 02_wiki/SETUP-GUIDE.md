---
type: setup-guide
status: 설정 필요
---

# 🔧 전체 시스템 연동 설정 가이드

> 이 가이드를 한 번만 완료하면 이후 모든 것이 자동으로 돌아갑니다.
> 예상 소요시간: **30분**

---

## STEP 1 — GitHub Desktop으로 저장소 생성 {#step1}

**1.** [GitHub Desktop 다운로드](https://desktop.github.com) 및 설치

**2.** GitHub Desktop 실행 → GitHub 계정으로 로그인

**3.** 메뉴: File → **Add Local Repository**

**4.** 폴더 선택:
```
C:\Users\신건식\Desktop\따라해보자고
```

**5.** "This folder does not appear to be a Git repository. Create a repository?" → **Create Repository** 클릭

**6.** Repository name: `ai-frontier` (또는 원하는 이름)

**7.** **Publish Repository** 클릭 → GitHub에 업로드

✅ 완료 시: GitHub.com에서 저장소 확인 가능

---

## STEP 2 — Obsidian Git 플러그인 설치 {#step2}

Obsidian과 GitHub를 자동으로 동기화합니다.  
GitHub Actions가 커밋하면 Obsidian에 자동으로 파일이 나타납니다.

**1.** Obsidian 설정(⚙️) → **커뮤니티 플러그인** → 안전 모드 끄기

**2.** **탐색** 클릭 → 검색창에 `git` 입력

**3.** **Obsidian Git** 선택 → **설치** → **활성화**

**4.** 설정에서 아래와 같이 구성:

| 설정 항목 | 값 |
|---|---|
| Auto pull interval | `30` (분마다 자동 pull) |
| Auto push on commit | ✅ 켜기 |
| Commit message | `📝 KNOT update: {{date}}` |
| Auto commit interval | `0` (수동 커밋) |

✅ 완료 시: Obsidian 왼쪽 사이드바에 Git 아이콘 등장

---

## STEP 3 — Cloudflare Pages 블로그 자동 배포 {#step3}

**1.** [Cloudflare.com](https://cloudflare.com) 가입 (무료)

**2.** 대시보드 → **Pages** → **Create a project**

**3.** **Connect to Git** → GitHub 계정 연결 → 저장소 선택 (`ai-frontier`)

**4.** 빌드 설정:

| 항목 | 값 |
|---|---|
| Framework preset | `None` |
| Build command | *(비워두기)* |
| Build output directory | `blog` |

**5.** **Save and Deploy** 클릭

**6.** 약 1분 후 `https://ai-frontier.pages.dev` 주소 발급

✅ 완료 시: blog/index.html이 인터넷에서 접속 가능

---

## STEP 4 — GitHub Actions 인텔 수집 확인 {#step4}

GitHub Actions는 저장소 업로드 시 자동으로 활성화됩니다.

**수동으로 즉시 실행하기:**

1. GitHub.com → 저장소 → **Actions** 탭 클릭
2. 왼쪽 목록에서 **"AI 인텔 일일 수집"** 클릭
3. **Run workflow** 버튼 클릭

약 30초 후 `01_inbox/intel-오늘날짜.md` 파일이 생성됩니다.

✅ 완료 시: Obsidian에 intel 보고서 자동 등장 (Obsidian Git이 30분마다 pull)

---

## 연동 완료 후 전체 흐름

```
[매일 오전 8시 자동]
GitHub Actions → intel_collector.py 실행
    → 01_inbox/intel-날짜.md 커밋

[30분마다 자동]
Obsidian Git → GitHub pull
    → Obsidian에 intel 파일 자동 등장

[사용자가 포스트 완성 후]
Obsidian Git → GitHub push
    → Cloudflare Pages 자동 배포
    → blog/index.html 인터넷에 반영
```

---

## 문제 해결

**Obsidian Git에서 "Not a git repository" 오류**
→ GitHub Desktop으로 먼저 저장소를 초기화한 후 플러그인 재설치

**GitHub Actions가 실행되지 않음**
→ 저장소 Settings → Actions → General → "Allow all actions" 선택

**Cloudflare Pages 빌드 실패**
→ Build output directory가 `blog` 인지 확인 (대소문자 주의)
