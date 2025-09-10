from compat_sql_store import update_event, list_events

EVENT_ID = "2FF602E4-E6B3-40FF-87CF-83225C672E2C"  # your new Workshop Runthrough

print("Before:")
print(list_events("central-seminar-room-beta"))

upd = update_event(
    EVENT_ID,
    {
        "title": "Workshop Runthrough (rescheduled)",
        "start_time": "2025-09-08T20:00:00",
        "end_time":   "2025-09-08T21:00:00",
        "description": "Rescheduled by test_update.py",
    },
    requester_email="peaceselem@gmail.com",
)

print("Updated:")
print(upd)

print("After:")
print(list_events("central-seminar-room-beta"))
