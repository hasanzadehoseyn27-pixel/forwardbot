from aiogram import Router, types, F
from aiogram.filters import Command

from app.config import SETTINGS
from app.storage.dests import add_destination, remove_destination, list_destinations
from app.storage.posts import list_today_posts
from app.handlers.scheduler import set_interval

router = Router()


# --------------------------------------------------------------------
#               ابزار: تشخیص ادمین فقط از روی .env
# --------------------------------------------------------------------
def is_admin(user_id: int) -> bool:
    return (user_id == SETTINGS.OWNER_ID) or (user_id in SETTINGS.ADMIN_IDS)


# --------------------------------------------------------------------
#               کیبورد اصلی (Reply Keyboard)
# --------------------------------------------------------------------
def admin_keyboard() -> types.ReplyKeyboardMarkup:
    """
    منوی اصلی مدیریت که بعد از start به ادمین نشان داده می‌شود.
    """
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton("📍 مدیریت مقصدها"),
                types.KeyboardButton("📋 پست‌های امروز"),
            ],
            [
                types.KeyboardButton("⏱ تنظیم فاصله"),
            ],
        ],
        resize_keyboard=True,
    )


# --------------------------------------------------------------------
#               کیبورد مدیریت مقصدها
# --------------------------------------------------------------------
def dests_keyboard() -> types.ReplyKeyboardMarkup:
    """
    دکمه‌های پایین مدیریت مقصدها در یک ردیف + بازگشت تمام عرض
    """
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton("➕ افزودن مقصد"),
                types.KeyboardButton("🗑 حذف مقصد"),
                types.KeyboardButton("📋 لیست مقصدها"),
            ],
            [
                types.KeyboardButton("🔙 بازگشت")  # تمام عرض
            ]
        ],
        resize_keyboard=True,
    )


# --------------------------------------------------------------------
#                        /admin (ورود به پنل)
# --------------------------------------------------------------------
@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")

    return await message.answer(
        "🔧 پنل مدیریت ربات",
        reply_markup=admin_keyboard()
    )


# ====================================================================
# 📍 مدیریت مقصدها
# ====================================================================

@router.message(F.text == "📍 مدیریت مقصدها")
async def manage_dests_root(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    return await message.answer(
        "📍 مدیریت مقصدها:\n"
        "➕ افزودن: یک پیام از کانال/گروه مقصد را فوروارد کن (⚠️ ربات باید عضو آن گروه باشد)\n"
        "🗑 حذف: chat_id مقصد را بفرست\n"
        "📋 لیست: همه مقاصد ثبت‌شده را نشان می‌دهد",
        reply_markup=dests_keyboard(),
    )


# --------------------------------------------------------------------
# ➕ افزودن مقصد
# --------------------------------------------------------------------
@router.message(F.text == "➕ افزودن مقصد")
async def add_dest_prompt(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "یک پیام از کانال/گروه مقصد را برای من *فوروارد* کن.\n"
        "⚠️ ربات باید حداقل عضو گروه مقصد باشد.\n"
        "تلگرام فقط در این صورت chat_id واقعی را می‌فرستد.",
        parse_mode="Markdown",
    )


@router.message(F.forward_from_chat)
async def add_dest_from_forward(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    chat = message.forward_from_chat

    if chat is None:
        return await message.answer(
            "❗ تلگرام اطلاعات مقصد را ارسال نکرد.\n"
            "⚠️ ربات باید داخل گروه/کانال مقصد عضو باشد.",
            parse_mode="Markdown"
        )

    chat_id = chat.id
    title = chat.title or getattr(chat, "full_name", "") or ""

    ok = add_destination(chat_id, title)

    if ok:
        return await message.answer(
            f"✅ مقصد اضافه شد:\n`{chat_id}` — {title}",
            parse_mode="Markdown",
            reply_markup=dests_keyboard()
        )
    else:
        return await message.answer(
            "ℹ️ این مقصد قبلاً ثبت شده بود.",
            reply_markup=dests_keyboard()
        )


# --------------------------------------------------------------------
# 🗑 حذف مقصد
# --------------------------------------------------------------------
@router.message(F.text == "🗑 حذف مقصد")
async def delete_dest_prompt(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "chat_id مقصد را ارسال کنید:\nمثال:\n`-1001234567890`",
        parse_mode="Markdown"
    )


@router.message(F.text.regexp(r"^-?\d+$"))
async def delete_dest(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    chat_id = int(message.text)
    ok = remove_destination(chat_id)

    return await message.answer(
        "🗑 مقصد حذف شد." if ok else "❗ مقصدی با این آیدی یافت نشد.",
        reply_markup=dests_keyboard()
    )


# --------------------------------------------------------------------
# 📋 لیست مقصدها
# --------------------------------------------------------------------
@router.message(F.text == "📋 لیست مقصدها")
async def list_dests(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    dests = list_destinations()
    if not dests:
        return await message.answer("❗ هنوز مقصدی ثبت نشده است.", reply_markup=dests_keyboard())

    text = "📍 مقصدهای فعلی:\n\n"
    for d in dests:
        text += f"- `{d['chat_id']}` — {d.get('title','')}\n"

    return await message.answer(
        text, parse_mode="Markdown", reply_markup=dests_keyboard()
    )


# ====================================================================
# 📋 پست‌های امروز
# ====================================================================

@router.message(F.text == "📋 پست‌های امروز")
async def today_posts(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    posts = list_today_posts()

    if not posts:
        return await message.answer("📭 امروز هیچ پستی ثبت نشده است.")

    txt = "📋 *پست‌های امروز:*\n\n"
    for p in posts:
        active = "🔔" if p["active"] else "❌"
        txt += f"{active} ID: `{p['message_id']}`\n"

    return await message.answer(txt, parse_mode="Markdown", reply_markup=admin_keyboard())


# ====================================================================
# ⏱ تنظیم فاصله
# ====================================================================

@router.message(F.text == "⏱ تنظیم فاصله")
async def interval_prompt(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "⏱ مقدار فاصله را ارسال کن:\n"
        "`5m` → پنج دقیقه\n"
        "`2h` → دو ساعت\n"
        "`10` → ۱۰ دقیقه",
        parse_mode="Markdown"
    )


@router.message(F.text.regexp(r"^\d+[mh]?$"))
async def interval_set_value(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    raw = message.text.lower()

    if raw.isdigit():
        seconds = int(raw) * 60
    elif raw.endswith("m"):
        seconds = int(raw[:-1]) * 60
    elif raw.endswith("h"):
        seconds = int(raw[:-1]) * 3600
    else:
        return await message.answer("❗ فرمت درست نیست.")

    await set_interval(seconds)

    return await message.answer(
        f"⏱ فاصله روی {seconds} ثانیه تنظیم شد.",
        reply_markup=admin_keyboard()
    )


# ====================================================================
# 🔙 بازگشت
# ====================================================================

@router.message(F.text == "🔙 بازگشت")
async def back_main(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    return await message.answer("بازگشت به پنل مدیریت:", reply_markup=admin_keyboard())
