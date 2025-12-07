import asyncio
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


# ================================
# 🚀 ارسال فوری برای حالت "یکبار"
# ================================
async def send_now(bot: Bot, message_id: int):
    """
    ارسال فوری پست وقتی حالت یک‌بار فعال است.
    """
    dests = list_destinations()
    if not dests:
        print("[SCHEDULER] No destinations for immediate send.")
        return

    print(f"[SCHEDULER] Immediate send for msg:{message_id}")

    for d in dests:
        await forward_post(bot, message_id, d["chat_id"])

    toggle_sent(message_id)


# ================================
# 🚀 Scheduler اصلی
# ================================

async def start_scheduler(bot: Bot):
    """
    Scheduler اصلی برای ارسال خودکار پیام‌ها.
    """
    print("[SCHEDULER] Scheduler started and running...")

    while True:
        try:
            # حالت "ارسال یکبار" → فقط پست‌های ارسال‌نشده قدیمی
            if SEND_ONCE_MODE:
                posts = list_unsent_posts()

                if posts:
                    print(f"[SCHEDULER] Sending {len(posts)} unsent posts...")
                    dests = list_destinations()

                    for p in posts:
                        msg_id = p["message_id"]

                        for d in dests:
                            await forward_post(bot, msg_id, d["chat_id"])

                        toggle_sent(msg_id)

                # حالت یک‌بار نیازی به interval ندارد → فقط منتظر پست جدید بماند
                await asyncio.sleep(3)
                continue

            # حالت دائمی → ارسال دوره‌ای
            posts = list_all_posts()
            dests = list_destinations()

            if not posts:
                print("[SCHEDULER] No posts to send.")
            elif not dests:
                print("[SCHEDULER] No destinations set.")
            else:
                print(f"[SCHEDULER] Sending {len(posts)} posts → {len(dests)} destinations")

                for p in posts:
                    if not p.get("active", True):
                        print(f"[SCHEDULER] Skip inactive post {p['message_id']}")
                        continue

                    msg_id = p["message_id"]

                    for d in dests:
                        await forward_post(bot, msg_id, d["chat_id"])

                print("[SCHEDULER] Forward cycle completed.")

            await asyncio.sleep(INTERVAL)

        except Exception as e:
            print(f"[SCHEDULER] LOOP ERROR: {e}")
            await asyncio.sleep(5)
