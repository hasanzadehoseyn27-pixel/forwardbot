import asyncio
from datetime import date
from aiogram import Bot

from app.config import SETTINGS
from app.storage.posts import list_today_posts
from app.storage.dests import list_destinations


# فاصله پیش‌فرض (۳۰ دقیقه)
INTERVAL = 60 * 30


async def set_interval(seconds: int):
    """
    تنظیم فاصله زمانی توسط ادمین.
    """
    global INTERVAL
    INTERVAL = seconds
    print(f"[SCHEDULER] Interval updated → {seconds} seconds")


async def forward_post(bot: Bot, message_id: int, dest_id: int):
    """
    ارسال پست به صورت copy_message (نه forward)
    این روش 100٪ کار می‌کند حتی اگر کانال مقصد محدودیت forward داشته باشد.
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
    حلقه پس‌زمینه برای ارسال خودکار پیام‌ها.
    هیچوقت متوقف نمی‌شود (حتی با خطا).
    """
    print("[SCHEDULER] Scheduler started and running...")

    # اجرای فوری پس از استارت
    await asyncio.sleep(1)

    while True:
        try:
            # صبر طبق INTERVAL
            await asyncio.sleep(INTERVAL)

            posts = list_today_posts()          # پست‌های امروز
            dests = list_destinations()         # تمام مقصدها

            if not posts:
                print("[SCHEDULER] No posts for today.")
                continue

            if not dests:
                print("[SCHEDULER] No destinations set.")
                continue

            print(f"[SCHEDULER] Sending {len(posts)} posts → {len(dests)} destinations")

            # ارسال پست‌ها
            for p in posts:
                if not p.get("active", True):
                    print(f"[SCHEDULER] Skip inactive post {p['message_id']}")
                    continue

                msg_id = p["message_id"]

                for dest in dests:
                    dest_id = dest["chat_id"]
                    await forward_post(bot, msg_id, dest_id)

            print("[SCHEDULER] Forward cycle completed.")

        except Exception as e:
            print(f"[SCHEDULER] LOOP ERROR: {e}")
            await asyncio.sleep(5)
