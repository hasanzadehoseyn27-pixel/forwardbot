from aiogram import Router, types, F
from aiogram.filters import Command

from app.config import SETTINGS
from app.storage.dests import add_destination, remove_destination, list_destinations
from app.storage.posts import list_today_posts
from app.handlers.scheduler import set_interval

router = Router()

# --------------------------------------------------------------------
#      ابزار: تشخیص ادمین فقط بر اساس OWNER_ID و ADMIN_IDS در env
# --------------------------------------------------------------------
def is_admin(user_id: int) -> bool:
    return (user_id == SETTINGS.OWNER_ID) or (user_id in SETTINGS.ADMIN_IDS)

# --------------------------------------------------------------------
#                      کیبوردهای پایین صفحه
# --------------------------------------------------------------------
def admin_keyboard() -> types.ReplyKeyboardMarkup:
    """
    منوی اصلی مدیریت که بعد از /start به ادمین نشان داده می‌شود
    """
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="📍 مدیریت مقصدها"),
                types.KeyboardButton(text="📋 پست‌های امروز"),
            ],
            [
                types.KeyboardButton(text="⏱ تنظیم فاصله"),
            ],
        ],
        resize_keyboard=True,
    )


def dests_keyboard() -> types.ReplyKeyboardMarkup:
    """
    زیرمنوی مدیریت مقصدها
    """
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="➕ افزودن مقصد")],
            [types.KeyboardButton(text="🗑 حذف مقصد")],
            [types.KeyboardButton(text="📋 لیست مقصدها")],
            [types.KeyboardButton(text="🔙 بازگشت")],
        ],
        resize_keyboard=True,
    )

# --------------------------------------------------------------------
#                      /admin (اختیاری)
# --------------------------------------------------------------------
@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")
    await message.answer("پنل مدیریت:", reply_markup=admin_keyboard())

# ====================================================================
# 📍 مدیریت مقصدها
# ====================================================================
@router.message(F.text == "📍 مدیریت مقصدها")
async def manage_dests_root(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📍 مدیریت مقصدها:\n"
        "➕ برای افزودن، روی «افزودن مقصد» بزن و سپس یک پیام از کانال/گروه مقصد را فوروارد کن.\n"
        "🗑 برای حذف، روی «حذف مقصد» بزن و chat_id مقصد را بفرست.\n"
        "📋 برای دیدن همه مقصدها، «لیست مقصدها» را بزن.",
        reply_markup=dests_keyboard(),
    )

# ---- افزودن مقصد ----
@router.message(F.text == "➕ افزودن مقصد")
async def add_dest_prompt(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "لطفاً *یک پیام* از کانال یا گروه مقصد را برای من *فوروارد* کن.\n"
        "ربات به‌صورت خودکار chat_id را تشخیص می‌دهد.",
        parse_mode="Markdown",
    )

@router.message(F.forward_from_chat)
async def add_dest_from_forward(message: types.Message):
    """
    هر پیام فورواردشده از کانال/گروه توسط ادمین → به‌عنوان مقصد ذخیره می‌شود.
    """
    if not is_admin(message.from_user.id):
        return

    chat = message.forward_from_chat
    chat_id = chat.id
    title = chat.title or getattr(chat, "full_name", "") or ""

    ok = add_destination(chat_id, title)

    if ok:
        await message.answer(f"✅ مقصد جدید اضافه شد:\n`{chat_id}` — {title}", parse_mode="Markdown")
    else:
        await message.answer("ℹ️ این مقصد قبلاً ثبت شده بود.")

# ---- حذف مقصد ----
@router.message(F.text == "🗑 حذف مقصد")
async def delete_dest_prompt(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "chat_id مقصدی که می‌خواهی حذف شود را بفرست.\n"
        "مثال: `-1001234567890`",
        parse_mode="Markdown",
    )

@router.message(F.text.regexp(r"^-?\d+$"))
async def delete_dest_by_id(message: types.Message):
    """
    هر عددی که ادمین بفرستد (بعد از زدن دکمه حذف مقصد) به‌عنوان chat_id حذف می‌شود.
    """
    if not is_admin(message.from_user.id):
        return

    chat_id = int(message.text)
    ok = remove_destination(chat_id)

    if ok:
        await message.answer("🗑 مقصد حذف شد.")
    else:
        await message.answer("❗ مقصدی با این آیدی پیدا نشد.")

# ---- لیست مقصدها ----
@router.message(F.text == "📋 لیست مقصدها")
async def list_dests(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    dests = list_destinations()
    if not dests:
        return await message.answer("❗ هنوز هیچ مقصدی ثبت نشده است.")

    lines = ["📍 مقصدهای فعلی:\n"]
    for d in dests:
        lines.append(f"- `{d['chat_id']}` — {d.get('title','')}")
    await message.answer("\n".join(lines), parse_mode="Markdown")

# ---- بازگشت به منوی اصلی ----
@router.message(F.text == "🔙 بازگشت")
async def back_to_main(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("بازگشت به منوی اصلی مدیریت:", reply_markup=admin_keyboard())

# ====================================================================
# ⏱ تنظیم فاصله ارسال خودکار
# ====================================================================
@router.message(F.text == "⏱ تنظیم فاصله")
async def interval_prompt(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "⏱ فاصله زمانی ارسال خودکار را وارد کن:\n\n"
        "- به دقیقه: `5m`, `30m`\n"
        "- به ساعت: `2h`, `12h`\n"
        "- فقط عدد (مثلاً `10`) = ۱۰ دقیقه\n\n"
        "حداقل ۱ دقیقه و سقف خاصی ندارد.",
        parse_mode="Markdown",
    )

@router.message(F.text.regexp(r"^\d+[mh]?$"))
async def interval_set(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    raw = message.text.lower().strip()

    if raw.isdigit():
        seconds = int(raw) * 60
    elif raw.endswith("m"):
        seconds = int(raw[:-1]) * 60
    elif raw.endswith("h"):
        seconds = int(raw[:-1]) * 3600
    else:
        return await message.answer("❗ فرمت اشتباه است.")

    await set_interval(seconds)
    await message.answer(f"⏱ فاصله زمانی روی {seconds} ثانیه تنظیم شد.")
# ====================================================================
# 📋 پست‌های امروز
# ===================================================================
@router.message(F.text == "📋 پست‌های امروز")
async def today_posts(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    posts = list_today_posts()
    if not posts:
        return await message.answer("📭 امروز هیچ پستی ثبت نشده است.")

    text = "📋 *پست‌های امروز:*\n\n"
    for p in posts:
        status = "🔔 فعال" if p["active"] else "❌ غیرفعال"
        text += f"- ID: `{p['message_id']}` → {status}\n"

    await message.answer(text, parse_mode="Markdown")
#شش