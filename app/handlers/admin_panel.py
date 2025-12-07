from aiogram import Router, types, F
from aiogram.filters import Command

from app.config import SETTINGS
from app.storage.dests import add_destination, remove_destination, list_destinations
from app.storage.posts import list_today_posts, toggle_post

from settings_storage import (
    get_send_mode,
    set_send_mode,
    get_interval,
    set_interval_value
)

router = Router()

# -------------------- تشخیص ادمین -------------------- #

def is_admin(uid: int) -> bool:
    return uid == SETTINGS.OWNER_ID or uid in SETTINGS.ADMIN_IDS


# -------------------- Reply Keyboards -------------------- #

def admin_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="📍 مدیریت مقصدها"),
                types.KeyboardButton(text="📋 پست‌های امروز"),
            ],
            [
                types.KeyboardButton(text="⚙️ حالت ارسال"),
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
                types.KeyboardButton(text="📋 لیست مقصدها"),
            ],
            [
                types.KeyboardButton(text="🔙 بازگشت")
            ]
        ],
        resize_keyboard=True
    )


def sendmode_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="🔁 ارسال دائمی"),
                types.KeyboardButton(text="1️⃣ ارسال یکبار"),
            ],
            [types.KeyboardButton(text="🔙 بازگشت")]
        ],
        resize_keyboard=True
    )


def interval_unit_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="⏱ ثانیه‌ای"),
                types.KeyboardButton(text="🕰 دقیقه‌ای"),
                types.KeyboardButton(text="⏳ ساعتی"),
            ],
            [types.KeyboardButton(text="🔙 بازگشت")]
        ],
        resize_keyboard=True
    )


# -------------------- حالت‌های انتظار برای ورودی -------------------- #

ADD_DEST_WAIT = set()
DEL_DEST_WAIT = set()

SENDMODE_STATE = {}   # user_id -> state
SENDMODE_UNIT = {}    # user_id -> "s" / "m" / "h"


# -------------------- /admin -------------------- #

@router.message(Command("admin"))
async def admin_start(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")
    return await message.answer("🔧 پنل مدیریت ربات", reply_markup=admin_keyboard())


# -------------------- مدیریت مقصدها -------------------- #

def extract_chat(text: str):
    text = text.strip()

    # حالت chat_id مستقیم
    if text.startswith("-100") and text[1:].isdigit():
        return int(text), None

    # حالت لینک t.me
    if "t.me/" in text:
        username = text.split("t.me/")[1]
        username = username.split("/")[0]
        return None, username

    return None, None


@router.message(F.text == "📍 مدیریت مقصدها")
async def menu_dest(message: types.Message):
    return await message.answer(
        "📍 <b>مدیریت مقصدها</b>",
        parse_mode="HTML",
        reply_markup=dests_keyboard()
    )


# -------------------- افزودن مقصد -------------------- #

@router.message(F.text == "➕ افزودن مقصد")
async def ask_add_dest(message: types.Message):
    ADD_DEST_WAIT.add(message.from_user.id)
    return await message.answer(
        "chat_id یا لینک گروه را ارسال کنید:",
        parse_mode="HTML"
    )


@router.message(F.text, F.from_user.id.func(lambda uid: uid in ADD_DEST_WAIT))
async def handle_add_dest(message: types.Message):
    uid = message.from_user.id
    ADD_DEST_WAIT.remove(uid)

    raw = message.text.strip()
    chat_id, username = extract_chat(raw)

    # حالت chat_id
    if chat_id:
        try:
            chat = await message.bot.get_chat(chat_id)
            title = chat.title or "گروه"
            add_destination(chat_id, title)
            return await message.answer(f"✅ مقصد اضافه شد: {title}", reply_markup=dests_keyboard())
        except:
            return await message.answer("❗ ربات به مقصد دسترسی ندارد.", reply_markup=dests_keyboard())

    # حالت username
    if username:
        try:
            chat = await message.bot.get_chat(username)
            cid = chat.id
            title = chat.title or "گروه"
            add_destination(cid, title)
            return await message.answer(f"✅ مقصد اضافه شد: {title}", reply_markup=dests_keyboard())
        except:
            return await message.answer("❗ ربات به مقصد دسترسی ندارد.", reply_markup=dests_keyboard())

    return await message.answer("❗ ورودی معتبر نبود.", reply_markup=dests_keyboard())


# -------------------- حذف مقصد -------------------- #

@router.message(F.text == "🗑 حذف مقصد")
async def ask_del(message: types.Message):
    DEL_DEST_WAIT.add(message.from_user.id)
    return await message.answer("chat_id مقصد را ارسال کنید:", parse_mode="HTML")


@router.message(F.text, F.from_user.id.func(lambda uid: uid in DEL_DEST_WAIT))
async def do_del(message: types.Message):
    uid = message.from_user.id
    DEL_DEST_WAIT.remove(uid)

    try:
        cid = int(message.text.strip())
    except:
        return await message.answer("❗ فرمت اشتباه.", reply_markup=dests_keyboard())

    ok = remove_destination(cid)
    return await message.answer(
        "🗑 حذف شد." if ok else "❗ مقصد یافت نشد.",
        reply_markup=dests_keyboard()
    )


# -------------------- لیست مقصدها -------------------- #

@router.message(F.text == "📋 لیست مقصدها")
async def list_destinations_handler(message: types.Message):
    dests = list_destinations()

    if not dests:
        return await message.answer("❗ هنوز هیچ مقصدی ثبت نشده.", reply_markup=dests_keyboard())

    txt = "<b>📍 لیست مقصدها</b>\n\n"

    for i, d in enumerate(dests, start=1):
        cid = d["chat_id"]
        title = d.get("title", "") or "گروه"

        internal = str(cid).replace("-100", "")
        link = f"https://t.me/c/{internal}/1"

        txt += f"{i}. <a href=\"{link}\">{title}</a>\n"

    return await message.answer(txt, parse_mode="HTML", reply_markup=dests_keyboard())


# -------------------- پست‌های امروز -------------------- #

@router.message(F.text == "📋 پست‌های امروز")
async def today(message: types.Message):
    posts = list_today_posts()
    if not posts:
        return await message.answer("📭 هیچ پستی وجود ندارد.", reply_markup=admin_keyboard())

    internal = str(SETTINGS.SOURCE_CHANNEL_ID).replace("-100", "")

    for p in posts:
        msg_id = p["message_id"]
        ad_num = p.get("ad_number", msg_id)
        active = p.get("active", True)

        bell = "🔔" if active else "🔕"
        link = f"https://t.me/c/{internal}/{msg_id}"

        text = (
            f"{bell} <b>آگهی شماره #{ad_num}</b>\n"
            f"<a href=\"{link}\">مشاهده پست</a>"
        )

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="✔ روشن" if active else "❌ خاموش",
                        callback_data=f"toggle:{msg_id}"
                    )
                ]
            ]
        )

        await message.answer(text, parse_mode="HTML", reply_markup=kb)


# -------------------- Toggle -------------------- #

@router.callback_query(F.data.startswith("toggle:"))
async def toggle_post_handler(query: types.CallbackQuery):
    msg_id = int(query.data.split(":")[1])
    new_state = toggle_post(msg_id)

    if new_state is None:
        return await query.answer("❗ پست یافت نشد!", show_alert=True)

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="✔ روشن" if new_state else "❌ خاموش",
                    callback_data=f"toggle:{msg_id}"
                )
            ]
        ]
    )

    await query.message.edit_reply_markup(reply_markup=kb)


# -------------------- حالت ارسال -------------------- #

@router.message(F.text == "⚙️ حالت ارسال")
async def send_mode_menu(message: types.Message):
    uid = message.from_user.id
    SENDMODE_STATE[uid] = "main"

    current = get_send_mode()

    return await message.answer(
        f"⚙️ حالت فعلی ارسال: <b>{'🔁 دائمی' if current=='repeat' else '1️⃣ یکبار'}</b>\n\n"
        "یکی از حالت‌ها را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=sendmode_keyboard()
    )


@router.message(F.text.in_(["🔁 ارسال دائمی", "1️⃣ ارسال یکبار"]))
async def choose_sendmode(message: types.Message):
    uid = message.from_user.id

    if message.text == "1️⃣ ارسال یکبار":
        set_send_mode("once")
        return await message.answer("🔔 حالت «ارسال یکبار» فعال شد.", reply_markup=admin_keyboard())

    set_send_mode("repeat")
    SENDMODE_STATE[uid] = "choose_unit"

    return await message.answer("واحد زمانی را انتخاب کنید:", reply_markup=interval_unit_keyboard())


@router.message(F.text.in_(["⏱ ثانیه‌ای", "🕰 دقیقه‌ای", "⏳ ساعتی"]))
async def choose_unit(message: types.Message):
    uid = message.from_user.id

    SENDMODE_UNIT[uid] = (
        "s" if message.text == "⏱ ثانیه‌ای" else
        "m" if message.text == "🕰 دقیقه‌ای" else
        "h"
    )

    return await message.answer("⏱ مقدار را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())


@router.message(F.text.regexp(r"^\d+$"))
async def set_interval_handler(message: types.Message):
    uid = message.from_user.id

    if uid not in SENDMODE_UNIT:
        return

    unit = SENDMODE_UNIT.pop(uid)
    value = int(message.text)

    sec = (
        value if unit == "s" else
        value * 60 if unit == "m" else
        value * 3600
    )

    set_interval_value(sec)
    set_send_mode("repeat")

    return await message.answer(
        f"⏱ فاصله روی <b>{sec}</b> ثانیه تنظیم شد.",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# -------------------- بازگشت -------------------- #

@router.message(F.text == "🔙 بازگشت")
async def back(message: types.Message):
    return await message.answer("بازگشت به پنل مدیریت", reply_markup=admin_keyboard())
