from src.db.knowledge_dao import (
    create_session, update_session, get_session,
    insert_insight, search_insights, list_insights,
    get_insight, get_insights_by_session, get_insights_by_maturity, get_stats
)


class KnowledgeBase:
    def __init__(self):
        self.current_session_id = None

    def start_session(self, topic: str, requirements: str = "") -> int:
        self.current_session_id = create_session(topic, requirements)
        return self.current_session_id

    def finish_session(self, requirements: str = None):
        if self.current_session_id:
            update_session(self.current_session_id, requirements=requirements, status="completed")

    def save_insight(self, insight: dict) -> int:
        return insert_insight(
            session_id=self.current_session_id,
            topic=insight.get("topic", ""),
            insight_type=insight.get("type", "IDEA"),
            title=insight.get("title", ""),
            content=insight.get("content", ""),
            main_idea=insight.get("main_idea", ""),
            core_approach=insight.get("core_approach", ""),
            strengths=insight.get("strengths", []),
            limitations=insight.get("limitations", []),
            gaps=insight.get("gaps", []),
            relevance=insight.get("relevance", ""),
            maturity=insight.get("maturity", "S1"),
            source_url=insight.get("source_url", ""),
            source_type=insight.get("source_type", ""),
            tags=insight.get("tags", [])
        )

    def save_insights(self, insights: list[dict]) -> list[int]:
        return [self.save_insight(i) for i in insights]

    def search(self, query: str, limit: int = 10) -> list[dict]:
        return search_insights(query, limit)

    def list_all(self, limit: int = 20, offset: int = 0) -> list[dict]:
        return list_insights(limit, offset)

    def get(self, insight_id: int) -> dict | None:
        return get_insight(insight_id)

    def get_by_session(self, session_id: int) -> list[dict]:
        return get_insights_by_session(session_id)

    def get_by_maturity(self, maturity: str, limit: int = 20) -> list[dict]:
        return get_insights_by_maturity(maturity, limit)

    def get_all_insights(self) -> list[dict]:
        return list_insights(limit=1000)

    def stats(self) -> dict:
        return get_stats()
