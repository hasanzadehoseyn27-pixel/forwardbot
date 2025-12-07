from aiogram import Router, types
from datetime import date
import re

from app.config import SETTINGS
from app.storage.posts import add_post, mark_sent_once
from app.storage.dests import list_destinations

router = Router()


# -------------------- استخراج شماره آگهی از متن -------------------- #

def extract_ad_number(text: str) -> int | None:
    """
    استخراج شماره آگهی از متن:
    مثل:
    🔖 آگهی شماره #22
    """
    if not text:
        return None

    match = re.search(r"#(\d+)", text)
    if match:
        return int(match.group(1))

    return None


# -------------------- ارسال فوری در حالت ارسال یکبار -------------------- #

async def send_once_immediately(bot, message_id: int):
    """
    اگر حالت ارسال یکبار فعال باشد → پیام جدید *بلافاصله* ارسال می‌شود.
    """
    dests = list_destinations()
    if not dests:
        print("[SOURCE] No destinations to send one-time message.")
        return

    for d in dests:
        try:
            await bot.copy_message(
                chat_id=d["chat_id"],
                from_chat_id=SETTINGS.SOURCE_CHANNEL_ID,
                message_id=message_id
            )
            print(f"[SOURCE] One-time sent → msg:{message_id} → {d['chat_id']}")
        except Exception as e:
            print(f"[SOURCE] ERROR sending → {e}")

    # علامت می‌زنیم این پیام یکبار ارسال شده
    mark_sent_once(message_id)


# -------------------- هندلر دریافت پست جدید کانال -------------------- #

@router.channel_post()
async def on_channel_post(message: types.Message):
    """
    وقتی پست جدیدی در کانال مبدا منتشر شود:
    1) شماره آگهی استخراج می‌شود
    2) پست ذخیره می‌شود
    3) اگر حالت ارسال یکبار فعال باشد → یکبار فوری ارسال می‌شود
    """

    if message.chat.id != SETTINGS.SOURCE_CHANNEL_ID:
        return

    msg_id = message.message_id
    today = date.today().isoformat()

    # استخراج شماره آگهی از متن
    ad_num = extract_ad_number(message.text or message.caption or "")

    add_post(
        message_id=msg_id,
        msg_date=today,
        ad_number=ad_num
    )

    print(f"[SOURCE] New post saved → {msg_id} (ad:{ad_num})")

    # اگر حالت ارسال یکبار فعال باشد → ارسال فوری
    if getattr(SETTINGS, "SEND_MODE", "repeat") == "once":
        await send_once_immediately(message.bot, msg_id)
