import asyncio
from aiogram import Bot

from app.config import SETTINGS
from app.storage.posts import list_today_posts
from app.storage.dests import list_destinations

# تنظیمات پایدار از فایل settings_storage
from settings_storage import (
    get_send_mode,
    get_interval
)


# ---------------------- ارسال پست ---------------------- #

async def forward_post(bot: Bot, message_id: int, dest_id: int):
    """
    ارسال پست به صورت copy_message.
    """
    try:
        await bot.copy_message(
            chat_id=dest_id,
            from_chat_id=SETTINGS.SOURCE_CHANNEL_ID,  # ✔ کانال واقعی منبع
            message_id=message_id
        )
        print(f"[SCHEDULER] Copied → msg:{message_id} → dest:{dest_id}")

    except Exception as e:
        print(f"[SCHEDULER] ERROR sending to {dest_id}: {e}")


# ---------------------- Scheduler اصلی ---------------------- #

async def start_scheduler(bot: Bot):
    """
    Scheduler اصلی:

    - اگر send_mode = once → فقط منتظر می‌ماند (هیچ ارسال دوره‌ای انجام نمی‌دهد)
      چون ارسال فوری در source.py انجام می‌شود.

    - اگر send_mode = repeat → ارسال دوره‌ای طبق interval انجام می‌شود.
    """

    print("[SCHEDULER] Scheduler started and running...")

    while True:
        try:
            send_mode = get_send_mode()
            interval = get_interval()

            # ---------------------- حالت ارسال یکبار ---------------------- #
            if send_mode == "once":
                print("[SCHEDULER] SEND_MODE = once → skip sending.")
                await asyncio.sleep(5)
                continue

            # ---------------------- حالت ارسال دوره‌ای ---------------------- #
            posts = list_today_posts()
            dests = list_destinations()

            if not posts:
                print("[SCHEDULER] No posts for today.")
                await asyncio.sleep(interval)
                continue

            if not dests:
                print("[SCHEDULER] No destinations set.")
                await asyncio.sleep(interval)
                continue

            print(
                f"[SCHEDULER] Repeat sending {len(posts)} posts → {len(dests)} destinations "
                f"(interval={interval}s)"
            )

            for p in posts:
                if not p.get("active", True):
                    print(f"[SCHEDULER] Skip inactive post {p['message_id']}")
                    continue

                msg_id = p["message_id"]

                # ارسال پست به تمام مقصدها
                for d in dests:
                    await forward_post(bot, msg_id, d["chat_id"])

            print("[SCHEDULER] Repeat cycle completed.")

            # صبر طبق interval
            await asyncio.sleep(interval)

        except Exception as e:
            print(f"[SCHEDULER] LOOP ERROR: {e}")
            await asyncio.sleep(5)
