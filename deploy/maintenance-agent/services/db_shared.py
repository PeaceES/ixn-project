import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor


def _conn():
    cs = os.environ["SQL_CS"]  # will raise KeyError if not set
    return psycopg2.connect(cs)

def get_shared_thread():
    """Return {'thread_id': str|None, 'updated_at_utc': str|None, 'updated_by': str|None}."""
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
