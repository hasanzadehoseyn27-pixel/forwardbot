from aiogram import Router, types, F
from aiogram.filters import Command
import re

from app.config import SETTINGS
from app.storage.dests import add_destination, remove_destination, list_destinations
from app.storage.posts import (
    list_all_posts,
    list_inactive_posts,
    toggle_post
)
from app.handlers.scheduler import (
    set_interval,
    set_send_mode
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
                types.KeyboardButton(text="📋 پست‌ها"),
            ],
            [
                types.KeyboardButton(text="🌓 پست‌های خاموش"),
                types.KeyboardButton(text="🔁 حالت ارسال"),
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


def send_mode_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="🔁 ارسال دائمی"),
                types.KeyboardButton(text="1️⃣ ارسال یکبار"),
            ],
            [
                types.KeyboardButton(text="🔙 بازگشت")
            ]
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
            [
                types.KeyboardButton(text="🔙 بازگشت")
            ]
        ],
        resize_keyboard=True
    )


def back_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="🔙 بازگشت")]],
        resize_keyboard=True
    )


# -------------------- State Sets -------------------- #

SEND_MENU = set()
WAIT_INTERVAL_VALUE = set()
INTERVAL_UNIT = {}  # user_id → sec/min/hour


# -------------------- /admin -------------------- #

@router.message(Command("admin"))
async def admin_start(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")
    return await message.answer("🔧 پنل مدیریت ربات", reply_markup=admin_keyboard())


# -------------------- مدیریت مقصدها -------------------- #

@router.message(F.text == "📍 مدیریت مقصدها")
async def menu_dest(message: types.Message):
    return await message.answer(
        "📍 مدیریت مقصدها",
        reply_markup=dests_keyboard()
    )


@router.message(F.text == "➕ افزودن مقصد")
async def ask_add_dest(message: types.Message):
    ADD_DEST_WAIT.add(message.from_user.id)
    return await message.answer(
        "chat_id یا لینک گروه را ارسال کنید:",
        parse_mode="HTML"
    )


ADD_DEST_WAIT = set()
DEL_DEST_WAIT = set()


@router.message(F.text, F.from_user.id.func(lambda uid: uid in ADD_DEST_WAIT))
async def handle_add_dest(message: types.Message):
    uid = message.from_user.id
    ADD_DEST_WAIT.remove(uid)

    txt = message.text.strip()

    # chat_id مستقیم
    if txt.startswith("-100") and txt[1:].isdigit():
        cid = int(txt)
        try:
            chat = await message.bot.get_chat(cid)
            title = chat.title or "گروه"
        except:
            title = "گروه"

        add_destination(cid, title)
        return await message.answer(f"✅ مقصد {title} اضافه شد!", reply_markup=dests_keyboard())

    # لینک t.me
    if "t.me/" in txt:
        username = txt.split("t.me/")[1].split("/")[0]
        try:
            chat = await message.bot.get_chat(username)
            cid = chat.id
            title = chat.title or "گروه"
            add_destination(cid, title)
            return await message.answer(f"✅ مقصد {title} اضافه شد!", reply_markup=dests_keyboard())
        except:
            return await message.answer("❗ خطا در گرفتن اطلاعات مقصد.", reply_markup=dests_keyboard())

    return await message.answer("❗ ورودی معتبر نبود!", reply_markup=dests_keyboard())


# حذف مقصد

@router.message(F.text == "🗑 حذف مقصد")
async def ask_del(message: types.Message):
    DEL_DEST_WAIT.add(message.from_user.id)
    return await message.answer("chat_id مقصد را ارسال کنید:", reply_markup=back_keyboard())


@router.message(F.text, F.from_user.id.func(lambda uid: uid in DEL_DEST_WAIT))
async def do_del(message: types.Message):
    uid = message.from_user.id
    DEL_DEST_WAIT.remove(uid)

    try:
        cid = int(message.text)
    except:
        return await message.answer("❗ فرمت اشتباه است!", reply_markup=dests_keyboard())

    ok = remove_destination(cid)
    return await message.answer("🗑 حذف شد." if ok else "❗ یافت نشد.", reply_markup=dests_keyboard())


# -------------------- لیست مقصدها -------------------- #

@router.message(F.text == "📋 لیست مقصدها")
async def list_destinations_handler(message: types.Message):
    dests = list_destinations()

    if not dests:
        return await message.answer("❗ مقصدی ثبت نشده.", reply_markup=dests_keyboard())

    text = "📍 لیست مقصدها:\n\n"
    for i, d in enumerate(dests, 1):
        text += f"{i}. {d.get('title','گروه')} — <code>{d['chat_id']}</code>\n"

    return await message.answer(text, parse_mode="HTML", reply_markup=dests_keyboard())


# -------------------- نمایش همه پست‌ها -------------------- #

@router.message(F.text == "📋 پست‌ها")
async def all_posts(message: types.Message):
    posts = list_all_posts()
    if not posts:
        return await message.answer("📭 هیچ پستی وجود ندارد.", reply_markup=admin_keyboard())

    internal_id = str(SETTINGS.SOURCE_CHANNEL_ID).replace("-100", "")

    for p in posts:
        msg_id = p["message_id"]
        active = p.get("active", True)

        # استخراج شماره آگهی
        try:
            fwd = await message.bot.forward_message(message.chat.id, SETTINGS.SOURCE_CHANNEL_ID, msg_id)
            caption = fwd.caption or fwd.text or ""
            await fwd.delete()
        except:
            caption = ""

        m = re.search(r"آگهی شماره\s*#(\d+)", caption)
        ad_no = m.group(1) if m else msg_id

        bell = "🔔" if active else "🔕"

        text = f'<a href="https://t.me/c/{internal_id}/{msg_id}">{bell} آگهی شماره #{ad_no}</a>'

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="❌ خاموش" if active else "✅ روشن",
                        callback_data=f"toggle:{msg_id}"
                    )
                ]
            ]
        )

        await message.answer(text, parse_mode="HTML", reply_markup=kb)


# -------------------- پست‌های خاموش -------------------- #

@router.message(F.text == "🌓 پست‌های خاموش")
async def inactive_posts(message: types.Message):

    posts = list_inactive_posts()
    if not posts:
        return await message.answer("هیچ پست خاموشی وجود ندارد.", reply_markup=admin_keyboard())

    internal_id = str(SETTINGS.SOURCE_CHANNEL_ID).replace("-100", "")

    for p in posts:
        msg_id = p["message_id"]

        try:
            fwd = await message.bot.forward_message(message.chat.id, SETTINGS.SOURCE_CHANNEL_ID, msg_id)
            caption = fwd.caption or fwd.text or ""
            await fwd.delete()
        except:
            caption = ""

        m = re.search(r"آگهی شماره\s*#(\d+)", caption)
        ad_no = m.group(1) if m else msg_id

        text = f'<a href="https://t.me/c/{internal_id}/{msg_id}">🔕 آگهی شماره #{ad_no}</a>'

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="♻ روشن", callback_data=f"toggle:{msg_id}")
                ]
            ]
        )

        await message.answer(text, parse_mode="HTML", reply_markup=kb)


# -------------------- Toggle پست -------------------- #

@router.callback_query(F.data.startswith("toggle:"))
async def toggle_post_handler(query: types.CallbackQuery):
    msg_id = int(query.data.split(":")[1])

    new_state = toggle_post(msg_id)

    await query.answer("✔ تغییر اعمال شد.")

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="❌ خاموش" if new_state else "✅ روشن",
                callback_data=f"toggle:{msg_id}"
            )]
        ]
    )

    await query.message.edit_reply_markup(reply_markup=kb)


# -------------------- حالت ارسال -------------------- #

@router.message(F.text == "🔁 حالت ارسال")
async def mode_menu(message: types.Message):
    SEND_MENU.add(message.from_user.id)
    return await message.answer("حالت ارسال را انتخاب کنید:", reply_markup=send_mode_keyboard())


@router.message(F.text == "🔁 ارسال دائمی")
async def mode_always(message: types.Message):
    await set_send_mode(False)
    return await message.answer("واحد زمانی را انتخاب کنید:", reply_markup=interval_unit_keyboard())


@router.message(F.text == "1️⃣ ارسال یکبار")
async def mode_once(message: types.Message):
    await set_send_mode(True)
    return await message.answer("✔ حالت ارسال یکبار فعال شد.", reply_markup=send_mode_keyboard())


# -------------------- انتخاب واحد زمانی -------------------- #

@router.message(F.text.in_(["⏱ ثانیه‌ای", "🕰 دقیقه‌ای", "⏳ ساعتی"]))
async def choose_unit(message: types.Message):
    uid = message.from_user.id

    if "ثانیه" in message.text:
        INTERVAL_UNIT[uid] = "sec"
        txt = "⏱ مقدار را به ثانیه وارد کنید:"
    elif "دقیقه" in message.text:
        INTERVAL_UNIT[uid] = "min"
        txt = "🕰 مقدار را به دقیقه وارد کنید:"
    else:
        INTERVAL_UNIT[uid] = "hour"
        txt = "⏳ مقدار را به ساعت وارد کنید:"

    WAIT_INTERVAL_VALUE.add(uid)

    return await message.answer(txt, reply_markup=back_keyboard())


# -------------------- مقدار فاصله -------------------- #

@router.message(F.text.regexp(r"^\d+$"))
async def interval_value_handler(message: types.Message):
    uid = message.from_user.id

    if uid not in WAIT_INTERVAL_VALUE:
        return

    value = int(message.text)
    unit = INTERVAL_UNIT.get(uid)

    if unit == "sec":
        sec = value
        label = f"{value} ثانیه"
    elif unit == "min":
        sec = value * 60
        label = f"{value} دقیقه"
    else:
        sec = value * 3600
        label = f"{value} ساعت"

    await set_interval(sec)

    WAIT_INTERVAL_VALUE.remove(uid)
    INTERVAL_UNIT.pop(uid, None)

    return await message.answer(
        f"✔ زمان تکرار هر {label} ثبت شد.",
        reply_markup=send_mode_keyboard()
    )


# -------------------- بازگشت -------------------- #

@router.message(F.text == "🔙 بازگشت")
async def back_to_main(message: types.Message):
    uid = message.from_user.id

    SEND_MENU.discard(uid)
    WAIT_INTERVAL_VALUE.discard(uid)
    INTERVAL_UNIT.pop(uid, None)

    return await message.answer("بازگشت به پنل مدیریت", reply_markup=admin_keyboard())
