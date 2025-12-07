from aiogram import Router, types
from datetime import date

from app.config import SETTINGS
from app.storage.posts import add_post
from app.handlers.scheduler import SEND_ONCE_MODE, send_now

router = Router()


@router.channel_post()
async def on_channel_post(message: types.Message):
    """
    هر پست جدیدی که در کانال مبدا منتشر شود:
    1) ذخیره می‌شود
    2) اگر حالت یکبار فعال باشد → فوری ارسال می‌شود
    """
    if message.chat.id != SETTINGS.SOURCE_CHANNEL_ID:
        return

    msg_id = message.message_id
    today = date.today().isoformat()

    add_post(msg_id, today)

    print(f"[SOURCE] New post saved → {msg_id}")

    # 🚀 ارسال فوری در حالت یکبار
    if SEND_ONCE_MODE:
        await send_now(message.bot, msg_id)
