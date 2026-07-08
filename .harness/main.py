"""
AI Frontier — Harness Orchestrator
수집(GitHub Actions) → Stage1 Gemini(작가) → Stage2 Claude(편집장)
→ blog/drafts/ (HTML) + 03_drafts/ (Obsidian MD) → 사람 검수 → 발행
"""
import os
import json
import datetime
import re

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

# ── 의존 패키지 안전 임포트 ────────────────────────────────────────
try:
    from google import genai as _genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

try:
    import anthropic as _anthropic_sdk
    _CLAUDE_AVAILABLE = True
except ImportError:
    _CLAUDE_AVAILABLE = False


class HarnessOrchestrator:
    """
    AI office 이중 모델 인프라 기반 블로그 자동화 오케스트레이터.

    Stage 1 — Gemini 3.5 Flash (Vertex AI, ai-transfer-center-495006): 원시 초안 작성
    Stage 2 — Claude Sonnet 4.6 (Anthropic API): 편집·SEO·팩트 검수
    저장 — blog/drafts/*.html (블로그용) + 03_drafts/*.md (Obsidian 검수용)
    """

    # ── 초기화 ─────────────────────────────────────────────────────

    def __init__(self, vault_path: str = "./"):
        self.vault_path = os.path.abspath(vault_path)
        self.config = self._load_config()
        self.system_principles = self._load_principles()

        # AI office 기준 GCP 설정 (test_vertex.py 확인 값)
        self.gcp_project  = os.environ.get("GCP_PROJECT_ID", "ai-transfer-center-495006")
        self.gcp_location = os.environ.get("GCP_LOCATION", "us-central1")   # global은 Vertex AI 미지원
        self.gemini_model = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")  # 3.5는 존재하지 않음
        self.creds_path   = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

        # Claude 설정 (AI office 동일)
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.claude_model  = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

        gemini_ok = bool(self.creds_path and os.path.exists(self.creds_path))
        claude_ok = bool(self.anthropic_key)

        print(f"[Harness] 초기화 완료 — Vault: {self.vault_path}")
        print(f"[Harness] Stage 1 Gemini  ({self.gemini_model}): {'OK' if gemini_ok else 'MISSING — GOOGLE_APPLICATION_CREDENTIALS 필요'}")
        print(f"[Harness] Stage 2 Claude  ({self.claude_model}): {'OK' if claude_ok else 'MISSING — ANTHROPIC_API_KEY 필요'}")

    def _load_config(self) -> dict:
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(f"config.json 없음: {CONFIG_PATH}")
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_principles(self) -> str:
        principles_file = self.config["orchestrator"]["principles_file"]
        path = os.path.join(self.vault_path, principles_file)
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # ── KNOT 공유 기억 ──────────────────────────────────────────────

    def get_shared_memory(self, keyword: str) -> str:
        wiki_path = os.path.join(self.vault_path, "02_wiki", f"{keyword}.md")
        if os.path.exists(wiki_path):
            with open(wiki_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def get_latest_intel(self) -> str:
        """가장 최근 인텔 보고서(01_inbox/intel-*.md)를 읽어 반환."""
        inbox = os.path.join(self.vault_path, "01_inbox")
        if not os.path.exists(inbox):
            return ""
        files = sorted(
            [f for f in os.listdir(inbox) if f.startswith("intel-") and f.endswith(".md")],
            reverse=True,
        )
        if not files:
            return ""
        with open(os.path.join(inbox, files[0]), "r", encoding="utf-8") as f:
            return f.read()

    def save_to_wiki(self, keyword: str, content: str, subfolder: str = "") -> str:
        wiki_dir = os.path.join(self.vault_path, "02_wiki", subfolder)
        os.makedirs(wiki_dir, exist_ok=True)
        filename = f"{keyword}-{datetime.date.today().isoformat()}.md"
        output_path = os.path.join(wiki_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[Harness] 위키 저장: {output_path}")
        return output_path

    # ── LLM 호출 ───────────────────────────────────────────────────

    def _call_gemini(self, prompt: str, max_tokens: int = 3000) -> str:
        """
        Stage 1: Gemini 3.5 Flash via Vertex AI.
        AI office GeminiClient와 동일한 ADC 방식 사용.
        GOOGLE_APPLICATION_CREDENTIALS 환경변수로 서비스 계정 키 지정.
        """
        if not _GEMINI_AVAILABLE:
            raise RuntimeError("google-genai 패키지 없음 — pip install google-genai google-auth")

        if self.creds_path and os.path.exists(self.creds_path):
            from google.oauth2 import service_account as _sa
            creds = _sa.Credentials.from_service_account_file(
                self.creds_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            client = _genai.Client(
                vertexai=True,
                project=self.gcp_project,
                location=self.gcp_location,
                credentials=creds,
            )
        else:
            # ADC 폴백 (gcloud auth application-default login)
            client = _genai.Client(
                vertexai=True,
                project=self.gcp_project,
                location=self.gcp_location,
            )

        response = client.models.generate_content(
            model=self.gemini_model,
            contents=prompt,
        )
        return response.text or ""

    def _call_claude(self, system: str, prompt: str, max_tokens: int = 4000) -> str:
        """
        Stage 2: Claude Sonnet 4.6 via Anthropic API.
        AI office ClaudeClient와 동일한 방식.
        ANTHROPIC_API_KEY 환경변수 필수.
        """
        if not _CLAUDE_AVAILABLE:
            raise RuntimeError("anthropic 패키지 없음 — pip install anthropic")
        if not self.anthropic_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY 없음.\n"
                "AI office/.env 의 키를 GitHub Secret ANTHROPIC_API_KEY 에 등록하세요."
            )
        client = _anthropic_sdk.Anthropic(api_key=self.anthropic_key)
        message = client.messages.create(
            model=self.claude_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    # ── 워크플로우 진입점 ──────────────────────────────────────────

    def execute_workflow(self, task_type: str, topic: str) -> str:
        print(f"\n{'='*60}")
        print(f"[Harness] {task_type} | 토픽: {topic}")
        print(f"{'='*60}")

        shared_ctx = self.get_shared_memory(topic)
        intel_ctx  = self.get_latest_intel()

        if task_type == "GENERATE_DRAFT":
            return self._generate_draft(topic, shared_ctx, intel_ctx)
        elif task_type == "BUILD_UTILITY_WEB":
            return self._build_utility_web(topic, shared_ctx)
        elif task_type == "GENERATE_CARD_NEWS":
            return self._generate_card_news(topic, shared_ctx)
        elif task_type == "LINT_WEB":
            return self._lint_web(topic)
        elif task_type == "FULL_PIPELINE":
            draft = self.execute_workflow("GENERATE_DRAFT", topic)
            self.execute_workflow("LINT_WEB", topic)
            self.execute_workflow("GENERATE_CARD_NEWS", topic)
            return draft
        else:
            raise ValueError(f"알 수 없는 task_type: {task_type}")

    # ── 2단계 초안 생성 파이프라인 ─────────────────────────────────

    def _generate_draft(self, topic: str, shared_ctx: str, intel_ctx: str) -> str:
        """
        Stage 1 (Gemini 3.5 Flash): 원시 HTML 초안 작성
        Stage 2 (Claude Sonnet 4.6): 편집·SEO·팩트 검수 및 개선
        저장: blog/drafts/*.html + 03_drafts/*.md (Obsidian 검수용)
        """
        today = datetime.date.today().isoformat()

        # ── Stage 1: Gemini — 원시 초안 ──────────────────────────
        print("\n[Stage 1/2] Gemini 3.5 Flash — 원시 초안 생성 중...")

        writer_prompt = f"""You are a sharp AI content writer for "AI Frontier" — a blog for English-speaking AI developers who follow Karpathy and Anthropic.

TODAY'S INTEL (RSS collection — pick the single most interesting item related to "{topic}"):
{intel_ctx[:3000]}

PRIOR CONTEXT for "{topic}":
{shared_ctx[:600]}

WRITING RULES:
- HTML fragment only (no <html>/<head>/<body> — just inner article content)
- Title: under 65 chars, strong keyword
- Length: 600–900 words
- Structure: Hook (2 sentences max) → Background → What happened → Developer impact → Takeaway
- Include a code example or concrete metric if the source supports it
- Tone: direct, technical, zero fluff
- End with exactly one CTA: <a href="../index.html">More on AI Frontier →</a>

OUTPUT — two blocks separated by ---META---:

[HTML fragment]

---META---
SLUG: url-friendly-slug
TITLE: Post title
DESCRIPTION: Meta description under 155 chars
CATEGORY: karpathy | anthropic | news | tools
SOURCE_URL: original source link or empty
"""

        try:
            stage1_raw = self._call_gemini(writer_prompt)
            print("[Stage 1] 완료")
        except Exception as e:
            print(f"[Stage 1 오류] {e}")
            return f"DRAFT_FAILED_STAGE1: {e}"

        # META 파싱
        meta = {
            "slug": topic, "title": topic, "description": "",
            "category": "news", "date": today,
            "source_url": "", "editor_notes": [],
        }
        if "---META---" in stage1_raw:
            raw_html, meta_block = stage1_raw.split("---META---", 1)
            raw_html = raw_html.strip()
            for line in meta_block.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
        else:
            raw_html = stage1_raw.strip()

        # ── Stage 2: Claude — 편집·검수 ──────────────────────────
        print(f"\n[Stage 2/2] Claude {self.claude_model} — 편집 및 검수 중...")

        editor_system = (
            'You are a senior editor for "AI Frontier" — a technical blog for English-speaking AI developers. '
            "Output publication-ready copy: precise, authoritative, zero fluff. "
            "Make complex AI topics immediately useful to practitioners."
        )

        editor_prompt = f"""Edit this draft and return a polished, publication-ready version.

EDITORIAL CHECKLIST (apply silently — do NOT explain changes in the body):
1. SEO: Title ≤65 chars with primary keyword. Description ≤155 chars, benefit-driven.
2. Fact flags: Add <!-- VERIFY: <claim> --> HTML comment next to any unverifiable fact (versions, dates, benchmarks). Keep the claim — just flag it.
3. Tone: Remove every sentence that adds no value. No "In this post..." openers. Lead with the most important insight.
4. Structure: Hook in first 2 sentences. Clear H2 per section. Specific, actionable takeaway.
5. Code: If a snippet exists, verify it is syntactically correct. If missing but would strengthen the argument, add one (max 10 lines).
6. English: Fix grammar, awkward phrasing, passive voice overuse.
7. AdSense: No clickbait. No misleading claims. Max 3 outbound links.
8. CTA: Exactly one — <a href="../index.html">More on AI Frontier →</a> at the end.

DRAFT HTML:
{raw_html}

META:
Title: {meta.get('title')}
Description: {meta.get('description')}
Category: {meta.get('category')}
Source: {meta.get('source_url', 'unknown')}

OUTPUT — two blocks separated by ---META---:

[Improved HTML fragment]

---META---
SLUG: {meta.get('slug')}
TITLE: (keep or improve)
DESCRIPTION: (keep or improve, ≤155 chars)
CATEGORY: {meta.get('category')}
SOURCE_URL: {meta.get('source_url', '')}
EDITOR_NOTE: (one bullet per issue — improvements made and VERIFY items for human reviewer)
EDITOR_NOTE: (add more EDITOR_NOTE lines as needed)
"""

        try:
            stage2_raw = self._call_claude(editor_system, editor_prompt)
            print("[Stage 2] 완료")
        except Exception as e:
            print(f"[Stage 2 오류] {e} — Stage 1 결과물로 진행합니다.")
            stage2_raw = stage1_raw

        # Stage 2 META 파싱 (EDITOR_NOTE는 복수 라인)
        editor_notes = []
        if "---META---" in stage2_raw:
            final_html, final_meta_block = stage2_raw.split("---META---", 1)
            final_html = final_html.strip()
            for line in final_meta_block.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    key = k.strip().lower()
                    val = v.strip()
                    if key == "editor_note":
                        editor_notes.append(val)
                    elif key != "date":  # date는 오늘 날짜 고정
                        meta[key] = val
        else:
            final_html = stage2_raw.strip()

        meta["editor_notes"] = editor_notes
        meta["date"] = today  # 항상 오늘 날짜 강제

        if editor_notes:
            print("\n[편집장 노트]")
            for note in editor_notes:
                print(f"  · {note}")

        # ── 저장 ──────────────────────────────────────────────────
        html_path, md_path = self._save_draft(final_html, meta)
        print(f"\n[Harness] HTML 저장: {html_path}")
        print(f"[Harness] Obsidian MD: {md_path}")
        print("[검수] Obsidian의 03_drafts/ 폴더에서 확인 후 승인하세요.")
        return html_path

    # ── 저장 메서드 ────────────────────────────────────────────────

    def _save_draft(self, html_fragment: str, meta: dict) -> tuple:
        """
        blog/drafts/YYYY-MM-DD-slug.html  — 블로그 배포용 HTML
        03_drafts/YYYY-MM-DD-slug.md      — Obsidian 검수용 Markdown
        두 파일을 동시에 저장하고 (html_path, md_path) 반환.
        """
        today   = meta.get("date", datetime.date.today().isoformat())
        slug    = re.sub(r"[^a-z0-9\-]", "", meta.get("slug", "draft").lower().replace(" ", "-"))
        fname   = f"{today}-{slug}"

        # ── HTML 저장 (blog/drafts/) ──────────────────────────────
        drafts_dir = os.path.join(self.vault_path, "blog", "drafts")
        os.makedirs(drafts_dir, exist_ok=True)
        html_path  = os.path.join(drafts_dir, f"{fname}.html")

        editor_notes = meta.get("editor_notes", [])
        note_comment = ""
        if editor_notes:
            lines = "\n".join(f"  - {n}" for n in editor_notes)
            note_comment = f"<!-- EDITOR NOTES\n{lines}\n-->\n\n"

        category = meta.get("category", "news")
        title    = meta.get("title", slug)
        desc     = meta.get("description", "")
        date_str = today

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | AI Frontier</title>
  <meta name="description" content="{desc}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://ai-frontier-eni.pages.dev/posts/{slug}.html">
  <link rel="stylesheet" href="../assets/css/style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js"
    data-cf-beacon='{{"token": "REPLACE_WITH_CF_ANALYTICS_TOKEN"}}'></script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{title}",
    "description": "{desc}",
    "datePublished": "{date_str}",
    "author": {{"@type": "Organization", "name": "AI Frontier"}},
    "publisher": {{"@type": "Organization", "name": "AI Frontier", "url": "https://ai-frontier-eni.pages.dev"}}
  }}
  </script>
</head>
<body>
<header class="site-header">
  <a href="../index.html" class="site-title">AI <span>Frontier</span></a>
  <nav>
    <a href="../index.html#posts">Posts</a>
    <a href="https://x.com/karpathy" target="_blank">Karpathy</a>
    <a href="https://www.anthropic.com/news" target="_blank">Anthropic</a>
  </nav>
</header>
<div class="ad-leaderboard"><!-- [Top_Leaderboard] 728x90 AdSense --></div>
<main>
  <div class="post-layout">
    <article>
      {note_comment}<header class="post-header">
        <span class="post-tag {category}">{category.capitalize()}</span>
        <h1>{title}</h1>
        <div class="byline">
          <span>AI Frontier</span><span>·</span><span>{date_str}</span>
        </div>
      </header>
      <div class="post-content">
{html_fragment}
      </div>
    </article>
    <aside>
      <div class="ad-skyscraper"><!-- [Aside_SkyScraper] 160x600 AdSense --></div>
    </aside>
  </div>
  <div class="ad-in-article"><!-- [In-Article_Sticky] 336x280 AdSense --></div>
</main>
<footer>
  <p>AI Frontier · Practical insights for AI developers · Hosted on Cloudflare Pages</p>
  <p style="margin-top:8px">
    <a href="https://x.com/karpathy">@karpathy</a> ·
    <a href="https://www.anthropic.com">Anthropic</a> ·
    <a href="https://github.com/geonchicshin-rgb/ai-frontier">GitHub</a>
  </p>
</footer>
</body>
</html>"""

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html)

        # ── Markdown 저장 (03_drafts/) — Obsidian 검수용 ─────────
        obs_dir = os.path.join(self.vault_path, "03_drafts")
        os.makedirs(obs_dir, exist_ok=True)
        md_path = os.path.join(obs_dir, f"{fname}.md")

        notes_yaml = "\n".join(f'  - "{n}"' for n in editor_notes) if editor_notes else '  - (없음)'
        verify_items = [n for n in editor_notes if "VERIFY" in n.upper()]
        verify_block = "\n".join(f"- [ ] {v}" for v in verify_items) if verify_items else "- [ ] 없음"

        md_content = f"""---
status: draft
date: {today}
slug: {slug}
title: "{title}"
description: "{desc}"
category: {category}
source_url: "{meta.get('source_url', '')}"
html_draft: "blog/drafts/{fname}.html"
editor_notes:
{notes_yaml}
generated_by:
  stage1: "Gemini {self.gemini_model}"
  stage2: "Claude {self.claude_model}"
---

# [DRAFT] {title}

> **Status:** draft | **Date:** {today} | **Category:** {category}
> **HTML 파일:** `blog/drafts/{fname}.html`

---

## 편집장 노트 (검수 필수 항목)

{verify_block}

---

## 검수 완료 후 발행 순서

1. 위 VERIFY 항목 사실 확인
2. `blog/drafts/{fname}.html` → `blog/posts/{slug}.html` 로 이동
3. `blog/index.html` 에 포스트 카드 추가 (아래 템플릿 복붙)
4. Obsidian Git → Commit & Push
5. Cloudflare Pages 자동 배포 (30초)
6. `04_published/index.md` 에 한 줄 기록

---

## index.html 포스트 카드 템플릿

```html
<article class="post-card" data-category="{category}">
  <div class="post-card-meta">
    <span class="post-tag {category}">{category.capitalize()}</span>
    <span class="post-date">{today}</span>
  </div>
  <h2><a href="posts/{slug}.html">{title}</a></h2>
  <p>{desc}</p>
</article>
```

---

## Reddit / X 배포 문구

**Reddit** (r/MachineLearning or r/LocalLLaMA):
> Title: {title}
> Body: [2-3줄 요약 직접 작성] — https://ai-frontier-eni.pages.dev/posts/{slug}.html

**X 스레드:**
> 트윗 1: [핵심 인사이트 1줄]
> 트윗 2: [왜 중요한지 1줄]
> 트윗 3: https://ai-frontier-eni.pages.dev/posts/{slug}.html #AI #LLM

---
*Harness 자동 생성 | Stage 1: Gemini {self.gemini_model} | Stage 2: Claude {self.claude_model}*
"""

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return html_path, md_path

    # ── 발행 이력 기록 ─────────────────────────────────────────────

    def record_published(self, slug: str, title: str, url: str = "") -> None:
        """
        발행 완료 후 04_published/index.md 에 한 줄 추가.
        Obsidian과 git 양쪽에 영구 보존.
        """
        pub_dir  = os.path.join(self.vault_path, "04_published")
        os.makedirs(pub_dir, exist_ok=True)
        index_path = os.path.join(pub_dir, "index.md")

        today = datetime.date.today().isoformat()
        post_url = url or f"https://ai-frontier-eni.pages.dev/posts/{slug}.html"
        new_line = f"| {today} | [{title}]({post_url}) | {slug} | published |\n"

        if not os.path.exists(index_path):
            header = (
                "# 발행 이력\n\n"
                "| 날짜 | 제목 | slug | 상태 |\n"
                "|---|---|---|---|\n"
            )
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(header)

        with open(index_path, "a", encoding="utf-8") as f:
            f.write(new_line)

        print(f"[Harness] 발행 이력 기록: {index_path}")

    # ── 기타 워커 (기존 유지) ──────────────────────────────────────

    def _build_utility_web(self, topic: str, shared_ctx: str) -> str:
        print("[Harness Worker] Codex → 정적 웹 빌드")
        prompt = (
            f"System Rules:\n{self.system_principles}\n\n"
            f"Context:\n{shared_ctx}\n\n"
            f"Task: '{topic}' HTML/JS 단일 유틸리티 툴\n"
            f"- 순수 Client-side JS (localStorage, 서버 없음)\n"
            f"- AdSense 3영역 레이아웃\n"
            f"- application/ld+json 구조화 데이터"
        )
        print(prompt[:400])
        return prompt

    def _generate_card_news(self, topic: str, shared_ctx: str) -> str:
        print("[Harness Worker] → X 스레드 문구 생성")
        return f"## X_THREAD_READY\n\nTopic: {topic}"

    def _lint_web(self, topic: str) -> str:
        print("[Harness Worker] → Lint 검사")
        lint_script = os.path.join(self.vault_path, "03_lint", "lint_check.py")
        if not os.path.exists(lint_script):
            print("[경고] lint_check.py 없음 — 건너뜁니다.")
            return "LINT_SKIPPED"
        target = os.path.join(self.vault_path, "blog", "drafts")
        os.system(f'python "{lint_script}" --target "{target}"')
        return "LINT_COMPLETE"


if __name__ == "__main__":
    orchestrator = HarnessOrchestrator(vault_path="./")
    orchestrator.execute_workflow("GENERATE_DRAFT", "anthropic")
