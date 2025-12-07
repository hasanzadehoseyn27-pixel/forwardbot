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


# -------------------- کیبوردها -------------------- #
def admin_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="📍 مدیریت مقصدها"),
                types.KeyboardButton(text="📋 پست‌ها"),
            ],
            [
                types.KeyboardButton(text="🌓 پست‌های خاموش"),
                types.KeyboardButton(text="⏱ تنظیم فاصله"),
            ],
            [
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
                types.KeyboardButton(text="🔙 بازگشت"),
            ]
        ],
        resize_keyboard=True
    )


ADD_DEST_WAIT = set()
DEL_DEST_WAIT = set()


# -------------------- /admin -------------------- #
@router.message(Command("admin"))
async def admin_start(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")
    return await message.answer("🔧 پنل مدیریت ربات", reply_markup=admin_keyboard())


# -------------------- مدیریت مقصدها -------------------- #
def extract_chat(text: str):
    text = text.strip()

    if text.startswith("-100") and text[1:].isdigit():
        return int(text), None

    if "t.me/" in text:
        username = text.split("t.me/")[1]
        username = username.replace("https://", "").replace("http://", "")
        username = username.split("/")[0]
        return None, username

    return None, None


@router.message(F.text.contains("مدیریت مقصد"))
async def menu_dest(message: types.Message):
    return await message.answer(
        "📍 <b>مدیریت مقصدها</b>\n\n"
        "➕ افزودن مقصد → آیدی یا لینک گروه را ارسال کنید\n"
        "🗑 حذف مقصد → فقط chat_id را بفرست\n"
        "📋 لیست مقصدها → نمایش همه مقصدها\n",
        parse_mode="HTML",
        reply_markup=dests_keyboard()
    )


# -------------------- افزودن مقصد -------------------- #
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
    ADD_DEST_WAIT.remove(uid)

    chat_id, username = extract_chat(raw)

    if chat_id:
        try:
            chat = await message.bot.get_chat(chat_id)
            title = chat.title or getattr(chat, "full_name", "") or "گروه"
        except:
            title = "گروه"

        add_destination(chat_id, title)

        return await message.answer(
            f"✅ مقصد اضافه شد:\n<code>{chat_id}</code> — {title}",
            parse_mode="HTML",
            reply_markup=dests_keyboard()
        )

    if username:
        try:
            chat = await message.bot.get_chat(username)
            cid = chat.id
            title = chat.title or getattr(chat, "full_name", "") or "گروه"

            add_destination(cid, title)

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


# -------------------- حذف مقصد -------------------- #
@router.message(F.text.contains("حذف مقصد"))
async def ask_delete(message: types.Message):
    DEL_DEST_WAIT.add(message.from_user.id)
    return await message.answer(
        "chat_id مقصد را ارسال کنید:\n<code>-100xxxxxxxx</code>",
        parse_mode="HTML"
    )


@router.message(F.text, F.from_user.id.func(lambda uid: uid in DEL_DEST_WAIT))
async def del_dest(message: types.Message):
    uid = message.from_user.id
    DEL_DEST_WAIT.remove(uid)

    try:
        cid = int(message.text)
    except:
        return await message.answer("❗ عدد معتبر نیست.", reply_markup=dests_keyboard())

    ok = remove_destination(cid)

    return await message.answer(
        "🗑 حذف شد." if ok else "❗ مقصدی با این آیدی وجود ندارد.",
        reply_markup=dests_keyboard()
    )


# -------------------- لیست مقصدها -------------------- #
@router.message(F.text.contains("لیست مقصد"))
async def list_dest(message: types.Message):
    dests = list_destinations()
    if not dests:
        return await message.answer("❗ هنوز هیچ مقصدی ثبت نشده است.", reply_markup=dests_keyboard())

    txt = "<b>📍 لیست مقصدها</b>\n\n"
    index = 1

    for d in dests:
        cid = d["chat_id"]
        title = d.get("title", "") or "گروه"
        internal_id = str(cid).replace("-100", "")
        link = f"https://t.me/c/{internal_id}/1"
        txt += f"{index}/ <a href=\"{link}\">{title}</a>\n"
        index += 1

    return await message.answer(txt, parse_mode="HTML", reply_markup=dests_keyboard())


# -------------------- نمایش همه پست‌ها -------------------- #
@router.message(F.text.contains("پست‌ها"))
async def all_posts(message: types.Message):

    posts = list_all_posts()
    if not posts:
        return await message.answer("📭 هیچ پستی وجود ندارد.", reply_markup=admin_keyboard())

    internal_id = str(SETTINGS.SOURCE_CHANNEL_ID).replace("-100", "")

    for p in posts:
        msg_id = p["message_id"]
        active = p.get("active", True)

        # گرفتن شماره آگهی واقعی با Forward Trick
        try:
            fwd = await message.bot.forward_message(
                chat_id=message.chat.id,
                from_chat_id=SETTINGS.SOURCE_CHANNEL_ID,
                message_id=msg_id
            )
            caption = fwd.caption or fwd.text or ""
            await fwd.delete()
        except:
            caption = ""

        # پیدا کردن شماره آگهی
        m = re.search(r"آگهی شماره\s*#(\d+)", caption)
        ad_no = m.group(1) if m else msg_id

        bell = "🔔" if active else "🔕"

        text = (
            f'<a href="https://t.me/c/{internal_id}/{msg_id}">{bell} آگهی شماره #{ad_no}</a>'
        )

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[
                types.InlineKeyboardButton(
                    text="❌ خاموش" if active else "✅ روشن",
                    callback_data=f"toggle:{msg_id}"
                )
            ]]
        )

        await message.answer(text, reply_markup=kb, parse_mode="HTML")


# -------------------- لیست پست‌های خاموش -------------------- #
@router.message(F.text.contains("پست‌های خاموش"))
async def inactive_posts(message: types.Message):

    posts = list_inactive_posts()
    if not posts:
        return await message.answer("🌓 پست خاموش وجود ندارد.", reply_markup=admin_keyboard())

    internal_id = str(SETTINGS.SOURCE_CHANNEL_ID).replace("-100", "")

    for p in posts:
        msg_id = p["message_id"]

        # forward trick برای گرفتن شماره آگهی
        try:
            fwd = await message.bot.forward_message(
                chat_id=message.chat.id,
                from_chat_id=SETTINGS.SOURCE_CHANNEL_ID,
                message_id=msg_id
            )
            caption = fwd.caption or fwd.text or ""
            await fwd.delete()
        except:
            caption = ""

        # شماره آگهی
        m = re.search(r"آگهی شماره\s*#(\d+)", caption)
        ad_no = m.group(1) if m else msg_id

        text = (
            f'<a href="https://t.me/c/{internal_id}/{msg_id}">🔕 آگهی شماره #{ad_no}</a>'
        )

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[
                types.InlineKeyboardButton(
                    text="✅ روشن کردن",
                    callback_data=f"toggle:{msg_id}"
                )
            ]]
        )

        await message.answer(text, reply_markup=kb, parse_mode="HTML")


# -------------------- Callback روشن/خاموش -------------------- #
@router.callback_query(F.data.startswith("toggle:"))
async def toggle_handler(query: types.CallbackQuery):
    msg_id = int(query.data.split(":")[1])

    new_state = toggle_post(msg_id)
    if new_state is None:
        return await query.answer("❗ پست یافت نشد!", show_alert=True)

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[
            types.InlineKeyboardButton(
                text="❌ خاموش" if new_state else "✅ روشن",
                callback_data=f"toggle:{msg_id}"
            )
        ]]
    )

    await query.answer("✔ تغییر انجام شد.")
    await query.message.edit_reply_markup(reply_markup=kb)


# -------------------- تنظیم فاصله (ثانیه/دقیقه/ساعت) -------------------- #
@router.message(F.text.contains("تنظیم فاصله"))
async def interval_menu(message: types.Message):

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="⏱ ثانیه‌ای", callback_data="iv:sec"),
                types.InlineKeyboardButton(text="🕰 دقیقه‌ای", callback_data="iv:min"),
                types.InlineKeyboardButton(text="⏳ ساعتی", callback_data="iv:hour"),
            ],
            [
                types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="iv:back")
            ]
        ]
    )

    await message.answer("واحد زمانی را انتخاب کنید:", reply_markup=kb)


@router.callback_query(F.data.startswith("iv:"))
async def interval_unit(query: types.CallbackQuery):

    unit = query.data.split(":")[1]

    if unit == "back":
        return await query.message.edit_text("🔧 تنظیمات", reply_markup=None)

    txt = {
        "sec": "⏱ لطفاً زمان را به ثانیه وارد کنید:",
        "min": "🕰 لطفاً زمان را به دقیقه وارد کنید:",
        "hour": "⏳ لطفاً زمان را به ساعت وارد کنید:",
    }[unit]

    await query.message.answer(txt)

    query.message.bot["interval_unit"] = unit  # ذخیره نوع واحد


@router.message(F.text.regexp(r"^\d+$"))
async def interval_value(message: types.Message):

    unit = message.bot.get("interval_unit", None)
    if not unit:
        return  # ربطی ندارد

    value = int(message.text)

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

    await message.answer(f"✔ زمان تکرار شما هر {label} ثبت شد.", reply_markup=admin_keyboard())


# -------------------- حالت ارسال (دائمی / یکبار) -------------------- #
@router.message(F.text.contains("حالت ارسال"))
async def send_mode_menu(message: types.Message):

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🔁 ارسال دائمی", callback_data="mode:always"),
                types.InlineKeyboardButton(text="1️⃣ ارسال یکبار", callback_data="mode:once"),
            ],
            [
                types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="mode:back")
            ]
        ]
    )

    await message.answer("حالت ارسال را انتخاب کنید:", reply_markup=kb)


@router.callback_query(F.data.startswith("mode:"))
async def change_mode(query: types.CallbackQuery):
    mode = query.data.split(":")[1]

    if mode == "back":
        return await query.message.edit_text("🔧 تنظیمات", reply_markup=None)

    if mode == "always":
        await set_send_mode(False)
        await query.answer("🔁 ارسال دائمی فعال شد ✔")

    else:
        await set_send_mode(True)
        await query.answer("1️⃣ ارسال یکبار فعال شد ✔")

    await query.message.delete()


# -------------------- بازگشت -------------------- #
@router.message(F.text.contains("بازگشت"))
async def back_main(message: types.Message):
    return await message.answer("بازگشت به پنل مدیریت", reply_markup=admin_keyboard())
