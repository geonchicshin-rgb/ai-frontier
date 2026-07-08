"""
intel_collector.py — Karpathy · Anthropic AI 인텔 자동 수집기
매일 오전 8시 Windows 작업 스케줄러로 자동 실행됩니다.
실행: python .harness/intel_collector.py
스케줄러 등록: python .harness/intel_collector.py --schedule
"""

import os
import sys
import datetime
import urllib.request
import xml.etree.ElementTree as ET

RSS_SOURCES = [
    # ── Karpathy ──────────────────────────────────────────────────
    {
        "name": "Karpathy YouTube",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCPk8m_r6fkUSYmvgCBwq-sw",
        "category": "karpathy",
    },
    {
        "name": "Karpathy - llm.c 커밋",
        "url": "https://github.com/karpathy/llm.c/commits/master.atom",
        "category": "karpathy",
    },
    {
        "name": "Karpathy - nanoGPT 커밋",
        "url": "https://github.com/karpathy/nanoGPT/commits/master.atom",
        "category": "karpathy",
    },
    # ── Anthropic ─────────────────────────────────────────────────
    {
        "name": "Anthropic News",
        "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
        "category": "anthropic",
    },
    {
        "name": "Anthropic Engineering Blog",
        "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
        "category": "anthropic",
    },
    {
        "name": "Anthropic - anthropic-cookbook 커밋",
        "url": "https://github.com/anthropics/anthropic-cookbook/commits/main.atom",
        "category": "anthropic",
    },
    {
        "name": "Anthropic SDK Python 릴리즈",
        "url": "https://github.com/anthropics/anthropic-sdk-python/releases.atom",
        "category": "anthropic",
    },
    # ── AI 뉴스 ───────────────────────────────────────────────────
    {
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
        "category": "news",
    },
    {
        "name": "Ahead of AI (Sebastian Raschka)",
        "url": "https://magazine.sebastianraschka.com/feed",
        "category": "news",
    },
    {
        "name": "Simon Willison (AI 뉴스 큐레이터)",
        "url": "https://simonwillison.net/atom/everything/",
        "category": "news",
    },
    # ── AI 도구 ───────────────────────────────────────────────────
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "tools",
    },
    {
        "name": "LangChain 릴리즈",
        "url": "https://github.com/langchain-ai/langchain/releases.atom",
        "category": "tools",
    },
]


def fetch_feed(url: str, timeout: int = 10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KNOT-Intel/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  [오류] {url[:60]} — {e}")
        return None


def parse_atom(xml_text: str, max_items: int = 3) -> list:
    items = []
    try:
        root = ET.fromstring(xml_text)
        ns = "http://www.w3.org/2005/Atom"
        media_ns = "http://search.yahoo.com/mrss/"

        for entry in root.findall(f"{{{ns}}}entry")[:max_items]:
            title_el = entry.find(f"{{{ns}}}title")
            link_el = entry.find(f"{{{ns}}}link")
            # updated 없으면 published 로 폴백 (YouTube, HuggingFace 등)
            date_el = (
                entry.find(f"{{{ns}}}updated")
                or entry.find(f"{{{ns}}}published")
            )
            # summary → content → media:description 순으로 폴백
            summary_el = (
                entry.find(f"{{{ns}}}summary")
                or entry.find(f"{{{ns}}}content")
                or entry.find(f"{{{media_ns}}}group/{{{media_ns}}}description")
            )

            title = (title_el.text or "(제목 없음)").strip() if title_el is not None else "(제목 없음)"
            link = link_el.get("href", "") if link_el is not None else ""
            date = (date_el.text or "")[:10] if date_el is not None else ""
            summary = ""
            if summary_el is not None and summary_el.text:
                raw = summary_el.text.strip()
                summary = raw[:250].replace("\n", " ") + ("..." if len(raw) > 250 else "")

            items.append({"title": title, "link": link, "date": date, "summary": summary})
    except Exception as e:
        print(f"  [파싱 오류] {e}")
    return items


def build_report(results: list, today: str) -> str:
    category_meta = {
        "karpathy": "## 🧠 Andrej Karpathy",
        "anthropic": "## 🤖 Anthropic",
        "news":      "## 📰 AI 뉴스 큐레이터",
        "tools":     "## 🛠️ AI 도구 업데이트",
    }

    grouped = {}
    for r in results:
        grouped.setdefault(r["category"], []).append(r)

    lines = [
        f"---",
        f"date: {today}",
        f"type: intel-report",
        f"status: unread",
        f"blog_candidate: false",
        f"---",
        f"",
        f"# AI 인텔 보고서 — {today}",
        f"> 자동 수집: Karpathy · Anthropic · AI 뉴스  ",
        f"> 흥미로운 항목을 아래 '블로그 소재 후보'에 체크하고 [[02_wiki/blog-posts/]] 로 이동하세요.",
        f"",
    ]

    for cat, heading in category_meta.items():
        if cat not in grouped:
            continue
        lines.append(heading)
        lines.append("")
        for item in grouped[cat]:
            lines.append(f"### [{item['title']}]({item['link']})")
            if item["date"]:
                lines.append(f"- 날짜: `{item['date']}`")
            if item["summary"]:
                lines.append(f"- 요약: {item['summary']}")
            lines.append(f"- 소스: {item['source_name']}")
            lines.append("")

    lines += [
        "---",
        "",
        "## 📝 블로그 소재 후보 (오늘 선택)",
        "",
        "- [ ] (위 항목 중 선택하여 작성)",
        "- [ ] ",
        "",
        "## 🔗 X(트위터) 수동 확인 목록 — 매주 월요일",
        "- [ ] [@karpathy](https://x.com/karpathy)",
        "- [ ] [@AnthropicAI](https://x.com/AnthropicAI)",
        "- [ ] [@sama](https://x.com/sama)",
        "- [ ] [@simonw](https://x.com/simonw)",
        "- [ ] [@ylecun](https://x.com/ylecun)",
        "- [ ] [@hwchung27](https://x.com/hwchung27)",
    ]

    return "\n".join(lines)


def register_scheduler():
    script_abs = os.path.abspath(__file__)
    python_exe = sys.executable
    task_name = "KNOT_IntelCollector"
    ps_script = os.path.join(os.path.dirname(script_abs), "setup_scheduler.ps1")

    print(f"[스케줄러] PowerShell 스크립트로 등록합니다: {ps_script}")
    os.system(f'powershell -ExecutionPolicy Bypass -File "{ps_script}"')


def main():
    vault_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    inbox_path = os.path.join(vault_path, "01_inbox")
    os.makedirs(inbox_path, exist_ok=True)

    today = datetime.date.today().isoformat()
    output_path = os.path.join(inbox_path, f"intel-{today}.md")

    if os.path.exists(output_path):
        print(f"[Intel] 오늘 보고서 이미 존재: {output_path}")
        return

    print(f"\n{'='*55}")
    print(f"  KNOT Intel Collector — {today}")
    print(f"{'='*55}")

    all_items = []
    for source in RSS_SOURCES:
        print(f"\n[수집] {source['name']}")
        xml = fetch_feed(source["url"])
        if not xml:
            continue
        items = parse_atom(xml, max_items=3)
        for item in items:
            item["source_name"] = source["name"]
            item["category"] = source["category"]
        all_items.extend(items)
        print(f"  → {len(items)}건 수집")

    report = build_report(all_items, today)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'='*55}")
    print(f"  완료: {output_path}")
    print(f"  Obsidian에서 01_inbox/intel-{today}.md 를 확인하세요.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    if "--schedule" in sys.argv:
        register_scheduler()
    else:
        main()
