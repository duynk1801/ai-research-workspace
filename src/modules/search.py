import httpx
import xml.etree.ElementTree as ET
from src.config import GITHUB_TOKEN


def search_github(query: str, limit: int = 5) -> list[dict]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": limit * 2}

    try:
        resp = httpx.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("items", [])[:limit * 2]:
            results.append({
                "type": "github",
                "title": item["full_name"],
                "url": item["html_url"],
                "description": item.get("description", "") or "",
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language", ""),
                "topics": item.get("topics", []),
            })
        return results
    except Exception as e:
        return [{"type": "error", "message": f"GitHub search failed: {e}"}]


def search_arxiv(query: str, limit: int = 5) -> list[dict]:
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": limit * 2,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }

    try:
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        results = []

        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            link = entry.find("atom:id", ns)
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]

            results.append({
                "type": "arxiv",
                "title": title.text.strip().replace("\n", " ") if title is not None else "",
                "url": link.text.strip() if link is not None else "",
                "description": summary.text.strip()[:500].replace("\n", " ") if summary is not None else "",
                "authors": authors[:3],
            })
        return results
    except Exception as e:
        return [{"type": "error", "message": f"Arxiv search failed: {e}"}]


def search_web(query: str, limit: int = 5) -> list[dict]:
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=15, follow_redirects=True)
        results = []

        import re
        snippets = re.findall(r'class="result__snippet">(.*?)</a>', resp.text, re.DOTALL)
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
        urls = re.findall(r'class="result__url"[^>]*>(.*?)</a>', resp.text, re.DOTALL)

        for i in range(min(limit, len(titles))):
            title = re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else ""
            url_str = re.sub(r'<[^>]+>', '', urls[i]).strip() if i < len(urls) else ""
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""

            if title and url_str:
                results.append({
                    "type": "web",
                    "title": title,
                    "url": url_str,
                    "description": snippet[:200],
                })

        return results
    except Exception as e:
        return [{"type": "error", "message": f"Web search failed: {e}"}]


def search_stackoverflow(query: str, limit: int = 3) -> list[dict]:
    url = "https://api.stackexchange.com/2.3/search"
    params = {
        "order": "desc",
        "sort": "relevance",
        "intitle": query,
        "site": "stackoverflow",
        "pagesize": limit,
    }

    try:
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("items", [])[:limit]:
            results.append({
                "type": "stackoverflow",
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "description": "",
                "score": item.get("score", 0),
                "tags": item.get("tags", []),
                "answer_count": item.get("answer_count", 0),
            })
        return results
    except Exception as e:
        return [{"type": "error", "message": f"StackOverflow search failed: {e}"}]


def filter_relevant(results: list[dict], topic: str) -> list[dict]:
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "for", "and", "or",
                  "of", "to", "in", "on", "with", "by", "from", "at", "as", "be",
                  "của", "và", "cho", "các", "là", "có", "trong", "với", "từ"}

    topic_words = set(topic.lower().split()) - stop_words
    filtered = []

    for r in results:
        if r.get("type") == "error":
            continue

        text = f"{r.get('title', '')} {r.get('description', '')}".lower()
        text_words = set(text.split())

        overlap = len(topic_words & text_words)

        if len(topic_words) <= 2:
            required_overlap = 1
        elif len(topic_words) <= 4:
            required_overlap = 2
        else:
            required_overlap = len(topic_words) // 2

        if overlap >= required_overlap:
            filtered.append(r)

    return filtered


def fetch_github_readme(repo_url: str) -> str:
    parts = repo_url.rstrip("/").split("/")
    owner, repo = parts[-2], parts[-1]

    headers = {"Accept": "application/vnd.github.v3.raw"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        resp = httpx.get(
            f"https://api.github.com/repos/{owner}/{repo}/readme",
            headers=headers, timeout=15
        )
        resp.raise_for_status()
        return resp.text[:3000]
    except Exception:
        return ""


def fetch_arxiv_abstract(url: str) -> str:
    try:
        resp = httpx.get(url, timeout=15)
        return resp.text[:3000]
    except Exception:
        return ""


def multi_search(query: str, sources: list[str] = None, limit: int = 3) -> dict:
    if sources is None:
        sources = ["github", "arxiv", "web", "stackoverflow"]

    results = {"query": query, "sources": {}}

    if "github" in sources:
        raw = search_github(query, limit)
        results["sources"]["github"] = filter_relevant(raw, query)[:limit]
    if "arxiv" in sources:
        raw = search_arxiv(query, limit)
        results["sources"]["arxiv"] = filter_relevant(raw, query)[:limit]
    if "web" in sources:
        raw = search_web(query, limit)
        results["sources"]["web"] = filter_relevant(raw, query)[:limit]
    if "stackoverflow" in sources:
        raw = search_stackoverflow(query, limit)
        results["sources"]["stackoverflow"] = filter_relevant(raw, query)[:limit]

    results["total"] = sum(len(v) for v in results["sources"].values())
    return results
