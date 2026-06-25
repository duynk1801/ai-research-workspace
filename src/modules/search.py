import httpx
import xml.etree.ElementTree as ET
from src.config import GITHUB_TOKEN


def search_github(query: str, limit: int = 5) -> list[dict]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": limit}

    try:
        resp = httpx.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("items", [])[:limit]:
            results.append({
                "type": "github",
                "title": item["full_name"],
                "url": item["html_url"],
                "description": item.get("description", ""),
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
        "max_results": limit,
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
        sources = ["github", "arxiv"]

    results = {"query": query, "sources": {}}

    if "github" in sources:
        results["sources"]["github"] = search_github(query, limit)
    if "arxiv" in sources:
        results["sources"]["arxiv"] = search_arxiv(query, limit)

    results["total"] = sum(len(v) for v in results["sources"].values())
    return results
