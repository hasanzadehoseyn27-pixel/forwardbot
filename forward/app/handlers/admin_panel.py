from aiogram import Router, types, F
from aiogram.filters import Command

from app.storage.dests import add_destination, remove_destination, list_destinations
from app.storage.admins import add_admin, remove_admin, list_admins, is_admin as check_admin
from app.storage.posts import list_today_posts, set_post_active
from app.handlers.scheduler import set_interval
from app.config import SETTINGS

router = Router()

# ------------------ ابزار ------------------ #

def is_admin(uid: int) -> bool:
    return check_admin(uid)


# ------------------ دکمه های پایین صفحه ------------------ #

def admin_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="📍 مدیریت مقصدها"),
                types.KeyboardButton(text="👤 مدیریت ادمین‌ها"),
            ],
            [
                types.KeyboardButton(text="⏱ تنظیم فاصله"),
                types.KeyboardButton(text="📋 پست‌های امروز"),
            ],
            [
                types.KeyboardButton(text="🔙 خروج"),
            ]
        ],
        resize_keyboard=True
    )


# ------------------ ورود به پنل ------------------ #

@router.message(Command("admin"))
async def open_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")

    await message.answer(
        "🔧 پنل مدیریت ربات فعال شد.",
        reply_markup=admin_keyboard()
    )


# ============================================================
# 📍 مدیریت مقصدها
# ============================================================

@router.message(F.text == "📍 مدیریت مقصدها")
async def manage_dest(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "➕ برای افزودن مقصد یک پیام از گروه/کانال مقصد فوروارد کنید.\n"
        "🗑 برای حذف مقصد، chat_id را بفرستید.\n"
        "📋 برای نمایش مقصدها: «📋 لیست مقصدها»",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton("➕ افزودن مقصد")],
                [types.KeyboardButton("🗑 حذف مقصد")],
                [types.KeyboardButton("📋 لیست مقصدها")],
                [types.KeyboardButton("🔙 بازگشت")],
            ],
            resize_keyboard=True
        )
    )


@router.message(F.text == "➕ افزودن مقصد")
async def add_dest_prompt(message: types.Message):
    await message.answer("یک پیام از مقصد *فوروارد کنید*.")


@router.message(F.forward_from_chat)
async def add_dest(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    chat = message.forward_from_chat
    ok = add_destination(chat.id, chat.title or chat.full_name or "")
    await message.answer("✅ اضافه شد." if ok else "ℹ️ قبلاً وجود داشت.")


@router.message(F.text == "🗑 حذف مقصد")
async def del_dest_prompt(message: types.Message):
    await message.answer("chat_id مقصد را ارسال کنید.")


@router.message(F.text.regexp(r"^-?\d+$"))
async def del_dest(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    ok = remove_destination(int(message.text))
    await message.answer("🗑 حذف شد." if ok else "❗ یافت نشد.")


@router.message(F.text == "📋 لیست مقصدها")
async def dest_list(message: types.Message):
    dests = list_destinations()
    if not dests:
        return await message.answer("❗ هیچ مقصدی وجود ندارد.")

    text = "📍 **مقصدها:**\n\n"
    for d in dests:
        text += f"- `{d['chat_id']}` — {d.get('title','')}\n"

    await message.answer(text, parse_mode="Markdown")


# ============================================================
# 👤 مدیریت ادمین‌ها
# ============================================================

@router.message(F.text == "👤 مدیریت ادمین‌ها")
async def manage_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "روش‌های افزودن ادمین:\n"
        "1️⃣ فوروارد پیام کاربر\n"
        "2️⃣ ارسال @username\n"
        "3️⃣ chat_id عددی\n\n"
        "برای حذف نیز chat_id را بفرستید.",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton("➕ افزودن ادمین")],
                [types.KeyboardButton("🗑 حذف ادمین")],
                [types.KeyboardButton("📋 لیست ادمین‌ها")],
                [types.KeyboardButton("🔙 بازگشت")],
            ],
            resize_keyboard=True
        )
    )


@router.message(F.text == "➕ افزودن ادمین")
async def add_admin_prompt(message: types.Message):
    await message.answer("یک پیام فوروارد کنید یا @username یا chat_id ارسال کنید.")


@router.message(F.forward_from)
async def add_admin_forward(message: types.Message):
    uid = message.forward_from.id
    ok = add_admin(uid)
    await message.answer("✅ افزوده شد." if ok else "ℹ️ قبلاً وجود داشت.")


@router.message(F.text.regexp(r"@([A-Za-z0-9_]{5,})"))
async def add_admin_username(message: types.Message):
    try:
        username = message.text.replace("@", "")
        chat = await message.bot.get_chat(username)
        uid = chat.id
        ok = add_admin(uid)
        await message.answer("✅ افزوده شد." if ok else "ℹ️ از قبل وجود داشت.")
    except:
        await message.answer("❗ کاربر یافت نشد.")


@router.message(F.text.regexp(r"^-?\d+$"))
async def add_admin_id(message: types.Message):
    uid = int(message.text)
    ok = add_admin(uid)
    await message.answer("✅ افزوده شد." if ok else "ℹ️ از قبل وجود داشت.")


@router.message(F.text == "🗑 حذف ادمین")
async def del_admin_prompt(message: types.Message):
    await message.answer("chat_id ادمین را ارسال کنید.")


@router.message(F.text.regexp(r"^-?\d+$"))
async def del_admin(message: types.Message):
    uid = int(message.text)
    ok = remove_admin(uid)
    await message.answer("🗑 حذف شد." if ok else "❗ یافت نشد / Owner حذف نمی‌شود.")


@router.message(F.text == "📋 لیست ادمین‌ها")
async def list_admin_list(message: types.Message):
    admins = list_admins()

    text = "👤 **ادمین‌ها:**\n"
    for uid in admins:
        text += f"- `{uid}`\n"

    await message.answer(text, parse_mode="Markdown")


# ============================================================
# ⏱ فاصله زمانی
# ============================================================

@router.message(F.text == "⏱ تنظیم فاصله")
async def interval_prompt(message: types.Message):
    await message.answer("⏱ مقدار فاصله را وارد کنید (مثال: `5m`, `2h`, `10`)", parse_mode="Markdown")


@router.message(F.text.regexp(r"^\d+[mh]?$"))
async def interval_set_value(message: types.Message):
    raw = message.text.lower()

    if raw.isdigit():
        seconds = int(raw) * 60
    elif raw.endswith("m"):
        seconds = int(raw[:-1]) * 60
    elif raw.endswith("h"):
        seconds = int(raw[:-1]) * 3600
    else:
        return await message.answer("❗فرمت اشتباه.")

    await set_interval(seconds)
    await message.answer(f"⏱ فاصله تنظیم شد: {seconds} ثانیه")


# ============================================================
# 📋 پست‌های امروز
# ============================================================

@router.message(F.text == "📋 پست‌های امروز")
async def today_posts(message: types.Message):
    posts = list_today_posts()
    if not posts:
        return await message.answer("📭 هیچ پستی نیست.")

    text = "📋 **پست‌های امروز:**\n"
    for p in posts:
        status = "🔔 فعال" if p["active"] else "❌ غیرفعال"
        text += f"- `{p['message_id']}` → {status}\n"

    await message.answer(text, parse_mode="Markdown")


# ============================================================
# 🔙 بازگشت
# ============================================================

@router.message(F.text == "🔙 بازگشت")
async def back_main(message: types.Message):
    await message.answer("🔧 بازگشت به منوی اصلی", reply_markup=admin_keyboard())
