from aiogram import Router, types, F
from aiogram.filters import Command

from app.config import SETTINGS
from app.storage.dests import add_destination, remove_destination, list_destinations
from app.storage.posts import list_today_posts, set_post_active
from app.handlers.scheduler import set_interval

router = Router()

__all__ = ["router", "admin_keyboard", "is_admin"]


# ------------------ ابزار ادمین ------------------ #

def is_admin(uid: int) -> bool:
    """
    فقط از روی .env تصمیم می‌گیریم.
    - OWNER_ID
    - ADMIN_IDS (لیست عددی، جدا شده با کاما)
    """
    return uid == SETTINGS.OWNER_ID or uid in SETTINGS.ADMIN_IDS


def admin_keyboard() -> types.ReplyKeyboardMarkup:
    """
    کیبورد اصلی پنل مدیریت (بدون مدیریت ادمین‌ها)
    """
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="➕ افزودن مقصد"),
                types.KeyboardButton(text="🗑 حذف مقصد"),
            ],
            [
                types.KeyboardButton(text="📋 لیست مقصدها"),
            ],
            [
                types.KeyboardButton(text="📋 پست‌های امروز"),
                types.KeyboardButton(text="⏱ تنظیم فاصله"),
            ],
            [
                types.KeyboardButton(text="🔙 خروج"),
            ],
        ],
        resize_keyboard=True,
    )


# ------------------ ورود به پنل ------------------ #

@router.message(Command("admin"))
async def open_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ این ربات مخصوص مدیر است.")

    await message.answer(
        "🔧 پنل مدیریت ربات فعال شد.",
        reply_markup=admin_keyboard(),
    )


# ============================================================
# 📍 مقصدها
# ============================================================

@router.message(F.text == "➕ افزودن مقصد")
async def add_dest_prompt(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "یک پیام از کانال/گروه مقصد را برای من *فوروارد* کنید.\n"
        "chat_id مقصد به صورت خودکار تشخیص داده می‌شود.",
        parse_mode="Markdown",
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
        await message.answer(f"✅ مقصد اضافه شد:\n`{chat_id}` — {title}", parse_mode="Markdown")
    else:
        await message.answer("ℹ️ این مقصد قبلاً ثبت شده بود.")


@router.message(F.text == "🗑 حذف مقصد")
async def del_dest_prompt(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "chat_id مقصد را ارسال کنید (عدد منفی).\n"
        "مثال: `-1001234567890`",
        parse_mode="Markdown",
    )


@router.message(F.text.regexp(r"^-\d+$"))
async def del_dest(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    chat_id = int(message.text)
    ok = remove_destination(chat_id)
    await message.answer("🗑 مقصد حذف شد." if ok else "❗ مقصد یافت نشد.")


@router.message(F.text == "📋 لیست مقصدها")
async def dest_list(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    dests = list_destinations()
    if not dests:
        return await message.answer("❗ هنوز هیچ مقصدی ثبت نشده است.")

    text = "📍 **مقصدهای فعلی:**\n\n"
    for d in dests:
        text += f"- `{d['chat_id']}` — {d.get('title', '')}\n"

    await message.answer(text, parse_mode="Markdown")


# ============================================================
# ⏱ فاصله زمانی
# ============================================================

@router.message(F.text == "⏱ تنظیم فاصله")
async def interval_prompt(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "**فاصله زمانی ارسال خودکار را وارد کنید:**\n\n"
        "- `5m`  → ۵ دقیقه\n"
        "- `30m` → ۳۰ دقیقه\n"
        "- `2h`  → ۲ ساعت\n"
        "- `10`  → ۱۰ دقیقه (بدون پسوند = دقیقه)\n\n"
        "از ۱ دقیقه تا هرچقدر بخواهید پشتیبانی می‌شود.",
        parse_mode="Markdown",
    )


@router.message(F.text.regexp(r"^\d+[mh]?$"))
async def interval_set_value(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    raw = message.text.strip().lower()

    if raw.isdigit():
        seconds = int(raw) * 60
    elif raw.endswith("m"):
        seconds = int(raw[:-1]) * 60
    elif raw.endswith("h"):
        seconds = int(raw[:-1]) * 3600
    else:
        return await message.answer("❗ فرمت صحیح نیست.")

    await set_interval(seconds)
    await message.answer(f"⏱ فاصله زمانی تنظیم شد: {seconds} ثانیه")


# ============================================================
# 📋 پست‌های امروز + لینک کانال
# ============================================================

def _build_post_link(message_id: int) -> str:
    """
    تبدیل SOURCE_CHANNEL_ID به لینک t.me/c/...
    فقط روی سوپرگروه/کانال با chat_id منفی کار می‌کند.
    """
    cid = SETTINGS.SOURCE_CHANNEL_ID
    if cid < 0:
        internal = abs(cid)
        if internal > 1_000_000_000_000:
            internal -= 1_000_000_000_000
        return f"https://t.me/c/{internal}/{message_id}"
    # اگر کانال عمومی با username داشته باشی، می‌تونی اینجا هاردکد کنی
    return str(message_id)


@router.message(F.text == "📋 پست‌های امروز")
async def today_posts(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    posts = list_today_posts()
    if not posts:
        return await message.answer("📭 امروز هیچ پستی ثبت نشده است.")

    # برای هر پست یک پیام جدا با لینک و دکمه فعال/غیرفعال
    for p in posts:
        msg_id = p["message_id"]
        active = p["active"]

        status = "🔔 فعال" if active else "❌ غیرفعال"
        link = _build_post_link(msg_id)

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="❌ غیرفعال کن" if active else "🔔 فعال کن",
                        callback_data=f"toggle_admin:{msg_id}",
                    )
                ]
            ]
        )

        text = f"{status}  <a href='{link}'>پست {msg_id}</a>"
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("toggle_admin:"))
async def toggle_from_admin(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی ندارید.", show_alert=True)

    msg_id = int(call.data.split(":")[1])
    posts = list_today_posts()

    target = next((p for p in posts if p["message_id"] == msg_id), None)
    if not target:
        return await call.answer("❗ پست امروز یافت نشد.", show_alert=True)

    new_state = not target["active"]
    set_post_active(msg_id, new_state)

    await call.answer("🔔 پست فعال شد." if new_state else "❌ پست غیرفعال شد.")

    # آپدیت متن دکمه
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="❌ غیرفعال کن" if new_state else "🔔 فعال کن",
                    callback_data=f"toggle_admin:{msg_id}",
                )
            ]
        ]
    )

    try:
        await call.message.edit_reply_markup(reply_markup=kb)
    except:
        pass


# ============================================================
# 🔙 خروج
# ============================================================

@router.message(F.text == "🔙 خروج")
async def exit_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "خروج از پنل مدیر.",
        reply_markup=types.ReplyKeyboardRemove(),
    )
