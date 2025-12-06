from aiogram import Router, types, F
from aiogram.filters import Command

from app.config import SETTINGS
from app.storage.dests import add_destination, remove_destination, list_destinations
from app.storage.posts import list_today_posts
from app.handlers.scheduler import set_interval

router = Router()


# =====================================================
#   ابزار: تشخیص ادمین از روی ENV
# =====================================================
def is_admin(uid: int) -> bool:
    return uid == SETTINGS.OWNER_ID or uid in SETTINGS.ADMIN_IDS


# =====================================================
#   کیبوردها
# =====================================================
def admin_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="📍 مدیریت مقصدها"),
                types.KeyboardButton(text="📋 پست‌های امروز"),
            ],
            [
                types.KeyboardButton(text="⏱ تنظیم فاصله")
            ]
        ],
        resize_keyboard=True
    )


def dests_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="➕ افزودن مقصد"),
                types.KeyboardButton(text="🗑 حذف مقصد"),
                types.KeyboardButton(text="📋 لیست مقصدها")
            ],
            [
                types.KeyboardButton(text="🔙 بازگشت")
            ]
        ],
        resize_keyboard=True
    )


# حالت انتظار جهت افزودن مقصد
ADD_DEST_WAIT = set()


# =====================================================
#   /admin → ورود به پنل
# =====================================================
@router.message(Command("admin"))
async def admin_start(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")
    return await message.answer("🔧 پنل مدیریت ربات", reply_markup=admin_keyboard())


# =====================================================
#   📍 مدیریت مقصدها
# =====================================================
@router.message(F.text.contains("مدیریت مقصد"))
async def menu_dest(message: types.Message):
    return await message.answer(
        "📍 <b>مدیریت مقصدها</b>\n\n"
        "➕ افزودن مقصد → آیدی یا لینک گروه را بفرست\n"
        "🗑 حذف مقصد → فقط chat_id را بزن\n"
        "📋 لیست مقصدها → نمایش همه مقاصد\n",
        parse_mode="HTML",
        reply_markup=dests_keyboard()
    )


# =====================================================
#   ➕ افزودن مقصد
# =====================================================
def extract_chat(text: str):
    text = text.strip()

    # chat_id مستقیم
    if text.startswith("-100") and text[1:].isdigit():
        return int(text), None

    # username / لینک
    if "t.me/" in text:
        username = text.split("t.me/")[1]
        username = username.replace("https://", "").replace("http://", "")
        username = username.split("/")[0]
        return None, username

    return None, None


@router.message(F.text.contains("افزودن مقصد"))
async def ask_add_dest(message: types.Message):
    ADD_DEST_WAIT.add(message.from_user.id)
    return await message.answer(
        "chat_id یا لینک گروه را ارسال کنید:\n"
        "<code>-1001234567890</code>\n"
        "<code>t.me/groupname</code>",
        parse_mode="HTML"
    )


@router.message(F.text, F.from_user.id.func(lambda uid: uid in ADD_DEST_WAIT))
async def handle_add_dest(message: types.Message):
    uid = message.from_user.id
    raw = message.text.strip()
    chat_id, username = extract_chat(raw)

    ADD_DEST_WAIT.remove(uid)

    # chat_id مستقیم
    if chat_id:
        ok = add_destination(chat_id, "")
        return await message.answer(
            "✅ مقصد اضافه شد." if ok else "ℹ️ این مقصد قبلاً وجود داشت.",
            reply_markup=dests_keyboard()
        )

    # username / لینک
    if username:
        try:
            chat = await message.bot.get_chat(username)
            cid = chat.id
            title = chat.title or getattr(chat, "full_name", "")
            ok = add_destination(cid, title)

            return await message.answer(
                f"✅ مقصد اضافه شد:\n<code>{cid}</code> — {title}",
                parse_mode="HTML",
                reply_markup=dests_keyboard()
            )
        except Exception as e:
            return await message.answer(
                f"❗ خطا در گرفتن اطلاعات گروه.\n<code>{e}</code>",
                parse_mode="HTML",
                reply_markup=dests_keyboard()
            )

    return await message.answer("❗ ورودی معتبر نبود.", reply_markup=dests_keyboard())


# =====================================================
#   🗑 حذف مقصد
# =====================================================
@router.message(F.text.contains("حذف مقصد"))
async def ask_delete(message: types.Message):
    return await message.answer(
        "chat_id مقصد را بفرست:\n<code>-100xxxxxxxx</code>",
        parse_mode="HTML"
    )


@router.message(F.text.regexp(r"^-?\d+$"))
async def del_dest(message: types.Message):
    cid = int(message.text)
    ok = remove_destination(cid)
    return await message.answer(
        "🗑 حذف شد." if ok else "❗ مقصدی با این آیدی نبود.",
        reply_markup=dests_keyboard()
    )


# =====================================================
#   📋 لیست مقصدها (با لینک قابل کلیک)
# =====================================================
@router.message(F.text.contains("لیست مقصد"))
async def list_dest(message: types.Message):
    dests = list_destinations()
    if not dests:
        return await message.answer("❗ هیچ مقصدی وجود ندارد.", reply_markup=dests_keyboard())

    txt = "<b>📍 لیست مقصدها</b>\n\n"

    for d in dests:
        cid = d["chat_id"]
        title = d.get("title", "")

        # ساخت لینک قابل کلیک به گروه
        internal_id = str(cid).replace("-100", "")
        link = f"https://t.me/c/{internal_id}/1"

        txt += (
            f"● <b>{title or 'Dest'}</b>\n"
            f"<code>{cid}</code>\n"
            f"<a href=\"{link}\">ورود به گروه</a>\n\n"
        )

    return await message.answer(txt, parse_mode="HTML", reply_markup=dests_keyboard())


# =====================================================
#   📋 پست‌های امروز
# =====================================================
@router.message(F.text.contains("پست‌های امروز"))
async def today(message: types.Message):
    posts = list_today_posts()
    if not posts:
        return await message.answer("📭 امروز پستی نیست.", reply_markup=admin_keyboard())

    txt = "<b>📋 پست‌های امروز</b>\n\n"
    for p in posts:
        icon = "🔔" if p["active"] else "❌"
        txt += f"{icon} <code>{p['message_id']}</code>\n"

    return await message.answer(txt, parse_mode="HTML", reply_markup=admin_keyboard())


# =====================================================
#   ⏱ تنظیم فاصله
# =====================================================
@router.message(F.text.contains("فاصله"))
async def ask_interval(message: types.Message):
    return await message.answer(
        "⏱ فاصله را بفرست:\n"
        "<code>5m</code> — ۵ دقیقه\n"
        "<code>2h</code> — ۲ ساعت\n"
        "<code>10</code> — ۱۰ دقیقه",
        parse_mode="HTML"
    )


@router.message(F.text.regexp(r"^\d+[mh]?$"))
async def set_int(message: types.Message):
    raw = message.text.lower()
    if raw.isdigit():
        sec = int(raw) * 60
    elif raw.endswith("m"):
        sec = int(raw[:-1]) * 60
    elif raw.endswith("h"):
        sec = int(raw[:-1]) * 3600

    await set_interval(sec)
    return await message.answer(
        f"⏱ فاصله روی <code>{sec}</code> ثانیه تنظیم شد.",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# =====================================================
#   🔙 بازگشت
# =====================================================
@router.message(F.text.contains("بازگشت"))
async def back_main(message: types.Message):
    return await message.answer("بازگشت به پنل مدیریت", reply_markup=admin_keyboard())
