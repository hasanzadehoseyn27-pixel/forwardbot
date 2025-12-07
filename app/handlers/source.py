from aiogram import Router, types
from datetime import date
import re

from app.config import SETTINGS
from app.storage.posts import add_post, mark_sent_once, is_sent_once
from app.storage.dests import list_destinations

# حالت ارسال از فایل تنظیمات خوانده می‌شود
from settings_storage import get_send_mode

router = Router()


# ---------------------- استخراج شماره آگهی ---------------------- #

def extract_ad_number(text: str) -> int | None:
    """
    استخراج شماره آگهی از متن:
    الگو:  🔖 آگهی شماره #22
    """
    if not text:
        return None

    match = re.search(r"#(\d+)", text)
    if match:
        return int(match.group(1))

    return None


# ---------------------- ارسال فوری در حالت ارسال یکبار ---------------------- #

async def send_once_immediately(bot, message_id: int):
    """
    وقتی حالت ارسال one-time فعال باشد،
    پست جدید *فوری* بدون هیچ تأخیر ارسال می‌شود.
    """

    dests = list_destinations()
    if not dests:
        print("[SOURCE] No destinations → skip sending.")
        return

    for d in dests:
        try:
            await bot.copy_message(
                chat_id=d["chat_id"],
                from_chat_id=SETTINGS.SOURCE_CHANNEL_ID,
                message_id=message_id
            )
            print(f"[SOURCE] One-time SEND → msg:{message_id} → dest:{d['chat_id']}")
        except Exception as e:
            print(f"[SOURCE] ERROR sending to {d['chat_id']}: {e}")

    # علامت‌گذاری ارسال یکبار
    mark_sent_once(message_id)


# ---------------------- دریافت پست جدید از کانال منبع ---------------------- #

@router.channel_post()
async def on_channel_post(message: types.Message):
    """
    هر پست جدیدی که از کانال مبدا دریافت شود:
    1) شماره آگهی استخراج می‌شود
    2) پست در دیتابیس ذخیره می‌شود
    3) اگر حالت ارسال یکبار فعال باشد → همان لحظه ارسال می‌شود
    """

    if message.chat.id != SETTINGS.SOURCE_CHANNEL_ID:
        return

    msg_id = message.message_id
    today = date.today().isoformat()

    # استخراج شماره آگهی از متن یا کپشن
    ad_num = extract_ad_number(message.text or message.caption or "")

    # ذخیره پست
    add_post(
        message_id=msg_id,
        msg_date=today,
        ad_number=ad_num,
    )

    print(f"[SOURCE] New post saved → msg:{msg_id} | ad:{ad_num}")

    # ---------------------- حالت ارسال یکبار ---------------------- #
    mode = get_send_mode()

    if mode == "once":
        # جلوگیری از ارسال دوباره (در صورت شرایط نادر)
        if is_sent_once(msg_id):
            print(f"[SOURCE] Already sent_once, skipping msg:{msg_id}")
            return

        print("[SOURCE] SEND_MODE = once → sending immediately...")
        await send_once_immediately(message.bot, msg_id)
