# src/flierbuyer/db_ops.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parents[2] / "corsair_market.db"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_schema() -> None:
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            boat_id TEXT PRIMARY KEY,
            url TEXT UNIQUE,
            model TEXT NOT NULL,
            year INTEGER,
            location TEXT,
            price REAL,
            trailer TEXT,
            has_head TEXT,
            extended_tongue TEXT,
            features TEXT, -- JSON string
            special TEXT,
            first_seen DATE NOT NULL,
            last_updated DATE NOT NULL,
            source_site TEXT,
            status TEXT DEFAULT 'Active'
        )
        """
    )
    conn.commit()
    conn.close()



