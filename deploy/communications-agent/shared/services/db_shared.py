# services/db_shared.py
import os, json, pyodbc

def _conn():
    return pyodbc.connect(os.environ["SQL_CS"])

def get_shared_thread():
    with _conn() as cn, cn.cursor() as cur:
        cur.execute("EXEC api.get_shared_thread")
        row = cur.fetchone()
        return json.loads(row[0]) if row and row[0] else {
            "thread_id": None, "updated_at_utc": None, "updated_by": None
        }
