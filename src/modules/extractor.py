import json
import logging
from src.llm import chat_json
from src.prompts.extraction import (
    EXTRACTION_SYSTEM, EXTRACTION_PROMPT,
    QUERY_SYSTEM, QUERY_PROMPT,
    IDEATE_SYSTEM, IDEATE_PROMPT
)

logger = logging.getLogger(__name__)


def extract_insights(content: str, source_title: str = "", source_type: str = "web",
                     source_url: str = "") -> dict:
    if not content or len(content.strip()) < 20:
        return {"insights": [], "summary": "Content too short to extract insights"}

    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM},
        {"role": "user", "content": EXTRACTION_PROMPT.format(
            source_title=source_title,
            source_type=source_type,
            source_url=source_url,
            content=content[:4000]
        )}
    ]

    try:
        result = chat_json(messages, temperature=0.3)
    except Exception as e:
        logger.error(f"Extraction failed for {source_title}: {e}")
        return {"insights": [], "summary": f"Extraction failed: {e}"}

    if isinstance(result, dict) and result.get("parse_error"):
        return {"insights": [], "summary": "Failed to parse extraction results"}

    if isinstance(result, dict) and "insights" in result:
        return result

    if isinstance(result, dict) and "raw" in result:
        return {"insights": [], "summary": "LLM returned unparseable output"}

    return {"insights": [], "summary": "Failed to extract insights"}


def extract_from_github(repo: dict, readme: str) -> list[dict]:
    try:
        result = extract_insights(
            content=readme,
            source_title=repo["title"],
            source_type="github",
            source_url=repo["url"]
        )
    except Exception as e:
        logger.error(f"GitHub extraction failed for {repo['title']}: {e}")
        return []

    insights = []
    for item in result.get("insights", []):
        if isinstance(item, dict) and item.get("title"):
            insights.append({
                "type": item.get("type", "IDEA"),
                "title": item.get("title", ""),
                "main_idea": item.get("main_idea", ""),
                "core_approach": item.get("core_approach", ""),
                "strengths": item.get("strengths", []),
                "limitations": item.get("limitations", []),
                "gaps": item.get("gaps", []),
                "relevance": item.get("relevance", ""),
                "maturity": item.get("maturity", "S1"),
                "tags": item.get("tags", []),
                "source_url": repo["url"],
                "source_type": "github",
            })
    return insights


def extract_from_arxiv(paper: dict) -> list[dict]:
    try:
        result = extract_insights(
            content=paper.get("description", ""),
            source_title=paper["title"],
            source_type="arxiv",
            source_url=paper["url"]
        )
    except Exception as e:
        logger.error(f"Arxiv extraction failed for {paper['title']}: {e}")
        return []

    insights = []
    for item in result.get("insights", []):
        if isinstance(item, dict) and item.get("title"):
            insights.append({
                "type": item.get("type", "IDEA"),
                "title": item.get("title", ""),
                "main_idea": item.get("main_idea", ""),
                "core_approach": item.get("core_approach", ""),
                "strengths": item.get("strengths", []),
                "limitations": item.get("limitations", []),
                "gaps": item.get("gaps", []),
                "relevance": item.get("relevance", ""),
                "maturity": item.get("maturity", "S1"),
                "tags": item.get("tags", []),
                "source_url": paper["url"],
                "source_type": "arxiv",
            })
    return insights


def query_kb(topic: str, requirements: dict, existing_insights: list[dict]) -> dict:
    insights_text = "\n".join([
        f"- [{i.get('id')}] {i.get('title')}: {i.get('main_idea', '')}"
        for i in existing_insights[:20]
    ])

    messages = [
        {"role": "system", "content": QUERY_SYSTEM},
        {"role": "user", "content": QUERY_PROMPT.format(
            topic=topic,
            requirements=json.dumps(requirements, ensure_ascii=False),
            existing_insights=insights_text or "No existing insights"
        )}
    ]

    try:
        result = chat_json(messages, temperature=0.3)
        if isinstance(result, dict) and not result.get("parse_error"):
            return result
    except Exception as e:
        logger.error(f"KB query failed: {e}")

    return {"relevant_insights": [], "connections": [], "gaps": [], "suggested_research": []}


def generate_ideas(topic: str, insights: list[dict], gaps: list[dict]) -> dict:
    insights_text = "\n".join([
        f"- {i.get('title')}: {i.get('main_idea', '')}"
        for i in insights[:15]
    ])
    gaps_text = "\n".join([f"- {g}" for g in gaps[:10]])

    messages = [
        {"role": "system", "content": IDEATE_SYSTEM},
        {"role": "user", "content": IDEATE_PROMPT.format(
            topic=topic,
            insights=insights_text or "No existing insights",
            gaps=gaps_text or "No identified gaps"
        )}
    ]

    try:
        result = chat_json(messages, temperature=0.7)
        if isinstance(result, dict) and not result.get("parse_error"):
            return result
    except Exception as e:
        logger.error(f"Ideation failed: {e}")

    return {"ideas": []}
