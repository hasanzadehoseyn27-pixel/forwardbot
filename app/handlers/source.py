from aiogram import Router, types, F
from datetime import date

from app.config import SETTINGS
from app.storage.posts import add_post, set_post_active, list_today_posts

router = Router()


# ------------------ دریافت پست جدید از کانال مبدا ------------------ #

@router.channel_post()
async def on_channel_post(message: types.Message):
    """
    وقتی پست جدید در کانال مبدا ارسال می‌شود:
    - ذخیره شود
    - دکمه فعال/غیرفعال زیر آن نمایش داده شود
    """
    if message.chat.id != SETTINGS.SOURCE_CHANNEL_ID:
        return

    msg_id = message.message_id
    today = date.today().isoformat()

    # ذخیره پست
    add_post(msg_id, today)

    # دکمه toggle
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🔔 فعال (ارسال می‌شود)",
                    callback_data=f"toggle:{msg_id}"
                )
            ]
        ]
    )

    await message.reply(
        "🔔 این پست فعال است و ارسال خواهد شد.",
        reply_markup=kb
    )

    print(f"[SOURCE] New post saved → {msg_id}")


# ------------------ تغییر وضعیت پست از داخل کانال ------------------ #

@router.callback_query(F.data.startswith("toggle:"))
async def toggle_status(call: types.CallbackQuery):
    """
    فعال/غیرفعال کردن پست از داخل کانال
    """

    msg_id = int(call.data.split(":")[1])

    posts = list_today_posts()
    target = None

    for p in posts:
        if p["message_id"] == msg_id:
            target = p
            break

    if not target:
        return await call.answer("❗ پست امروز یافت نشد.", show_alert=True)

    new_state = not target["active"]
    set_post_active(msg_id, new_state)

    if new_state:
        btn_text = "❌ غیرفعال کن"
        alert = "🔔 پست فعال شد."
    else:
        btn_text = "🔔 فعال کن"
        alert = "❌ پست غیرفعال شد."

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=btn_text,
                    callback_data=f"toggle:{msg_id}"
                )
            ]
        ]
    )

    try:
        await call.message.edit_reply_markup(reply_markup=kb)
    except:
        pass

    await call.answer(alert, show_alert=False)

    print(f"[SOURCE] Post {msg_id} updated → {new_state}")
