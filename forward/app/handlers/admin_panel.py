from aiogram import Router, types, F
from aiogram.filters import Command

from app.config import SETTINGS
from app.storage.dests import add_destination, remove_destination, list_destinations
from app.storage.posts import list_today_posts
from app.handlers.scheduler import set_interval

router = Router()


# ================================================================
#   ابزار: تشخیص ادمین فقط از روی .env
# ================================================================
def is_admin(user_id: int) -> bool:
    return (user_id == SETTINGS.OWNER_ID) or (user_id in SETTINGS.ADMIN_IDS)


# ================================================================
#   کیبوردهای منو
# ================================================================
def admin_keyboard() -> types.ReplyKeyboardMarkup:
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
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="➕ افزودن مقصد"),
                types.KeyboardButton(text="🗑 حذف مقصد"),
                types.KeyboardButton(text="📋 لیست مقصدها"),
            ],
            [
                types.KeyboardButton(text="🔙 بازگشت")
            ]
        ],
        resize_keyboard=True,
    )


# ================================================================
#   /admin → ورود به پنل
# ================================================================
@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")
    return await message.answer("🔧 پنل مدیریت ربات", reply_markup=admin_keyboard())


# ================================================================
# 📍 مدیریت مقصدها
# ================================================================
@router.message(F.text.contains("مدیریت مقصد"))
async def manage_dests(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    return await message.answer(
        "📍 مدیریت مقصدها:\n\n"
        "➕ افزودن مقصد: آیدی گروه یا لینک گروه را ارسال کنید.\n"
        "نمونه:\n"
        "`-1001234567890`\n"
        "`t.me/groupname`\n\n"
        "🗑 حذف مقصد: فقط chat_id را بزن.\n"
        "📋 لیست مقصدها: نمایش همه مقصدها\n",
        parse_mode="Markdown",
        reply_markup=dests_keyboard()
    )


# ================================================================
# ➕ افزودن مقصد (بدون فوروارد)
# ================================================================
def extract_chat_id_from_text(text: str):
    text = text.strip()

    # اگر مستقیم chat_id است
    if text.startswith("-") and text[1:].isdigit():
        return int(text), None

    # اگر لینک t.me است
    if "t.me/" in text:
        username = text.split("t.me/")[1]
        username = username.replace("https://", "").replace("http://", "")
        username = username.split("/")[0]
        return None, username

    return None, None


@router.message(F.text.contains("افزودن مقصد"))
async def add_dest_prompt(message: types.Message):
    return await message.answer(
        "chat_id یا لینک گروه را ارسال کنید:\n\n"
        "`-100xxxxxxx`\n"
        "`t.me/groupname`",
        parse_mode="Markdown"
    )


@router.message(
    F.text.regexp(r".+")
    & ~F.text.contains("حذف مقصد")
    & ~F.text.contains("لیست مقصدها")
    & ~F.text.contains("بازگشت")
    & ~F.text.contains("پست")
    & ~F.text.contains("فاصله")
)
async def add_dest_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    raw = message.text.strip()
    chat_id, username = extract_chat_id_from_text(raw)

    # حالت chat_id مستقیم
    if chat_id:
        ok = add_destination(chat_id, "")
        return await message.answer(
            "✅ مقصد اضافه شد." if ok else "ℹ️ مقصد از قبل وجود داشت.",
            reply_markup=dests_keyboard()
        )

    # حالت username
    if username:
        try:
            chat = await message.bot.get_chat(username)
            cid = chat.id
            title = chat.title or getattr(chat, "full_name", "")
            ok = add_destination(cid, title)

            return await message.answer(
                f"✅ مقصد اضافه شد:\n`{cid}` — {title}",
                parse_mode="Markdown",
                reply_markup=dests_keyboard()
            )
        except Exception as e:
            return await message.answer(
                f"❗ خطا در گرفتن اطلاعات گروه.\n{e}",
                reply_markup=dests_keyboard()
            )

    return await message.answer("❗ ورودی معتبر نیست.", reply_markup=dests_keyboard())


# ================================================================
# 🗑 حذف مقصد
# ================================================================
@router.message(F.text.contains("حذف مقصد"))
async def delete_dest_prompt(message: types.Message):
    return await message.answer(
        "chat_id مقصد را ارسال کنید:\n`-100xxxxxxxx`",
        parse_mode="Markdown"
    )


@router.message(F.text.regexp(r"^-?\d+$"))
async def delete_dest(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    chat_id = int(message.text)
    ok = remove_destination(chat_id)

    return await message.answer(
        "🗑 مقصد حذف شد." if ok else "❗ مقصدی با این آیدی وجود ندارد.",
        reply_markup=dests_keyboard()
    )


# ================================================================
# 📋 لیست مقصدها
# ================================================================
@router.message(F.text.contains("لیست مقصد"))
async def list_destinations_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    dests = list_destinations()
    if not dests:
        return await message.answer("❗ هیچ مقصدی ثبت نشده است.", reply_markup=dests_keyboard())

    txt = "📍 مقصدهای ثبت‌شده:\n\n"
    for d in dests:
        txt += f"- `{d['chat_id']}` — {d.get('title','')}\n"

    return await message.answer(txt, parse_mode="Markdown", reply_markup=dests_keyboard())


# ================================================================
# 📋 پست‌های امروز
# ================================================================
@router.message(F.text.contains("پست‌های امروز"))
async def today_posts(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    posts = list_today_posts()
    if not posts:
        return await message.answer("📭 امروز هیچ پستی نیست.", reply_markup=admin_keyboard())

    txt = "📋 امروز:\n\n"
    for p in posts:
        active = "🔔" if p["active"] else "❌"
        txt += f"{active} ID: `{p['message_id']}`\n"

    return await message.answer(txt, parse_mode="Markdown", reply_markup=admin_keyboard())


# ================================================================
# ⏱ تنظیم فاصله
# ================================================================
@router.message(F.text.contains("فاصله"))
async def interval_prompt(message: types.Message):
    return await message.answer(
        "⏱ مقدار فاصله را بفرست:\n"
        "`5m` → پنج دقیقه\n"
        "`2h` → دو ساعت\n"
        "`10` → ده دقیقه",
        parse_mode="Markdown"
    )


@router.message(F.text.regexp(r"^\d+[mh]?$"))
async def interval_set(message: types.Message):
    raw = message.text.lower().strip()

    if raw.isdigit():
        seconds = int(raw) * 60
    elif raw.endswith("m"):
        seconds = int(raw[:-1]) * 60
    elif raw.endswith("h"):
        seconds = int(raw[:-1]) * 3600
    else:
        return await message.answer("❗ فرمت صحیح نیست.")

    await set_interval(seconds)

    return await message.answer(
        f"⏱ فاصله روی {seconds} ثانیه تنظیم شد.",
        reply_markup=admin_keyboard()
    )


# ================================================================
# 🔙 بازگشت
# ================================================================
@router.message(F.text.contains("بازگشت"))
async def back_main(message: types.Message):
    return await message.answer("بازگشت به پنل مدیریت:", reply_markup=admin_keyboard())
