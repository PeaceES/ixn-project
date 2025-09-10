from compat_sql_store import cancel_event, list_events

EVENT_ID = "2FF602E4-E6B3-40FF-87CF-83225C672E2C"  # your Workshop Runthrough (rescheduled)

print("Cancelling…")
print(cancel_event(EVENT_ID, "peaceselem@gmail.com"))

print("After:")
print(list_events("central-seminar-room-beta"))
