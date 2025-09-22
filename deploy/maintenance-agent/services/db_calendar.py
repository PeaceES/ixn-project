# services/db_calendar.py
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from dateutil import parser as dtp  # pip install python-dateutil

def _conn():
    cs = os.environ["SQL_CS"]  # must be exported in this terminal
    return psycopg2.connect(cs)

def get_rooms():
    """
    Returns the same shape your code expects from rooms.json:
    { "rooms": [ {id,name,location,room_type,capacity}, ... ] }
    """
    try:
        with _conn() as cn, cn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT calendar.get_rooms_json()")
            row = cur.fetchone()
            data = row['get_rooms_json'] if row and row['get_rooms_json'] else []
            return {"rooms": data}
    except Exception as e:
        print(f"Error getting rooms: {e}")
        return {"rooms": []}

def get_maintenance(room_code: str | None = None):
    # Note: list_maintenance_json not yet implemented in PostgreSQL
    # For now, return empty maintenance list
    try:
        # TODO: Implement calendar.list_maintenance_json function in PostgreSQL
        return {"maintenance": []}
    except Exception as e:
        print(f"Error getting maintenance: {e}")
        return {"maintenance": []}
    
    
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
    try:
        with _conn() as cn, cn.cursor(cursor_factory=RealDictCursor) as cur:
            # Use PostgreSQL function with uuid_generate_v4()
            cur.execute("""
                SELECT calendar.create_event_json(
                    uuid_generate_v4()::uuid,
                    %s::varchar,
                    %s::varchar,
                    %s::timestamp,
                    %s::timestamp,
                    'maintenance@system'::varchar,
                    %s::text,
                    '[]'::json
                )
            """, (room_code, title, start_sql, end_sql, description))
            row = cur.fetchone()
            return row['create_event_json'] if row and row['create_event_json'] else None
    except Exception as e:
        print(f"Error creating maintenance hold: {e}")
        return None


def cancel_maintenance_hold(event_id: str, requester_email: str = "maintenance@system"):
    """Cancel (soft-delete) a maintenance reservation by id."""
    try:
        with _conn() as cn, cn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT calendar.cancel_event_json(%s::uuid, %s::varchar)",
                (event_id, requester_email)
            )
            row = cur.fetchone()
            return row['cancel_event_json'] if row and row['cancel_event_json'] else None
    except Exception as e:
        print(f"Error canceling maintenance hold: {e}")
        return None
    

def set_room_status(room_code: str, status: str, updated_by: str = "maintenance@system", note: str | None = None):
    """
    status: 'faulty' or 'operational'
    Returns the updated room JSON from the proc.
    """
    # Note: set_room_status not yet implemented in PostgreSQL
    # For now, return None
    try:
        # TODO: Implement calendar.set_room_status function in PostgreSQL
        print(f"Warning: set_room_status not yet implemented for PostgreSQL")
        return None
    except Exception as e:
        print(f"Error setting room status: {e}")
        return None

