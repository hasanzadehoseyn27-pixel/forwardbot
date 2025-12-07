import asyncio
from datetime import date
from aiogram import Bot

from app.config import SETTINGS
from app.storage.posts import (
    list_all_posts,
    list_unsent_posts,
    toggle_sent
)
from app.storage.dests import list_destinations


# فاصله پیش‌فرض (۳۰ دقیقه)
INTERVAL = 60 * 30

# حالت ارسال (True = ارسال یکبار / False = ارسال دائمی)
SEND_ONCE_MODE = False


async def set_interval(seconds: int):
    """
    تنظیم فاصله زمانی توسط ادمین.
    """
    global INTERVAL
    INTERVAL = seconds
    print(f"[SCHEDULER] Interval updated → {seconds} seconds")


async def set_send_mode(once: bool):
    """
    تغییر حالت ارسال (دائمی / یکبار)
    """
    global SEND_ONCE_MODE
    SEND_ONCE_MODE = once
    print(f"[SCHEDULER] Send Mode updated → {'ONCE' if once else 'ALWAYS'}")


async def forward_post(bot: Bot, message_id: int, dest_id: int):
    """
    ارسال پست به صورت copy_message (نه forward)
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
    """
    print("[SCHEDULER] Scheduler started and running...")

    while True:
        try:
            # انتخاب لیست پست‌ها با توجه به حالت ارسال
            if SEND_ONCE_MODE:
                posts = list_unsent_posts()     # فقط پست‌هایی که هنوز ارسال نشده‌اند
            else:
                posts = list_all_posts()        # همه پست‌ها

            dests = list_destinations()         # مقصدها

            if not posts:
                print("[SCHEDULER] No posts to send.")
            elif not dests:
                print("[SCHEDULER] No destinations set.")
            else:
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

                    # اگر حالت یکبار فعال است → sent = True شود
                    if SEND_ONCE_MODE:
                        toggle_sent(msg_id)

                print("[SCHEDULER] Forward cycle completed.")

            # انتظار
            await asyncio.sleep(INTERVAL)

        except Exception as e:
            print(f"[SCHEDULER] LOOP ERROR: {e}")
            await asyncio.sleep(5)
