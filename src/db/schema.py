import sqlite3
from src.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            requirements TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            topic TEXT NOT NULL,
            insight_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            main_idea TEXT DEFAULT '',
            core_approach TEXT DEFAULT '',
            strengths TEXT DEFAULT '[]',
            limitations TEXT DEFAULT '[]',
            gaps TEXT DEFAULT '[]',
            relevance TEXT DEFAULT '',
            maturity TEXT DEFAULT 'S1',
            source_url TEXT DEFAULT '',
            source_type TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS insights_fts USING fts5(
            title, content, main_idea, tags,
            content='insights',
            content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS insights_ai AFTER INSERT ON insights BEGIN
            INSERT INTO insights_fts(rowid, title, content, main_idea, tags)
            VALUES (new.id, new.title, new.content, new.main_idea, new.tags);
        END;

        CREATE TRIGGER IF NOT EXISTS insights_ad AFTER DELETE ON insights BEGIN
            INSERT INTO insights_fts(insights_fts, rowid, title, content, main_idea, tags)
            VALUES ('delete', old.id, old.title, old.content, old.main_idea, old.tags);
        END;

        CREATE TRIGGER IF NOT EXISTS insights_au AFTER UPDATE ON insights BEGIN
            INSERT INTO insights_fts(insights_fts, rowid, title, content, main_idea, tags)
            VALUES ('delete', old.id, old.title, old.content, old.main_idea, old.tags);
            INSERT INTO insights_fts(rowid, title, content, main_idea, tags)
            VALUES (new.id, new.title, new.content, new.main_idea, new.tags);
        END;
    """)
    conn.commit()
    conn.close()
