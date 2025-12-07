from aiogram import Router, types, F
from aiogram.filters import Command
import re

from app.config import SETTINGS
from app.storage.dests import add_destination, remove_destination, list_destinations
from app.storage.posts import list_today_posts, toggle_post
from app.handlers.scheduler import set_interval

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
                types.KeyboardButton(text="📋 پست‌های امروز"),
            ],
            [
                types.KeyboardButton(text="⏱ تنظیم فاصله"),
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


# -------------------- پست‌های امروز + دکمه روشن/خاموش -------------------- #

@router.message(F.text.contains("پست‌های امروز"))
async def today(message: types.Message):

    posts = list_today_posts()
    if not posts:
        return await message.answer("📭 امروز هیچ پستی یافت نشد.", reply_markup=admin_keyboard())

    internal_id = str(SETTINGS.SOURCE_CHANNEL_ID).replace("-100", "")

    for p in posts:
        msg_id = p["message_id"]
        active = p.get("active", True)

        bell = "🔔" if active else "🔕"
        link = f"https://t.me/c/{internal_id}/{msg_id}"

        text = (
            f"{bell} <b>آگهی شماره {msg_id}</b>\n"
            f"<a href=\"{link}\">مشاهده پست در کانال</a>"
        )

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[
                types.InlineKeyboardButton(
                    text="❌ خاموش کردن" if active else "✅ روشن کردن",
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
                text="❌ خاموش کردن" if new_state else "✅ روشن کردن",
                callback_data=f"toggle:{msg_id}"
            )
        ]]
    )

    await query.answer("وضعیت تغییر کرد.")
    await query.message.edit_reply_markup(reply_markup=kb)


# -------------------- تنظیم فاصله -------------------- #

@router.message(F.text.contains("فاصله"))
async def ask_interval(message: types.Message):
    return await message.answer(
        "⏱ مقدار فاصله را ارسال کنید:\n"
        "<code>5m</code>\n"
        "<code>2h</code>\n"
        "<code>10</code>",
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


# -------------------- بازگشت -------------------- #

@router.message(F.text.contains("بازگشت"))
async def back_main(message: types.Message):
    return await message.answer("بازگشت به پنل مدیریت", reply_markup=admin_keyboard())
#ss