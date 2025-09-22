# --- Room status ops (DB) -----------------------------------------------
import logging
from services.db_calendar import set_room_status   # we added this earlier

logger = logging.getLogger(__name__)

async def on_external_fault(room_code: str, summary: str = "fault reported"):
    """
    Called when the external service tells us a room is faulty.
    1) Persist status in SQL so schedulers won’t use the room.
    2) (Optional) Post to the shared thread, if you already have that function.
    """
    res = set_room_status(room_code, "faulty", "maintenance@system", summary[:200])
    logger.info(f"[Maintenance] Marked {room_code} as FAULTY in SQL: {res and res.get('status_note')}")
    # If you have a 'post_to_shared_thread' util, call it here:
    try:
        msg = f"🚧 Room **{room_code}** marked *faulty*: {summary}"
        # await post_to_shared_thread(msg)  # keep if you already have this
    except Exception as e:
        logger.warning(f"[Maintenance] Thread post failed: {e}")

async def on_external_resolve(room_code: str, note: str = "fault resolved"):
    """
    Called when the external service tells us the room is OK now.
    """
    res = set_room_status(room_code, "operational", "maintenance@system", note[:200])
    logger.info(f"[Maintenance] Marked {room_code} as OPERATIONAL in SQL: {res and res.get('status_note')}")
    try:
        msg = f"✅ Room **{room_code}** back to *operational*: {note}"
        # await post_to_shared_thread(msg)
    except Exception as e:
        logger.warning(f"[Maintenance] Thread post failed: {e}")
