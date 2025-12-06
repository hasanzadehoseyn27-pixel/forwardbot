from aiogram import Router, types, F
from aiogram.filters import Command

from app.config import SETTINGS
from app.storage.dests import (
    add_destination,
    remove_destination,
    list_destinations,
)

from app.storage.admins import (
    add_admin,
    remove_admin,
    list_admins,
    is_admin as admin_check,
)

from app.storage.posts import (
    list_today_posts,
    set_post_active
)

from app.handlers.scheduler import set_interval


router = Router()


# ---------------------- ابزار ---------------------- #

def is_admin(uid: int) -> bool:
    return admin_check(uid)


# ---------------------- Reply Keyboard ---------------------- #

def admin_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📍 مدیریت مقصدها")],
            [types.KeyboardButton(text="👤 مدیریت ادمین‌ها")],
            [types.KeyboardButton(text="⏱ تنظیم فاصله")],
            [types.KeyboardButton(text="📋 پست‌های امروز")],
            [types.KeyboardButton(text="🔙 خروج")],
        ],
        resize_keyboard=True
    )


# ---------------------- ورود به پنل ---------------------- #

@router.message(Command("admin"))
async def admin_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")

    await message.answer(
        "🔧 **پنل مدیریت ربات**",
        reply_markup=admin_keyboard(),
        parse_mode="Markdown"
    )


# ============================================================
#  📍 مدیریت مقصدها
# ============================================================

@router.message(F.text == "📍 مدیریت مقصدها")
async def dests_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="➕ افزودن مقصد")],
            [types.KeyboardButton(text="🗑 حذف مقصد")],
            [types.KeyboardButton(text="📋 لیست مقصدها")],
            [types.KeyboardButton(text="🔙 بازگشت")],
        ],
        resize_keyboard=True,
    )

    await message.answer("📍 مدیریت مقصدها:", reply_markup=kb)


# --- افزودن مقصد --- #

@router.message(F.text == "➕ افزودن مقصد")
async def dest_add_prompt(message: types.Message):
    await message.answer("یک پیام از مقصد *فوروارد* کنید.")


@router.message(F.forward_from_chat)
async def dest_add_from_forward(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    chat = message.forward_from_chat
    ok = add_destination(chat.id, chat.title or chat.full_name or "")

    await message.answer(
        "✅ مقصد اضافه شد." if ok else "ℹ️ این مقصد قبلاً وجود دارد.",
        reply_markup=admin_keyboard()
    )


# --- حذف مقصد --- #

@router.message(F.text == "🗑 حذف مقصد")
async def dest_remove_prompt(message: types.Message):
    await message.answer("آیدی مقصد را وارد کنید:")


@router.message(F.text.regexp(r"^-?\d+$"))
async def dest_remove(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    chat_id = int(message.text)
    ok = remove_destination(chat_id)

    await message.answer(
        "🗑 حذف شد." if ok else "❗ یافت نشد.",
        reply_markup=admin_keyboard()
    )


# --- لیست مقصدها --- #

@router.message(F.text == "📋 لیست مقصدها")
async def dest_list(message: types.Message):
    dests = list_destinations()

    if not dests:
        return await message.answer("❗ هیچ مقصدی ثبت نشده.", reply_markup=admin_keyboard())

    text = "📍 **لیست مقصدها:**\n\n"
    for d in dests:
        text += f"- `{d['chat_id']}` — {d.get('title','')}\n"

    await message.answer(text, parse_mode="Markdown", reply_markup=admin_keyboard())


# ============================================================
#  👤 مدیریت ادمین‌ها
# ============================================================

@router.message(F.text == "👤 مدیریت ادمین‌ها")
async def admin_users_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="➕ افزودن ادمین")],
            [types.KeyboardButton(text="🗑 حذف ادمین")],
            [types.KeyboardButton(text="📋 لیست ادمین‌ها")],
            [types.KeyboardButton(text="🔙 بازگشت")],
        ],
        resize_keyboard=True,
    )

    await message.answer("👤 مدیریت ادمین‌ها:", reply_markup=kb)


# --- افزودن ادمین --- #

@router.message(F.text == "➕ افزودن ادمین")
async def admin_add_prompt(message: types.Message):
    await message.answer(
        "روش‌های افزودن ادمین:\n"
        "1️⃣ فوروارد پیام کاربر\n"
        "2️⃣ ارسال @username\n"
        "3️⃣ ارسال لینک t.me\n"
        "4️⃣ ارسال chat_id عددی",
        parse_mode="Markdown"
    )


# فوروارد
@router.message(F.forward_from)
async def admin_add_from_forward(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    uid = message.forward_from.id
    ok = add_admin(uid)
    await message.answer("✅ افزوده شد." if ok else "ℹ️ قبلاً ادمین بود.", reply_markup=admin_keyboard())


# username
@router.message(F.text.regexp(r"@([A-Za-z0-9_]{5,})"))
async def admin_add_from_username(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    username = message.text.replace("@", "")

    try:
        chat = await message.bot.get_chat(username)
        uid = chat.id
        ok = add_admin(uid)
        await message.answer("✅ افزوده شد." if ok else "ℹ️ قبلاً بود.", reply_markup=admin_keyboard())
    except:
        await message.answer("❗ کاربر یافت نشد.", reply_markup=admin_keyboard())


# chat_id
@router.message(F.text.regexp(r"^-?\d+$"))
async def admin_add_from_id(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    uid = int(message.text)
    ok = add_admin(uid)
    await message.answer("✅ افزوده شد." if ok else "ℹ️ قبلاً بود.", reply_markup=admin_keyboard())


# --- حذف ادمین --- #

@router.message(F.text == "🗑 حذف ادمین")
async def admin_del_prompt(message: types.Message):
    await message.answer("chat_id ادمین را ارسال کنید:")


@router.message(F.text.regexp(r"^-?\d+$"))
async def admin_del(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    uid = int(message.text)
    ok = remove_admin(uid)
    await message.answer(
        "🗑 حذف شد." if ok else "❗ یافت نشد / Owner حذف نمی‌شود.",
        reply_markup=admin_keyboard()
    )


# --- لیست ادمین‌ها --- #

@router.message(F.text == "📋 لیست ادمین‌ها")
async def admin_list_all(message: types.Message):
    admins = list_admins()
    text = "👤 **ادمین‌ها:**\n\n"
    for a in admins:
        text += f"- `{a}`\n"

    await message.answer(text, parse_mode="Markdown", reply_markup=admin_keyboard())


# ============================================================
#  ⏱ تنظیم فاصله زمانی
# ============================================================

@router.message(F.text == "⏱ تنظیم فاصله")
async def interval_prompt(message: types.Message):
    await message.answer(
        "⏱ فاصله را وارد کنید:\n"
        "`5m` , `30m` , `2h` , `10`",
        parse_mode="Markdown"
    )


@router.message(F.text.regexp(r"^\d+[mh]?$"))
async def interval_set(message: types.Message):
    raw = message.text.lower()

    if raw.isdigit():
        seconds = int(raw) * 60
    elif raw.endswith("m"):
        seconds = int(raw[:-1]) * 60
    elif raw.endswith("h"):
        seconds = int(raw[:-1]) * 3600
    else:
        return await message.answer("❗ فرمت اشتباه.")

    await set_interval(seconds)
    await message.answer(f"⏱ فاصله تنظیم شد: {seconds} ثانیه", reply_markup=admin_keyboard())


# ============================================================
#  📋 پست‌های امروز
# ============================================================

@router.message(F.text == "📋 پست‌های امروز")
async def posts_today(message: types.Message):
    posts = list_today_posts()

    if not posts:
        return await message.answer("📭 هیچ پستی ثبت نشده.", reply_markup=admin_keyboard())

    text = "📋 **پست‌های امروز:**\n\n"
    for p in posts:
        status = "🔔 فعال" if p["active"] else "❌ غیرفعال"
        text += f"- ID `{p['message_id']}` → {status}\n"

    await message.answer(text, parse_mode="Markdown", reply_markup=admin_keyboard())


# ============================================================
#  🔙 بازگشت
# ============================================================

@router.message(F.text == "🔙 بازگشت")
async def back_to_main(message: types.Message):
    await message.answer("🔧 پنل مدیریت ربات", reply_markup=admin_keyboard())
