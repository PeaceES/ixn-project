# services/db_calendar.py
import os, json, pyodbc
from datetime import datetime, timezone
from dateutil import parser as dtp  # pip install python-dateutil

def _conn():
    cs = os.environ["SQL_CS"]  # must be exported in this terminal
    return pyodbc.connect(cs)

def get_rooms():
    """
    Returns the same shape your code expects from rooms.json:
    { "rooms": [ {id,name,location,room_type,capacity}, ... ] }
    """
    with _conn() as cn, cn.cursor() as cur:
        cur.execute("EXEC api.get_rooms_json")
        row = cur.fetchone()
        data = json.loads(row[0]) if row and row[0] else []
        return {"rooms": data}

def get_maintenance(room_code: str | None = None):
    with _conn() as cn, cn.cursor() as cur:
        if room_code:
            cur.execute("EXEC api.list_maintenance_json @room_code=?", (room_code,))
        else:
            cur.execute("EXEC api.list_maintenance_json")
        row = cur.fetchone()
        data = json.loads(row[0]) if row and row[0] else []
        return {"maintenance": data}
    
    
def _iso_to_sql_dt(s: str | datetime) -> str:
    if isinstance(s, datetime):
        d = s.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        d = dtp.isoparse(s).astimezone(timezone.utc).replace(tzinfo=None)
    return d.strftime("%Y-%m-%dT%H:%M:%S")  # DATETIME2 format (no 'Z')


def create_maintenance_hold(room_code: str, start_iso, end_iso,
                            title="Maintenance: block", description=""):
    """Create a maintenance reservation. Returns JSON from the proc."""
    start_sql = _iso_to_sql_dt(start_iso)
    end_sql   = _iso_to_sql_dt(end_iso)
    with _conn() as cn, cn.cursor() as cur:
        # Let SQL generate/validate; pass empty attendees list
        cur.execute("""
            DECLARE @eid UNIQUEIDENTIFIER = NEWID();
            EXEC api.create_event_json
              @event_id        = @eid,
              @calendar_id     = ?,
              @title           = ?,
              @start_utc       = ?,
              @end_utc         = ?,
              @organizer_email = N'maintenance@system',
              @description     = ?,
              @attendees_json  = N'[]';
        """, (room_code, title, start_sql, end_sql, description))
        row = cur.fetchone()
        return json.loads(row[0]) if row and row[0] else None


def cancel_maintenance_hold(event_id: str, requester_email: str = "maintenance@system"):
    """Cancel (soft-delete) a maintenance reservation by id."""
    with _conn() as cn, cn.cursor() as cur:
        cur.execute(
            "EXEC api.cancel_event_json @event_id=?, @requester_email=?",
            (event_id, requester_email)
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row and row[0] else None
    

def set_room_status(room_code: str, status: str, updated_by: str = "maintenance@system", note: str | None = None):
    """
    status: 'faulty' or 'operational'
    Returns the updated room JSON from the proc.
    """
    with _conn() as cn, cn.cursor() as cur:
        cur.execute(
            "EXEC api.set_room_status @room_code=?, @status=?, @updated_by=?, @note=?",
            (room_code, status, updated_by, note)
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row and row[0] else None

