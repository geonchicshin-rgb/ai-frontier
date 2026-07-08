import os
import json
import datetime
import urllib.request

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

try:
    from google import genai as _genai
    from google.genai import types as _genai_types
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False


class HarnessOrchestrator:
    """
    KNOT 기반 멀티 에이전트 오케스트레이터.
    수집(GitHub Actions) → 초안 생성(Anthropic API) → 검수(사람) → 발행
    """

    def __init__(self, vault_path: str = "./"):
        self.vault_path = os.path.abspath(vault_path)
        self.config = self._load_config()
        self.system_principles = self._load_principles()
        self.gcp_project  = os.environ.get("GCP_PROJECT_ID", "geonchicsproject")
        self.gemini_model = os.environ.get("GEMINI_MODEL_NAME", "publishers/google/models/gemini-2.5-flash")
        self.creds_path   = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        print(f"[Harness] 오케스트레이터 초기화 완료 — Vault: {self.vault_path}")
        if not self.creds_path or not os.path.exists(self.creds_path):
            print("[Harness] 경고: GCP 서비스 계정 키 없음 — GOOGLE_APPLICATION_CREDENTIALS 설정 필요")

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
    # Gemini Vertex AI 호출 (janus agent와 동일한 인프라)
    # ──────────────────────────────────────────────────────────────

    def _call_gemini(self, prompt: str, max_tokens: int = 4096) -> str:
        """
        GCP Vertex AI + Gemini 2.5 Flash 호출.
        janus agent의 gcp-key.json / GCP_PROJECT_ID와 동일한 인프라 사용.
        GOOGLE_APPLICATION_CREDENTIALS 환경변수로 서비스 계정 키 경로 지정.
        """
        if not _GEMINI_AVAILABLE:
            raise RuntimeError(
                "google-genai 패키지 없음.\n"
                "pip install google-genai google-auth 실행 후 재시도하세요."
            )
        if self.creds_path and os.path.exists(self.creds_path):
            from google.oauth2 import service_account as _sa
            creds = _sa.Credentials.from_service_account_file(
                self.creds_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            client = _genai.Client(
                vertexai=True,
                project=self.gcp_project,
                location="us-central1",
                credentials=creds,
            )
        else:
            # ADC 폴백 (로컬 gcloud auth application-default login 환경)
            client = _genai.Client(
                vertexai=True,
                project=self.gcp_project,
                location="us-central1",
            )
        response = client.models.generate_content(
            model=self.gemini_model,
            contents=prompt,
            config=_genai_types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=0.3,
            ),
        )
        return response.text

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
    # Worker: 블로그 초안 자동 생성 — 2단계 파이프라인
    # Stage 1: Gemini (작가) → 원시 초안
    # Stage 2: Gemini (편집장) → 품질 검토 및 개선
    # ──────────────────────────────────────────────────────────────

    def _generate_draft(self, topic: str, shared_ctx: str, intel_ctx: str) -> str:
        """
        2단계 파이프라인으로 블로그 초안을 생성합니다.
        Stage 1 (작가): 인텔 기반 원시 초안 작성
        Stage 2 (편집장): SEO·팩트·어조 검토 후 최종본 출력
        결과물은 blog/drafts/ 에 저장되며, 사람 검수 후 blog/posts/ 로 이동.
        """
        today = datetime.date.today().isoformat()

        # ── Stage 1: 작가 — 원시 초안 ──────────────────────────
        print("\n[Stage 1 / 2] ▶ Gemini (작가) — 원시 초안 생성 중...")

        writer_prompt = f"""You are a sharp AI content writer for "AI Frontier" — a blog for English-speaking AI developers who follow Karpathy and Anthropic.

TODAY'S INTEL (RSS collection):
{intel_ctx[:3000]}

CONTEXT for topic "{topic}":
{shared_ctx[:800]}

TASK:
Pick the single most interesting/relevant item from the intel above related to "{topic}" and write a blog post HTML fragment about it.

REQUIREMENTS:
- HTML fragment only (no <html>/<head>/<body> tags — just inner article content)
- Title: under 65 chars with a strong keyword
- Length: 600–900 words
- Structure: Hook → Background → What happened → Developer impact → Takeaway + CTA
- Include a code example or concrete numbers if the source material supports it
- Tone: direct, technical but readable. Zero fluff.
- CTA last line: link back to <a href="../index.html">AI Frontier</a>

OUTPUT FORMAT — two sections separated by ---META---:

[HTML fragment here]

---META---
SLUG: url-friendly-slug-here
TITLE: Full Post Title Here
DESCRIPTION: Meta description under 155 chars
CATEGORY: karpathy | anthropic | news | tools
DATE: {today}
SOURCE_URL: (original link from intel if available)
"""

        try:
            stage1_output = self._call_gemini(writer_prompt, max_tokens=3000)
            print("[Stage 1] 완료 ✓")
        except Exception as e:
            print(f"[Stage 1 오류] {e}")
            return f"DRAFT_FAILED_STAGE1: {e}"

        # META 파싱
        meta = {"slug": topic, "title": topic, "description": "",
                "category": "news", "date": today, "source_url": ""}
        if "---META---" in stage1_output:
            raw_html, meta_block = stage1_output.split("---META---", 1)
            raw_html = raw_html.strip()
            for line in meta_block.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
        else:
            raw_html = stage1_output.strip()

        # ── Stage 2: 편집장 — 품질 검토 및 개선 ───────────────
        print("\n[Stage 2 / 2] ▶ Gemini (편집장) — 품질 검토 및 개선 중...")

        editor_prompt = f"""You are a strict editorial AI for "AI Frontier" blog.
Your job: review the draft below and output an improved, publication-ready version.

EDITORIAL CHECKLIST (fix all issues silently — do NOT explain changes):
1. SEO: Title must be under 65 chars and include the primary keyword. Meta description under 155 chars.
2. Factual flags: Add an HTML comment <!-- VERIFY: ... --> next to any claim that needs human fact-checking (dates, version numbers, quotes).
3. Tone: Remove any marketing fluff. Every sentence must earn its place.
4. Structure: Hook in the first 2 sentences. Clear H2 sections. Takeaway is specific, not generic.
5. Code: If a code snippet is present, ensure it is syntactically plausible. If not present but would strengthen the post, add a short illustrative example.
6. AdSense policy: No excessive external links, no clickbait titles, no misleading claims.
7. CTA: Exactly one call-to-action at the end linking to ../index.html.

DRAFT TO REVIEW:
{raw_html}

ORIGINAL META:
Title: {meta.get('title')}
Description: {meta.get('description')}
Category: {meta.get('category')}

OUTPUT FORMAT — same two-section format:

[Improved HTML fragment]

---META---
SLUG: {meta.get('slug')}
TITLE: (keep or improve)
DESCRIPTION: (keep or improve, under 155 chars)
CATEGORY: {meta.get('category')}
DATE: {today}
SOURCE_URL: {meta.get('source_url', '')}
EDITOR_NOTES: (1–3 bullet points of what was changed or flagged for human review)
"""

        try:
            stage2_output = self._call_gemini(editor_prompt, max_tokens=3500)
            print("[Stage 2] 완료 ✓")
        except Exception as e:
            print(f"[Stage 2 오류] {e} — Stage 1 결과물을 저장합니다.")
            stage2_output = stage1_output  # 편집 실패 시 Stage 1 결과 사용

        # Stage 2 META 파싱
        if "---META---" in stage2_output:
            final_html, final_meta_block = stage2_output.split("---META---", 1)
            final_html = final_html.strip()
            for line in final_meta_block.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    key = k.strip().lower()
                    if key == "editor_notes":
                        meta["editor_notes"] = v.strip()
                    else:
                        meta[key] = v.strip()
        else:
            final_html = stage2_output.strip()

        # 편집장 노트 출력
        if meta.get("editor_notes"):
            print(f"\n[편집장 노트]\n{meta['editor_notes']}\n")

        # 최종 초안 저장
        draft_path = self._save_draft(final_html, meta)
        print(f"\n[Harness] ✅ 최종 초안 저장: {draft_path}")
        print("[검수 필요] blog/drafts/ 에서 내용을 확인하고 blog/posts/ 로 이동하세요.")
        return draft_path

    def _save_draft(self, html_fragment: str, meta: dict) -> str:
        """초안을 blog/drafts/ 에 전체 HTML로 감싸서 저장. 편집장 노트 포함."""
        drafts_dir = os.path.join(self.vault_path, "blog", "drafts")
        os.makedirs(drafts_dir, exist_ok=True)

        slug = meta.get("slug", "draft")
        filename = f"{meta['date']}-{slug}.html"
        output_path = os.path.join(drafts_dir, filename)

        # 편집장 노트를 HTML 주석으로 삽입
        if meta.get("editor_notes"):
            editor_comment = f"\n<!-- EDITOR NOTES\n{meta['editor_notes']}\n-->\n"
            html_fragment = editor_comment + html_fragment

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
