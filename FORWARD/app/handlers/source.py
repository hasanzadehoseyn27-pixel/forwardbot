from aiogram import Router, types
from datetime import date

from app.config import SETTINGS
from app.storage.posts import add_post
import app.handlers.scheduler as sched   # ⬅ درست شد

router = Router()


@router.channel_post()
async def on_channel_post(message: types.Message):

    if message.chat.id != SETTINGS.SOURCE_CHANNEL_ID:
        return

    msg_id = message.message_id
    today = date.today().isoformat()

    add_post(msg_id, today)
    print(f"[SOURCE] New post saved → {msg_id}")

    # ارسال فوری فقط وقتی حالت یکبار فعال باشد
    if sched.SEND_ONCE_MODE:
        print("[SOURCE] Sending immediately...")
        await sched.send_now(message.bot, msg_id)
