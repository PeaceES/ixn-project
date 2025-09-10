import uuid
from compat_sql_store import create_event, list_events

event = {
    "id": str(uuid.uuid4()),
    "calendar_id": "central-seminar-room-beta",
    "title": "Workshop Runthrough",
    "start_time": "2025-09-08T19:00:00",   # pick a free slot
    "end_time":   "2025-09-08T20:00:00",
    "organizer": "peaceselem@gmail.com",
    "description": "Created from test_create.py",
    "attendees": ["robotics-society-soc@example.edu"]
}

print("CREATED:", create_event(event))
print("EVENTS:", list_events("central-seminar-room-beta"))
