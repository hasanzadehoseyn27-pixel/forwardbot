from aiogram import Router, types, F
from aiogram.filters import Command

from app.config import SETTINGS
from app.storage.dests import (
    add_destination,
    remove_destination,
    list_destinations,
)

from app.storage.posts import (
    list_today_posts,
    set_post_active
)

from app.handlers.scheduler import set_interval

router = Router()


# ---------------------- چک ادمین ---------------------- #

def is_admin(user_id: int) -> bool:
    return user_id == SETTINGS.OWNER_ID or user_id in SETTINGS.ADMIN_IDS


# ---------------------- منوی ادمین ---------------------- #

@router.message(Command("admin"))
async def admin_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="➕ افزودن مقصد")],
            [types.KeyboardButton(text="🗑 حذف مقصد")],
            [types.KeyboardButton(text="📋 لیست مقصدها")],
            [types.KeyboardButton(text="📋 پست‌های امروز")],
            [types.KeyboardButton(text="⏱ تنظیم فاصله")],
            [types.KeyboardButton(text="🔙 خروج")],
        ],
        resize_keyboard=True
    )

    await message.answer("پنل مدیریت:", reply_markup=kb)


# ---------------------- لیست مقصدها ---------------------- #

@router.message(F.text == "📋 لیست مقصدها")
async def admin_list(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی ندارید.")

    dests = list_destinations()
    if not dests:
        return await message.answer("❗ هیچ مقصدی ثبت نشده است.")

    lines = ["📍 مقصدهای ثبت‌شده:\n"]
    for d in dests:
        lines.append(f"- {d['chat_id']} — {d.get('title','')}")
    await message.answer("\n".join(lines))


# ---------------------- افزودن مقصد ---------------------- #

@router.message(F.text == "➕ افزودن مقصد")
async def start_add_dest(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی ندارید.")

    await message.answer(
        "لطفاً یک پیام از کانال/گروه مقصد را برای من *فوروارد* کنید.\n"
        "ربات به صورت خودکار chat_id مقصد را تشخیص می‌دهد."
    )


@router.message(F.forward_from_chat)
async def add_dest_from_forward(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    chat = message.forward_from_chat
    chat_id = chat.id
    title = chat.title or chat.full_name or ""

    ok = add_destination(chat_id, title)

    if ok:
        await message.answer(f"✅ مقصد اضافه شد:\n{chat_id} — {title}")
    else:
        await message.answer("ℹ️ این مقصد قبلاً ثبت شده بود.")


# ---------------------- حذف مقصد ---------------------- #

@router.message(F.text == "🗑 حذف مقصد")
async def prompt_delete_dest(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی ندارید.")

    await message.answer(
        "آیدی مقصد موردنظر را وارد کنید.\n"
        "مثال: -1001234567890"
    )


@router.message(F.text.regexp(r"^-?\d+$"))
async def delete_dest(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    chat_id = int(message.text)
    ok = remove_destination(chat_id)

    if ok:
        await message.answer("🗑 مقصد حذف شد.")
    else:
        await message.answer("❗ مقصد یافت نشد.")


# ---------------------- پست‌های امروز ---------------------- #

@router.message(F.text == "📋 پست‌های امروز")
async def show_today_posts(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی ندارید.")

    posts = list_today_posts()
    if not posts:
        return await message.answer("📭 امروز هیچ پستی دریافت نشده است.")

    text = "📋 **پست‌های امروز:**\n\n"
    for p in posts:
        status = "🔔 فعال" if p["active"] else "❌ غیرفعال"
        text += f"● ID: `{p['message_id']}` → {status}\n"

    await message.answer(text, parse_mode="Markdown")

    # ارسال دکمه برای هر پست
    for p in posts:
        msg_id = p["message_id"]
        state = p["active"]

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="❌ غیرفعال کن" if state else "🔔 فعال کن",
                        callback_data=f"toggle_admin:{msg_id}"
                    )
                ]
            ]
        )

        await message.answer(f"پست `{msg_id}`", reply_markup=kb, parse_mode="Markdown")


# ---------------------- تغییر وضعیت پست ---------------------- #

@router.callback_query(F.data.startswith("toggle_admin:"))
async def toggle_from_admin(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی ندارید.", show_alert=True)

    msg_id = int(call.data.split(":")[1])
    posts = list_today_posts()

    found = None
    for p in posts:
        if p["message_id"] == msg_id:
            found = p
            break

    if not found:
        return await call.answer("❗ پست یافت نشد.", show_alert=True)

    new_state = not found["active"]
    set_post_active(msg_id, new_state)

    await call.answer(
        "🔔 پست فعال شد." if new_state else "❌ پست غیرفعال شد."
    )

    # بروزرسانی دکمه
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="❌ غیرفعال کن" if new_state else "🔔 فعال کن",
                    callback_data=f"toggle_admin:{msg_id}"
                )
            ]
        ]
    )

    try:
        await call.message.edit_reply_markup(reply_markup=kb)
    except:
        pass


# ---------------------- تنظیم فاصله زمانی ---------------------- #

@router.message(F.text == "⏱ تنظیم فاصله")
async def set_interval_prompt(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")

    await message.answer(
        "**فاصله زمانی ارسال خودکار را وارد کنید:**\n\n"
        "- `5m`  → ۵ دقیقه\n"
        "- `30m` → ۳۰ دقیقه\n"
        "- `2h`  → ۲ ساعت\n"
        "- `10`  → ۱۰ دقیقه\n\n"
        "از ۱ دقیقه تا هرچقدر بخواهید پشتیبانی می‌شود.",
        parse_mode="Markdown"
    )


@router.message(F.text.regexp(r"^\d+[mh]?$"))
async def set_interval_value(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    raw = message.text.strip().lower()

    if raw.isdigit():
        seconds = int(raw) * 60

    elif raw.endswith("m"):
        minutes = int(raw[:-1])
        seconds = minutes * 60

    elif raw.endswith("h"):
        hours = int(raw[:-1])
        seconds = hours * 3600

    else:
        return await message.answer("❗ فرمت صحیح نیست.")

    await set_interval(seconds)
    await message.answer(f"⏱ فاصله زمانی تنظیم شد: {seconds} ثانیه")


# ---------------------- خروج ---------------------- #

@router.message(F.text == "🔙 خروج")
async def exit_admin(message: types.Message):
    await message.answer("خروج از پنل.", reply_markup=types.ReplyKeyboardRemove())
