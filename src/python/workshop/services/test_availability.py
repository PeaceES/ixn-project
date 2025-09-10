from compat_sql_store import check_availability

print("Overlap (should be False):",
      check_availability("central-seminar-room-beta", "2025-09-08T16:30:00", "2025-09-08T16:45:00"))

print("Free slot (should be True):",
      check_availability("central-seminar-room-beta", "2025-09-08T22:00:00", "2025-09-08T23:00:00"))
