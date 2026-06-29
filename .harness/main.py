import os
import json
import datetime

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


class HarnessOrchestrator:
    """
    KNOT 기반 멀티 에이전트 오케스트레이터.
    Claude(지휘자) → Codex(웹 빌드) / Gemini(카드뉴스) / Linter(품질검사)
    """

    def __init__(self, vault_path: str = "./"):
        self.vault_path = os.path.abspath(vault_path)
        self.config = self._load_config()
        self.system_principles = self._load_principles()
        print(f"[Harness] 오케스트레이터 초기화 완료 — Vault: {self.vault_path}")

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

    def get_shared_memory(self, keyword: str) -> str:
        """KNOT 위키에서 공유 기억을 읽어오는 핵심 메서드"""
        wiki_path = os.path.join(self.vault_path, "02_wiki", f"{keyword}.md")
        if os.path.exists(wiki_path):
            with open(wiki_path, "r", encoding="utf-8") as f:
                return f.read()
        return "공유된 기존 기억 없음 — 신규 자산화가 필요합니다."

    def save_to_wiki(self, keyword: str, content: str, subfolder: str = ""):
        """생성된 결과물을 KNOT 위키에 영구 자산화"""
        wiki_dir = os.path.join(self.vault_path, "02_wiki", subfolder)
        os.makedirs(wiki_dir, exist_ok=True)
        date_str = datetime.date.today().isoformat()
        filename = f"{keyword}-{date_str}.md"
        output_path = os.path.join(wiki_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[Harness] 위키 저장 완료: {output_path}")
        return output_path

    def execute_workflow(self, task_type: str, topic: str) -> str:
        """에이전트 워크플로우 실행 진입점"""
        print(f"\n{'='*60}")
        print(f"[Harness] 태스크 가동: {task_type} | 토픽: {topic}")
        print(f"{'='*60}")

        shared_ctx = self.get_shared_memory(topic)

        if task_type == "BUILD_UTILITY_WEB":
            return self._build_utility_web(topic, shared_ctx)

        elif task_type == "GENERATE_CARD_NEWS":
            return self._generate_card_news(topic, shared_ctx)

        elif task_type == "LINT_WEB":
            return self._lint_web(topic)

        elif task_type == "FULL_PIPELINE":
            print("[Harness] 풀 파이프라인 가동: 빌드 → 린트 → 카드뉴스")
            self.execute_workflow("BUILD_UTILITY_WEB", topic)
            self.execute_workflow("LINT_WEB", topic)
            return self.execute_workflow("GENERATE_CARD_NEWS", topic)

        else:
            raise ValueError(f"알 수 없는 task_type: {task_type}")

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
        # ─── 실제 LLM API 연동 구역 ───────────────────────────────────
        # Cursor API 또는 OpenAI/Anthropic 엔드포인트를 이곳에 바인딩하세요.
        # response = cursor_api.call(model="codex", prompt=prompt)
        # ──────────────────────────────────────────────────────────────
        print(f"[Codex 프롬프트 생성 완료] 길이: {len(prompt)}자")
        print("[안내] Cursor 채팅창에 아래 프롬프트를 붙여넣어 웹 빌드를 시작하세요.")
        print("-" * 40)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        return prompt

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
            f"Task: '{topic}' 메타 보너스 수령용 카드뉴스 5장 대본 + DALL-E 이미지 프롬프트 추출\n"
            f"출력 형식: 슬라이드별 텍스트 대본 + 이미지 생성 프롬프트 + 인스타 캡션"
        )
        print(f"[Gemini 프롬프트 생성 완료] 길이: {len(prompt)}자")
        return "## CARD_NEWS_SCRIPT_READY\n\n" + prompt

    def _lint_web(self, topic: str) -> str:
        print("[Harness Worker] ▶ Linter 에이전트 활성화 → 품질 검사")
        lint_script = os.path.join(self.vault_path, "03_lint", "lint_check.py")
        if not os.path.exists(lint_script):
            print("[경고] lint_check.py 없음 — 린트를 건너뜁니다.")
            return "LINT_SKIPPED"
        product_dir = os.path.join(self.vault_path, "02_wiki", "02A_products")
        print(f"[Linter] 검사 대상: {product_dir}")
        os.system(f'python "{lint_script}" --target "{product_dir}"')
        return "LINT_COMPLETE"


if __name__ == "__main__":
    orchestrator = HarnessOrchestrator(vault_path="./")

    # 사용 예시 — 원하는 태스크를 선택하여 실행
    # orchestrator.execute_workflow("BUILD_UTILITY_WEB", "compound-interest-calculator")
    # orchestrator.execute_workflow("GENERATE_CARD_NEWS", "compound-interest-calculator")
    # orchestrator.execute_workflow("LINT_WEB", "compound-interest-calculator")
    orchestrator.execute_workflow("FULL_PIPELINE", "compound-interest-calculator")
