"""
PostgreSQL Store Compatibility Layer
Provides the same interface as the original SQL Server version but uses PostgreSQL
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from typing import Optional, Dict, List, Any

# Get PostgreSQL connection string from environment
DATABASE_URL = os.environ.get("SQL_CS", os.environ.get("DATABASE_URL", ""))

# Fallback demo data for when database is unavailable
DEMO_USERS = [
    {
        'id': '650e8400-e29b-41d4-a716-446655440001',
        'email': 'john.doe@university.edu',
        'name': 'John Doe',
        'role_scope': 'student',
        'department_id': '550e8400-e29b-41d4-a716-446655440001'
    },
    {
        'id': '650e8400-e29b-41d4-a716-446655440002',
        'email': 'alice.chen@university.edu',
        'name': 'Alice Chen',
        'role_scope': 'student',
        'department_id': '550e8400-e29b-41d4-a716-446655440002'
    },
    {
        'id': '650e8400-e29b-41d4-a716-446655440003',
        'email': 'sarah.jones@university.edu',
        'name': 'Sarah Jones',
        'role_scope': 'student',
        'department_id': '550e8400-e29b-41d4-a716-446655440004'
    },
    {
        'id': '650e8400-e29b-41d4-a716-446655440004',
        'email': 'alex.brown@university.edu',
        'name': 'Alex Brown',
        'role_scope': 'student',
        'department_id': '550e8400-e29b-41d4-a716-446655440003'
    },
    {
        'id': '650e8400-e29b-41d4-a716-446655440005',
        'email': 'prof.johnson@university.edu',
        'name': 'Professor Johnson',
        'role_scope': 'faculty',
        'department_id': '550e8400-e29b-41d4-a716-446655440001'
    }
]

def _conn():
    """Create PostgreSQL connection"""
    if not DATABASE_URL:
        raise ValueError("No database connection string provided")
    return psycopg2.connect(DATABASE_URL)

def get_rooms() -> Dict[str, List[Dict]]:
    """Return {"rooms": [...]} exactly like the current code expects."""
    try:
        with _conn() as cn:
            with cn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT calendar.get_rooms_json()")
                row = cur.fetchone()
                data = row['get_rooms_json'] if row and row['get_rooms_json'] else []
                return {"rooms": data if data else []}
    except Exception as e:
        print(f"Database error in get_rooms: {e}")
        # Return demo rooms if database fails
        return {
            "rooms": [
                {
                    'id': 'central-meeting-room-alpha',
                    'name': 'Meeting Room Alpha',
                    'capacity': 10,
                    'room_type': 'meeting_room',
                    'location': 'Main Building, 2nd Floor',
                    'equipment': ['projector', 'whiteboard']
                },
                {
                    'id': 'central-meeting-room-beta',
                    'name': 'Meeting Room Beta',
                    'capacity': 8,
                    'room_type': 'meeting_room',
                    'location': 'Main Building, 2nd Floor',
                    'equipment': ['tv_screen', 'whiteboard']
                }
            ]
        }

def list_events(calendar_id: str) -> Dict[str, List[Dict]]:
    """Return {"events": [...]} for the given calendar_id (room code)."""
    try:
        with _conn() as cn:
            with cn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT calendar.get_events_json(%s)", (calendar_id,))
                row = cur.fetchone()
                data = row['get_events_json'] if row and row['get_events_json'] else []
                return {"events": data if data else []}
    except Exception as e:
        print(f"Database error in list_events: {e}")
        return {"events": []}

def create_event(ev: Dict) -> Optional[Dict]:
    """
    ev keys expected (same as your current JSON):
      id (guid string), calendar_id, title, start_time, end_time,
      organizer (email), description (optional), attendees (list of emails)
    Returns the created event object (dict).
    """
    try:
        with _conn() as cn:
            with cn.cursor(cursor_factory=RealDictCursor) as cur:
                # Generate UUID if not provided
                event_id = ev.get("id")
                if not event_id:
                    event_id = str(uuid.uuid4())
                else:
                    # Ensure it's a valid UUID format
                    try:
                        uuid.UUID(event_id)
                    except ValueError:
                        event_id = str(uuid.uuid4())
                
                cur.execute(
                    "SELECT calendar.create_event_json(%s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        event_id,
                        ev["calendar_id"],
                        ev["title"],
                        ev["start_time"],   # ISO e.g. '2025-09-08T19:00:00'
                        ev["end_time"],
                        ev.get("organizer", "system@university.edu"),
                        ev.get("description"),
                        json.dumps(ev.get("attendees", [])),
                    )
                )
                row = cur.fetchone()
                cn.commit()
                return row['create_event_json'] if row and row['create_event_json'] else None
    except Exception as e:
        print(f"Database error in create_event: {e}")
        # Return the event as created for demo purposes
        return ev

def update_event(event_id: str, patch: Dict, requester_email: str) -> Optional[Dict]:
    """
    patch may include: title, start_time, end_time, description.
    requester_email must match the organizer.
    Returns the updated event (dict).
    """
    try:
        with _conn() as cn:
            with cn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT calendar.update_event_json(%s, %s, %s, %s, %s, %s)",
                    (
                        event_id,
                        requester_email,
                        patch.get("title"),
                        patch.get("start_time"),
                        patch.get("end_time"),
                        patch.get("description"),
                    )
                )
                row = cur.fetchone()
                cn.commit()
                return row['update_event_json'] if row and row['update_event_json'] else None
    except Exception as e:
        print(f"Database error in update_event: {e}")
        return None

def cancel_event(event_id: str, requester_email: str) -> Optional[Dict]:
    """Cancel (soft delete) an event. Returns the updated event dict."""
    try:
        with _conn() as cn:
            with cn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT calendar.cancel_event_json(%s, %s)",
                    (event_id, requester_email)
                )
                row = cur.fetchone()
                cn.commit()
                return row['cancel_event_json'] if row and row['cancel_event_json'] else None
    except Exception as e:
        print(f"Database error in cancel_event: {e}")
        return None

def check_availability(calendar_id: str, start_iso: str, end_iso: str, exclude_event_id: Optional[str] = None) -> bool:
    """Return True if the time window is free for this calendar (room)."""
    try:
        with _conn() as cn:
            with cn.cursor() as cur:
                cur.execute(
                    "SELECT calendar.check_room_availability(%s, %s, %s, %s)",
                    (calendar_id, start_iso, end_iso, exclude_event_id)
                )
                result = cur.fetchone()
                return bool(result[0]) if result else False
    except Exception as e:
        print(f"Database error in check_availability: {e}")
        return True  # Assume available if database fails

def lookup_entity_emails(query: str) -> List[Dict]:
    """Return a list of entity matches [{'entity_type','entity_id','name','email','department_id'}, ...]."""
    try:
        with _conn() as cn:
            with cn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT calendar.lookup_entity_emails(%s)", (query,))
                row = cur.fetchone()
                return row['lookup_entity_emails'] if row and row['lookup_entity_emails'] else []
    except Exception as e:
        print(f"Database error in lookup_entity_emails: {e}")
        return []

def get_org_structure() -> Dict[str, Any]:
    """Get organization structure including departments, users, and groups."""
    try:
        with _conn() as cn:
            with cn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT calendar.get_org_structure()")
                row = cur.fetchone()
                return row['get_org_structure'] if row and row['get_org_structure'] else {
                    'departments': [],
                    'users': [],
                    'groups': []
                }
    except Exception as e:
        print(f"Database error in get_org_structure: {e}. Using demo data.")
        # Return demo data if database fails
        return {
            'departments': [
                {'id': '550e8400-e29b-41d4-a716-446655440001', 'name': 'Computer Science', 'code': 'CS'},
                {'id': '550e8400-e29b-41d4-a716-446655440002', 'name': 'Engineering', 'code': 'ENG'},
                {'id': '550e8400-e29b-41d4-a716-446655440003', 'name': 'Business', 'code': 'BUS'},
                {'id': '550e8400-e29b-41d4-a716-446655440004', 'name': 'Arts', 'code': 'ARTS'}
            ],
            'users': DEMO_USERS,
            'groups': [
                {'id': '750e8400-e29b-41d4-a716-446655440001', 'name': 'Engineering Society', 'code': 'eng-soc', 'group_type': 'society'},
                {'id': '750e8400-e29b-41d4-a716-446655440002', 'name': 'Computer Science Department', 'code': 'cs-dept', 'group_type': 'department'},
                {'id': '750e8400-e29b-41d4-a716-446655440003', 'name': 'Robotics Club', 'code': 'robotics', 'group_type': 'club'},
                {'id': '750e8400-e29b-41d4-a716-446655440004', 'name': 'Drama Club', 'code': 'drama', 'group_type': 'club'},
                {'id': '750e8400-e29b-41d4-a716-446655440005', 'name': 'Student Government', 'code': 'student-gov', 'group_type': 'society'}
            ]
        }

def get_user_by_id_or_email(identifier: str) -> Optional[Dict]:
    """Get user by ID or email."""
    try:
        with _conn() as cn:
            with cn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT calendar.get_user_by_id_or_email(%s)", (identifier,))
                row = cur.fetchone()
                return row['get_user_by_id_or_email'] if row and row['get_user_by_id_or_email'] else None
    except Exception as e:
        print(f"Database error in get_user_by_id_or_email: {e}. Using demo data.")
        # Search in demo users
        for user in DEMO_USERS:
            if user['id'] == identifier or user['email'] == identifier:
                return user
        return None


def get_shared_thread():
    """Return {'thread_id': str|None, 'updated_at_utc': str|None, 'updated_by': str|None}."""
    try:
        # PostgreSQL version
        if "postgresql" in os.getenv("SQL_CS", "").lower():
            with _conn() as cn, cn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT calendar.get_shared_thread()")
                row = cur.fetchone()
                return row['get_shared_thread'] if row and row['get_shared_thread'] else {
                    "thread_id": None, "updated_at_utc": None, "updated_by": None
                }
        else:
            # SQL Server version (for future compatibility)
            with _conn() as cn, cn.cursor() as cur:
                cur.execute("EXEC api.get_shared_thread")
                row = cur.fetchone()
                return json.loads(row[0]) if row and row[0] else {
                    "thread_id": None, "updated_at_utc": None, "updated_by": None
                }
    except Exception as e:
        print(f"Database error in get_shared_thread: {e}")
        return {"thread_id": None, "updated_at_utc": None, "updated_by": None}


def set_shared_thread(thread_id: str, updated_by: str | None = None):
    """Upsert the current shared thread id and return the saved value as dict."""
    try:
        # PostgreSQL version
        if "postgresql" in os.getenv("SQL_CS", "").lower():
            with _conn() as cn, cn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT calendar.set_shared_thread(%s, %s)", (thread_id, updated_by))
                row = cur.fetchone()
                result = row['set_shared_thread'] if row and row['set_shared_thread'] else {
                    "thread_id": thread_id, "updated_at_utc": None, "updated_by": updated_by
                }
                print(f"[compat_sql_store] Shared thread set: {thread_id} by {updated_by}")
                return result
        else:
            # SQL Server version (for future compatibility)
            with _conn() as cn, cn.cursor() as cur:
                cur.execute("EXEC api.set_shared_thread @thread_id=?, @updated_by=?", (thread_id, updated_by))
                row = cur.fetchone()
                result = json.loads(row[0]) if row and row[0] else {
                    "thread_id": thread_id, "updated_at_utc": None, "updated_by": updated_by
                }
                print(f"[compat_sql_store] Shared thread set: {thread_id} by {updated_by}")
                return result
    except Exception as e:
        print(f"Database error in set_shared_thread: {e}")
        return {"thread_id": thread_id, "updated_at_utc": None, "updated_by": updated_by}