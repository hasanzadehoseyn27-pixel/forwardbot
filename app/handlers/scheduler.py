import asyncio
from aiogram import Bot

from app.config import SETTINGS
from app.storage.posts import list_today_posts, mark_sent_once
from app.storage.dests import list_destinations


# فاصله پیش‌فرض (۳۰ دقیقه)
INTERVAL = 60 * 30


async def set_interval(seconds: int):
    """
    تنظیم فاصله ارسال در حالت ارسال دائمی.
    """
    global INTERVAL
    INTERVAL = seconds
    print(f"[SCHEDULER] Interval updated → {seconds} seconds")


async def forward_post(bot: Bot, message_id: int, dest_id: int):
    """
    ارسال پست به صورت copy_message (نه forward).
    """
    try:
        await bot.copy_message(
            chat_id=dest_id,
            from_chat_id=SETTINGS.SOURCE_CHANNEL_ID,
            message_id=message_id
        )
        print(f"[SCHEDULER] Copied → msg:{message_id} → dest:{dest_id}")

    except Exception as e:
        print(f"[SCHEDULER] ERROR sending to {dest_id}: {e}")


async def start_scheduler(bot: Bot):
    """
    حلقه اصلی Scheduler.

    حالت‌ها:

    1) SEND_MODE == "once"
       → Scheduler هیچ کاری انجام نمی‌دهد
         (ارسال فوری در source.py انجام می‌شود)

    2) SEND_MODE == "repeat"
       → ارسال دوره‌ای بر اساس INTERVAL
    """

    print("[SCHEDULER] Scheduler started and running...")

    while True:
        try:
            # ========== حالت ارسال یک بار ==========
            if getattr(SETTINGS, "SEND_MODE", "repeat") == "once":
                print("[SCHEDULER] SEND_MODE=once → skip cycle")
                await asyncio.sleep(5)
                continue

            # ========== حالت ارسال دوره‌ای ==========
            posts = list_today_posts()
            dests = list_destinations()

            if not posts:
                print("[SCHEDULER] No posts for today.")
                await asyncio.sleep(INTERVAL)
                continue

            if not dests:
                print("[SCHEDULER] No destinations set.")
                await asyncio.sleep(INTERVAL)
                continue

            print(f"[SCHEDULER] Repeat sending {len(posts)} posts → {len(dests)} destinations")

            # ارسال پست‌ها
            for p in posts:
                if not p.get("active", True):
                    print(f"[SCHEDULER] Skip inactive post {p['message_id']}")
                    continue

                msg_id = p["message_id"]

                for d in dests:
                    await forward_post(bot, msg_id, d["chat_id"])

            print("[SCHEDULER] Repeat cycle completed.")

            await asyncio.sleep(INTERVAL)

        except Exception as e:
            print(f"[SCHEDULER] LOOP ERROR: {e}")
            await asyncio.sleep(5)
