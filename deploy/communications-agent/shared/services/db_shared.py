# services/db_shared.py
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def _conn():
    """Create PostgreSQL connection."""
    return psycopg2.connect(os.environ["SQL_CS"])

def get_shared_thread():
    """Get shared thread from PostgreSQL database."""
    try:
        with _conn() as cn, cn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT calendar.get_shared_thread()")
            row = cur.fetchone()
            return row['get_shared_thread'] if row and row['get_shared_thread'] else {
                "thread_id": None, "updated_at_utc": None, "updated_by": None
            }
    except Exception as e:
        print(f"Error getting shared thread: {e}")
        return {
            "thread_id": None, "updated_at_utc": None, "updated_by": None
        }
