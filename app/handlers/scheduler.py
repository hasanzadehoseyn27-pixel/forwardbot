import asyncio
from aiogram import Bot

from app.config import SETTINGS
from app.storage.posts import list_today_posts
from app.storage.dests import list_destinations

# تنظیمات پایدار
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
            from_chat_id=SETTINGS.SOURCE_CHANNEL_ID,
            message_id=message_id
        )
        print(f"[SCHEDULER] Copied → msg:{message_id} → dest:{dest_id}")

    except Exception as e:
        print("COPY ERROR TYPE:", type(e))
        print(f"[SCHEDULER] ERROR → {e}")


# ---------------------- Scheduler اصلی ---------------------- #

async def start_scheduler(bot: Bot):
    """
    - حالت ارسال یکبار → هیچ ارسال دوره‌ای نکن
    - حالت ارسال دائمی → ارسال دوره‌ای طبق interval
    """

    print("[SCHEDULER] Scheduler started and running...")

    while True:
        try:
            send_mode = get_send_mode()
            interval = get_interval()

            # حالت ارسال یکبار
            if send_mode == "once":
                await asyncio.sleep(5)
                continue

            # حالت ارسال دائمی
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
                f"[SCHEDULER] Sending {len(posts)} posts → {len(dests)} destinations "
                f"(interval={interval}s)"
            )

            for p in posts:
                if not p.get("active", True):
                    continue

                msg_id = p["message_id"]

                for d in dests:
                    await forward_post(bot, msg_id, d["chat_id"])

            print("[SCHEDULER] Cycle done.")
            await asyncio.sleep(interval)

        except Exception as e:
            print(f"[SCHEDULER] LOOP ERROR → {e}")
            await asyncio.sleep(5)
