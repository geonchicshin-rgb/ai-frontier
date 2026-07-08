import os
import json
import datetime
import urllib.request

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

try:
    import anthropic as _anthropic_sdk
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False


class HarnessOrchestrator:
    """
    KNOT 기반 멀티 에이전트 오케스트레이터.
    수집(GitHub Actions) → 초안 생성(Anthropic API) → 검수(사람) → 발행
    """

    def __init__(self, vault_path: str = "./"):
        self.vault_path = os.path.abspath(vault_path)
        self.config = self._load_config()
        self.system_principles = self._load_principles()
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        print(f"[Harness] 오케스트레이터 초기화 완료 — Vault: {self.vault_path}")
        if not self.api_key:
            print("[Harness] 경고: ANTHROPIC_API_KEY 환경변수 없음 — 드래프트 생성 불가")

    def _load_config(self) -> dict:
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(f"config.json 없음: {CONFIG_PATH}")
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_principles(self) -> str:
        principles_file = self.config["orchestrator"]["principles_file"]
        path = os.path.join(self.vault_path, principles_file)
        if not os.path.exists(path):
            return "[경고] _templates/claude.md 없음 — 기본 원칙으로 동작합니다."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # ──────────────────────────────────────────────────────────────
    # 공유 기억 (KNOT 위키)
    # ──────────────────────────────────────────────────────────────

    def get_shared_memory(self, keyword: str) -> str:
        wiki_path = os.path.join(self.vault_path, "02_wiki", f"{keyword}.md")
        if os.path.exists(wiki_path):
            with open(wiki_path, "r", encoding="utf-8") as f:
                return f.read()
        return "공유된 기존 기억 없음 — 신규 자산화가 필요합니다."

    def get_latest_intel(self) -> str:
        """가장 최근 인텔 보고서를 읽어 반환"""
        inbox = os.path.join(self.vault_path, "01_inbox")
        if not os.path.exists(inbox):
            return ""
        files = sorted(
            [f for f in os.listdir(inbox) if f.startswith("intel-") and f.endswith(".md")],
            reverse=True,
        )
        if not files:
            return ""
        path = os.path.join(inbox, files[0])
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def save_to_wiki(self, keyword: str, content: str, subfolder: str = ""):
        wiki_dir = os.path.join(self.vault_path, "02_wiki", subfolder)
        os.makedirs(wiki_dir, exist_ok=True)
        date_str = datetime.date.today().isoformat()
        filename = f"{keyword}-{date_str}.md"
        output_path = os.path.join(wiki_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[Harness] 위키 저장 완료: {output_path}")
        return output_path

    # ──────────────────────────────────────────────────────────────
    # Anthropic API 호출 (핵심 자동화)
    # ──────────────────────────────────────────────────────────────

    def _call_anthropic(self, prompt: str, max_tokens: int = 4096) -> str:
        """Anthropic Claude API 호출. ANTHROPIC_API_KEY 환경변수 필수."""
        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY 환경변수를 설정하세요.\n"
                "GitHub Actions: Settings → Secrets → ANTHROPIC_API_KEY"
            )
        if not _ANTHROPIC_AVAILABLE:
            raise RuntimeError(
                "anthropic 패키지 없음. pip install anthropic 실행 후 재시도하세요."
            )
        client = _anthropic_sdk.Anthropic(api_key=self.api_key)
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    # ──────────────────────────────────────────────────────────────
    # 워크플로우 진입점
    # ──────────────────────────────────────────────────────────────

    def execute_workflow(self, task_type: str, topic: str) -> str:
        print(f"\n{'='*60}")
        print(f"[Harness] 태스크 가동: {task_type} | 토픽: {topic}")
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
            print("[Harness] 풀 파이프라인: 초안 생성 → 린트 → 카드뉴스")
            draft = self.execute_workflow("GENERATE_DRAFT", topic)
            self.execute_workflow("LINT_WEB", topic)
            self.execute_workflow("GENERATE_CARD_NEWS", topic)
            return draft
        else:
            raise ValueError(f"알 수 없는 task_type: {task_type}")

    # ──────────────────────────────────────────────────────────────
    # Worker: 블로그 초안 자동 생성 (핵심)
    # ──────────────────────────────────────────────────────────────

    def _generate_draft(self, topic: str, shared_ctx: str, intel_ctx: str) -> str:
        """
        수집된 인텔을 바탕으로 블로그 포스트 HTML 초안을 생성하고
        blog/drafts/ 에 저장합니다. 사람이 검수 후 blog/posts/ 로 이동.
        """
        print("[Harness Worker] ▶ Claude — 블로그 초안 생성 중...")

        prompt = f"""You are an expert AI content writer for "AI Frontier" blog.
Target audience: English-speaking AI developers who follow Karpathy and Anthropic.
Tone: Technical but accessible. No fluff. Lead with what matters.

System principles:
{self.system_principles}

Latest intel report (today's RSS collection):
{intel_ctx[:3000]}

Shared context for topic "{topic}":
{shared_ctx[:1000]}

Task:
Write a complete, publication-ready blog post HTML fragment (NOT a full HTML document — just the <article> inner content) about the most interesting item related to "{topic}" from the intel report above.

Requirements:
- Title: under 65 chars, include a power keyword
- 600–900 words
- Structure: Lead (hook) → Context → What happened → What it means for developers → Takeaway
- Include at least one code snippet or concrete example if relevant
- End with a 1-sentence CTA linking back to the home page
- Output ONLY the raw HTML fragment, no markdown, no explanation

Also output at the very end, separated by ---META---:
SLUG: (url-friendly filename, e.g. anthropic-sdk-0116-agent-memory)
TITLE: (full post title)
DESCRIPTION: (meta description, under 155 chars)
CATEGORY: karpathy | anthropic | news | tools
DATE: {datetime.date.today().isoformat()}
"""

        try:
            html_fragment = self._call_anthropic(prompt)
        except Exception as e:
            print(f"[오류] API 호출 실패: {e}")
            return f"DRAFT_FAILED: {e}"

        # META 블록 파싱
        meta = {"slug": topic, "title": topic, "description": "", "category": "news",
                "date": datetime.date.today().isoformat()}
        if "---META---" in html_fragment:
            content_part, meta_part = html_fragment.split("---META---", 1)
            html_fragment = content_part.strip()
            for line in meta_part.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
        else:
            content_part = html_fragment

        # 초안을 blog/drafts/ 에 저장
        draft_path = self._save_draft(html_fragment, meta)
        print(f"[Harness] 초안 저장 완료: {draft_path}")
        print("[검수 필요] blog/drafts/ 폴더에서 내용을 확인하고 blog/posts/ 로 이동하세요.")
        return draft_path

    def _save_draft(self, html_fragment: str, meta: dict) -> str:
        """초안을 blog/drafts/ 에 전체 HTML로 감싸서 저장"""
        drafts_dir = os.path.join(self.vault_path, "blog", "drafts")
        os.makedirs(drafts_dir, exist_ok=True)

        slug = meta.get("slug", "draft")
        filename = f"{meta['date']}-{slug}.html"
        output_path = os.path.join(drafts_dir, filename)

        # blog-post-template.html 로드
        template_path = os.path.join(self.vault_path, "_templates", "blog-post-template.html")
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
            # 템플릿 내 플레이스홀더 교체
            full_html = (template
                .replace("{{TITLE}}", meta.get("title", slug))
                .replace("{{DESCRIPTION}}", meta.get("description", ""))
                .replace("{{CATEGORY}}", meta.get("category", "news"))
                .replace("{{DATE}}", meta.get("date", ""))
                .replace("{{SLUG}}", slug)
                .replace("{{CONTENT}}", html_fragment))
        else:
            # 템플릿 없으면 최소 HTML 래핑
            full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{meta.get('title', slug)} | AI Frontier</title>
  <meta name="description" content="{meta.get('description', '')}">
  <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
<header class="site-header">
  <a href="../index.html" class="site-title">AI <span>Frontier</span></a>
</header>
<main>
  <div class="post-layout">
    <article>
      <header class="post-header">
        <span class="post-tag {meta.get('category','news')}">{meta.get('category','news').capitalize()}</span>
        <h1>{meta.get('title', slug)}</h1>
        <div class="byline"><span>AI Frontier</span><span>·</span><span>{meta.get('date','')}</span></div>
      </header>
      <div class="post-content">
{html_fragment}
      </div>
    </article>
  </div>
</main>
<footer>
  <p>AI Frontier · <a href="../index.html">← All Posts</a></p>
</footer>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        return output_path

    # ──────────────────────────────────────────────────────────────
    # Worker: 유틸리티 웹 빌드 (기존 유지)
    # ──────────────────────────────────────────────────────────────

    def _build_utility_web(self, topic: str, shared_ctx: str) -> str:
        print("[Harness Worker] ▶ Codex 에이전트 활성화 → 정적 웹 빌드")
        prompt = (
            f"System Rules:\n{self.system_principles}\n\n"
            f"Context (KNOT 공유 기억):\n{shared_ctx}\n\n"
            f"Task: '{topic}' 관련 HTML/JS 단일 유틸리티 툴 설계 및 구현\n"
            f"요구사항:\n"
            f"- 순수 Client-side JS (localStorage 기반, 서버·DB 없음)\n"
            f"- AdSense 3영역 레이아웃 확보\n"
            f"- application/ld+json 구조화 데이터 동적 생성\n"
            f"- 03_lint/lint_check.py 통과 필수"
        )
        print(f"[Codex 프롬프트 생성 완료] 길이: {len(prompt)}자")
        print("[안내] Cursor 채팅창에 아래 프롬프트를 붙여넣어 웹 빌드를 시작하세요.")
        print("-" * 40)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        return prompt

    # ──────────────────────────────────────────────────────────────
    # Worker: 카드뉴스 생성 (기존 유지)
    # ──────────────────────────────────────────────────────────────

    def _generate_card_news(self, topic: str, shared_ctx: str) -> str:
        print("[Harness Worker] ▶ Gemini 에이전트 활성화 → 카드뉴스 생성")
        template_path = os.path.join(self.vault_path, "_templates", "gemini-shorts.md")
        gemini_template = ""
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                gemini_template = f.read()

        prompt = (
            f"참고 템플릿:\n{gemini_template}\n\n"
            f"Context (KNOT 공유 기억):\n{shared_ctx}\n\n"
            f"Task: '{topic}' X 스레드 3-line summary + blog link CTA\n"
            f"출력 형식: 트위터 스레드 3줄 + 링크 + 해시태그"
        )
        print(f"[Card News 프롬프트 생성 완료] 길이: {len(prompt)}자")
        return "## CARD_NEWS_SCRIPT_READY\n\n" + prompt

    # ──────────────────────────────────────────────────────────────
    # Worker: Lint 검사 (기존 유지)
    # ──────────────────────────────────────────────────────────────

    def _lint_web(self, topic: str) -> str:
        print("[Harness Worker] ▶ Linter 에이전트 활성화 → 품질 검사")
        lint_script = os.path.join(self.vault_path, "03_lint", "lint_check.py")
        if not os.path.exists(lint_script):
            print("[경고] lint_check.py 없음 — 린트를 건너뜁니다.")
            return "LINT_SKIPPED"
        product_dir = os.path.join(self.vault_path, "blog", "drafts")
        print(f"[Linter] 검사 대상: {product_dir}")
        os.system(f'python "{lint_script}" --target "{product_dir}"')
        return "LINT_COMPLETE"


if __name__ == "__main__":
    orchestrator = HarnessOrchestrator(vault_path="./")

    # 사용 예시
    # orchestrator.execute_workflow("GENERATE_DRAFT", "anthropic")   # 인텔 기반 초안 자동 생성
    # orchestrator.execute_workflow("BUILD_UTILITY_WEB", "compound-interest-calculator")
    # orchestrator.execute_workflow("GENERATE_CARD_NEWS", "anthropic")
    orchestrator.execute_workflow("GENERATE_DRAFT", "anthropic")
