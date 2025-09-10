import os, json, pyodbc
import uuid


CS = os.environ["SQL_CS"]

def _conn():
    return pyodbc.connect(CS)

def get_rooms():
    """Return {"rooms": [...]} exactly like the current code expects."""
    with _conn() as cn, cn.cursor() as cur:
        cur.execute("EXEC api.get_rooms_json")
        row = cur.fetchone()
        data = json.loads(row[0]) if row and row[0] else []
        return {"rooms": data}

def list_events(calendar_id: str):
    """Return {"events": [...]} for the given calendar_id (room code)."""
    with _conn() as cn, cn.cursor() as cur:
        cur.execute("EXEC api.get_events_json @calendar_id=?", calendar_id)
        row = cur.fetchone()
        data = json.loads(row[0]) if row and row[0] else []
        return {"events": data}


def create_event(ev: dict):
    """
    ev keys expected (same as your current JSON):
      id (guid string), calendar_id, title, start_time, end_time,
      organizer (email), description (optional), attendees (list of emails)
    Returns the created event object (dict).
    """
    with _conn() as cn, cn.cursor() as cur:
        cur.execute(
            "EXEC api.create_event_json "
            "@event_id=?, @calendar_id=?, @title=?, @start_utc=?, @end_utc=?, "
            "@organizer_email=?, @description=?, @attendees_json=?",
            ev["id"],
            ev["calendar_id"],
            ev["title"],
            ev["start_time"],   # ISO e.g. '2025-09-08T19:00:00'
            ev["end_time"],
            ev.get("organizer"),
            ev.get("description"),
            json.dumps(ev.get("attendees", [])),
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row and row[0] else None

def update_event(event_id: str, patch: dict, requester_email: str):
    """
    patch may include: title, start_time, end_time, description.
    requester_email must match the organizer.
    Returns the updated event (dict).
    """
    with _conn() as cn, cn.cursor() as cur:
        cur.execute(
            "EXEC api.update_event_json "
            "@event_id=?, @requester_email=?, @title=?, @start_utc=?, @end_utc=?, @description=?",
            event_id,
            requester_email,
            patch.get("title"),
            patch.get("start_time"),
            patch.get("end_time"),
            patch.get("description"),
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row and row[0] else None

def cancel_event(event_id: str, requester_email: str):
    """Cancel (soft delete) an event. Returns the updated event dict."""
    with _conn() as cn, cn.cursor() as cur:
        cur.execute(
            "EXEC api.cancel_event_json @event_id=?, @requester_email=?",
            event_id,
            requester_email,
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row and row[0] else None

def check_availability(calendar_id: str, start_iso: str, end_iso: str, exclude_event_id: str | None = None) -> bool:
    """Return True if the time window is free for this calendar (room)."""
    with _conn() as cn, cn.cursor() as cur:
        cur.execute(
            "EXEC api.check_availability @calendar_id=?, @start_utc=?, @end_utc=?, @exclude_event_id=?",
            calendar_id, start_iso, end_iso, exclude_event_id
        )
        (available,) = cur.fetchone()
        return bool(available)
