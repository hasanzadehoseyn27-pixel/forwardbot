from aiogram import Router, types
from datetime import date

from app.config import SETTINGS
from app.storage.posts import add_post

router = Router()


@router.channel_post()
async def on_channel_post(message: types.Message):
    """
    هر پست جدیدی که در کانال مبدا ارسال شود اینجا ذخیره می‌کنیم.
    هیچ پیام اضافه‌ای در کانال ارسال نمی‌کنیم.
    """
    if message.chat.id != SETTINGS.SOURCE_CHANNEL_ID:
        return

    msg_id = message.message_id
    today = date.today().isoformat()

    add_post(msg_id, today)

    print(f"[SOURCE] New post saved → {msg_id} ({today})")
