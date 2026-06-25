import json
from datetime import datetime
from src.db.schema import get_connection


def create_session(topic: str, requirements: str = "") -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO sessions (topic, requirements, status) VALUES (?, ?, 'active')",
        (topic, requirements)
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def update_session(session_id: int, requirements: str = None, status: str = None):
    conn = get_connection()
    updates = []
    params = []
    if requirements is not None:
        updates.append("requirements = ?")
        params.append(requirements)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if updates:
        params.append(session_id)
        conn.execute(f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    conn.close()


def get_session(session_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def insert_insight(session_id: int, topic: str, insight_type: str, title: str,
                   content: str = "", main_idea: str = "", core_approach: str = "",
                   strengths: list[str] = None, limitations: list[str] = None,
                   gaps: list[str] = None, relevance: str = "", maturity: str = "S1",
                   source_url: str = "", source_type: str = "", tags: list[str] = None) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO insights (session_id, topic, insight_type, title, content,
           main_idea, core_approach, strengths, limitations, gaps, relevance, maturity,
           source_url, source_type, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, topic, insight_type, title, content, main_idea, core_approach,
         json.dumps(strengths or []), json.dumps(limitations or []),
         json.dumps(gaps or []), relevance, maturity,
         source_url, source_type, json.dumps(tags or []))
    )
    insight_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return insight_id


def search_insights(query: str, limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT i.* FROM insights i
           JOIN insights_fts f ON i.id = f.rowid
           WHERE insights_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (query, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_insights(limit: int = 20, offset: int = 0) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM insights ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_insight(insight_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM insights WHERE id = ?", (insight_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_insights_by_session(session_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM insights WHERE session_id = ? ORDER BY created_at",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_insights_by_maturity(maturity: str, limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM insights WHERE maturity = ? ORDER BY created_at DESC LIMIT ?",
        (maturity, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    conn = get_connection()
    total_insights = conn.execute("SELECT COUNT(*) FROM insights").fetchone()[0]
    total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    by_type = conn.execute(
        "SELECT insight_type, COUNT(*) as cnt FROM insights GROUP BY insight_type"
    ).fetchall()
    by_maturity = conn.execute(
        "SELECT maturity, COUNT(*) as cnt FROM insights GROUP BY maturity"
    ).fetchall()
    conn.close()
    return {
        "total_insights": total_insights,
        "total_sessions": total_sessions,
        "by_type": {r["insight_type"]: r["cnt"] for r in by_type},
        "by_maturity": {r["maturity"]: r["cnt"] for r in by_maturity}
    }
