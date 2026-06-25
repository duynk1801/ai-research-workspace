from src.modules.search import multi_search


def quick_search(topic: str) -> list[dict]:
    results = multi_search(topic, ["github", "arxiv", "web"], limit=5)
    items = []
    for source, entries in results.get("sources", {}).items():
        for item in entries:
            if item.get("type") != "error":
                items.append({
                    "source": source,
                    "title": item["title"],
                    "url": item.get("url", ""),
                    "description": item.get("description", "")[:150],
                    "stars": item.get("stars"),
                    "language": item.get("language", ""),
                    "topics": item.get("topics", []),
                })
    return items


def analyze_results(topic: str, results: list[dict]) -> dict:
    all_text = " ".join(
        f"{r['title']} {r['description']} {r.get('language', '')} {' '.join(r.get('topics', []))}"
        for r in results
    ).lower()

    topic_lower = topic.lower()

    code_indicators = ["library", "framework", "tool", "cli", "api", "sdk", "package",
                       "pip", "npm", "build", "develop", "implement", "python", "javascript",
                       "code", "github", "repo", "install", "import"]
    paper_indicators = ["paper", "research", "study", "survey", "review", "analysis",
                        "algorithm", "model", "dataset", "benchmark", "theory", "academic"]

    code_hits = sum(1 for w in code_indicators if w in all_text or w in topic_lower)
    paper_hits = sum(1 for w in paper_indicators if w in all_text or w in topic_lower)

    languages = {}
    for r in results:
        lang = r.get("language", "")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1

    top_languages = sorted(languages.keys(), key=lambda x: languages[x], reverse=True)[:3]

    all_topics = []
    for r in results:
        all_topics.extend(r.get("topics", []))
    unique_topics = list(dict.fromkeys(all_topics))[:8]

    stars = [r["stars"] for r in results if r.get("stars") is not None]
    avg_stars = sum(stars) // len(stars) if stars else 0

    github_count = sum(1 for r in results if r["source"] == "github")
    arxiv_count = sum(1 for r in results if r["source"] == "arxiv")

    is_code = code_hits >= paper_hits
    is_paper = paper_hits > 0

    existing_tools = []
    for r in results:
        if (r.get("stars") or 0) > 100:
            existing_tools.append(f"{r['title']} ({r.get('stars', 0)} stars)")

    return {
        "is_code": is_code,
        "is_paper": is_paper,
        "top_languages": top_languages,
        "related_topics": unique_topics,
        "avg_stars": avg_stars,
        "existing_tools": existing_tools,
        "github_count": github_count,
        "arxiv_count": arxiv_count,
    }


def get_problem_definition_questions(topic: str, analysis: dict) -> list[dict]:
    existing = analysis.get("existing_tools", [])
    topics = analysis.get("related_topics", [])
    langs = analysis.get("top_languages", [])

    context_hints = []
    if existing:
        context_hints.append(f"Đã có: {', '.join(existing[:3])}")
    if topics:
        context_hints.append(f"Topics liên quan: {', '.join(topics[:5])}")
    if langs:
        context_hints.append(f"Ngôn ngữ phổ biến: {', '.join(langs)}")

    questions = [
        {
            "id": "what",
            "label": "WHAT",
            "question": "Bài toán cụ thể bạn muốn giải quyết là gì?",
            "hint": "Mô tả ngắn gọn: bạn muốn build, tìm hiểu, hay tạo mới cái gì?",
            "context": "\n   ".join(context_hints) if context_hints else "",
        },
        {
            "id": "why",
            "label": "WHY",
            "question": "Tại sao bạn cần điều này? Vấn đề hiện tại là gì?",
            "hint": "Cái gì đang chưa tốt mà bạn muốn cải thiện?",
            "context": "",
        },
        {
            "id": "who",
            "label": "WHO",
            "question": "Đối tượng sử dụng là ai?",
            "hint": "Bạn (self-use), developer team, hay end-user không chuyên?",
            "context": "",
        },
        {
            "id": "scope",
            "label": "SCOPE",
            "question": "Giới hạn của bài toán?",
            "hint": "Cái gì BINCLUDED và EXCLUDED? Ví dụ: chỉ Python, chỉ web, chỉ mobile...",
            "context": "",
        },
        {
            "id": "depth",
            "label": "DEPTH",
            "question": "Bạn cần depth đến đâu?",
            "hint": "Overview (tổng quan) / Deep dive (sâu 1 hướng) / Novel (tạo cái mới)",
            "context": "",
        },
    ]

    return questions


def format_problem_definition(answers: dict) -> str:
    lines = []
    for key in ["what", "why", "who", "scope", "depth"]:
        label = key.upper()
        answer = answers.get(key, "N/A")
        lines.append(f"  {label}: {answer}")
    return "\n".join(lines)


def is_problem_defined(answers: dict) -> bool:
    required = ["what", "why", "who", "scope", "depth"]
    filled = sum(1 for k in required if answers.get(k, "").strip())
    return filled >= 4
