import asyncio
from aiogram import Bot
from app.config import SETTINGS
from app.storage.posts import (
    list_all_posts,
    list_unsent_posts,
    toggle_sent
)
from app.storage.dests import list_destinations

INTERVAL = 60 * 30
SEND_ONCE_MODE = False


async def set_interval(seconds: int):
    global INTERVAL
    INTERVAL = seconds
    print(f"[SCHEDULER] Interval updated → {seconds} seconds")


async def set_send_mode(once: bool):
    global SEND_ONCE_MODE
    SEND_ONCE_MODE = once
    print(f"[SCHEDULER] MODE = {'ONCE' if once else 'ALWAYS'}")


async def forward_post(bot: Bot, message_id: int, dest_id: int):
    try:
        await bot.copy_message(
            chat_id=dest_id,
            from_chat_id=SETTINGS.SOURCE_CHANNEL_ID,
            message_id=message_id
        )
        print(f"[SCHEDULER] Sent → msg:{message_id} → {dest_id}")
    except Exception as e:
        print(f"[SCHEDULER] ERROR → {e}")


async def send_now(bot: Bot, message_id: int):
    print(f"[SCHEDULER] Immediate send triggered for msg:{message_id}")

    dests = list_destinations()
    if not dests:
        print("[SCHEDULER] No destinations.")
        return

    for d in dests:
        await forward_post(bot, message_id, d["chat_id"])

    toggle_sent(message_id)


async def start_scheduler(bot: Bot):
    print("[SCHEDULER] Scheduler running...")

    while True:
        try:
            # حالت ارسال یکبار → فقط پست‌های unsent
            if SEND_ONCE_MODE:
                unsent = list_unsent_posts()
                if unsent:
                    print(f"[SCHEDULER] Sending UNSENT posts: {len(unsent)}")

                    for p in unsent:
                        msg_id = p["message_id"]
                        for d in list_destinations():
                            await forward_post(bot, msg_id, d["chat_id"])
                        toggle_sent(msg_id)

                await asyncio.sleep(2)
                continue

            # حالت دائمی
            posts = list_all_posts()
            dests = list_destinations()

            if posts and dests:
                print(f"[SCHEDULER] Periodic send: {len(posts)} posts")
                for p in posts:
                    if not p.get("active", True):
                        continue

                    msg_id = p["message_id"]
                    for d in dests:
                        await forward_post(bot, msg_id, d["chat_id"])

            await asyncio.sleep(INTERVAL)

        except Exception as e:
            print(f"[SCHEDULER] LOOP ERROR → {e}")
            await asyncio.sleep(5)
