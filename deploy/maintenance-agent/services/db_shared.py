import os, json, pyodbc


def _conn():
    cs = os.environ["SQL_CS"]  # will raise KeyError if not set
    return pyodbc.connect(cs)

def get_shared_thread():
    """Return {'thread_id': str|None, 'updated_at_utc': str|None, 'updated_by': str|None}."""
    with _conn() as cn, cn.cursor() as cur:
        cur.execute("EXEC api.get_shared_thread")
        row = cur.fetchone()
        return json.loads(row[0]) if row and row[0] else {
            "thread_id": None, "updated_at_utc": None, "updated_by": None
        }
