from aiogram import Router, types, F
from aiogram.filters import Command

from app.config import SETTINGS
from app.storage.dests import (
    add_destination,
    remove_destination,
    list_destinations,
)
from app.storage.admins import (
    add_admin,
    remove_admin,
    list_admins,
    is_admin as admin_check,
)
from app.storage.posts import (
    list_today_posts,
    set_post_active
)
from app.handlers.scheduler import set_interval

router = Router()


# ---------------------- زیرساخت ---------------------- #

def is_admin(uid: int) -> bool:
    return admin_check(uid)


# ---------------------- پنل اصلی ---------------------- #

def admin_main_menu():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📍 مدیریت مقصدها", callback_data="menu_dests")],
            [types.InlineKeyboardButton(text="👤 مدیریت ادمین‌ها", callback_data="menu_admins")],
            [types.InlineKeyboardButton(text="⏱ تنظیم فاصله زمانی", callback_data="menu_interval")],
            [types.InlineKeyboardButton(text="📋 پست‌های امروز", callback_data="menu_posts")],
            [types.InlineKeyboardButton(text="🔚 خروج", callback_data="menu_exit")],
        ]
    )


@router.message(Command("admin"))
async def admin_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما ادمین نیستید.")
    await message.answer(
        "🔧 **پنل مدیریت ربات**",
        reply_markup=admin_main_menu(),
        parse_mode="Markdown"
    )


# ---------------------- زیرمنو مقصدها ---------------------- #

def menu_dests():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ افزودن مقصد", callback_data="dests_add")],
            [types.InlineKeyboardButton(text="🗑 حذف مقصد", callback_data="dests_remove")],
            [types.InlineKeyboardButton(text="📋 لیست مقصدها", callback_data="dests_list")],
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_main")],
        ]
    )


@router.callback_query(F.data == "menu_dests")
async def open_dest_menu(call: types.CallbackQuery):
    await call.message.edit_text("📍 مدیریت مقصدها", reply_markup=menu_dests())


# --- افزودن مقصد --- #

@router.callback_query(F.data == "dests_add")
async def dests_add_prompt(call: types.CallbackQuery):
    await call.message.edit_text(
        "➕ یک پیام از مقصد *فوروارد* کنید.\n"
        "ربات chat_id را تشخیص می‌دهد.",
        parse_mode="Markdown",
        reply_markup=menu_dests()
    )


@router.message(F.forward_from_chat)
async def add_dest_from_forward(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    chat = message.forward_from_chat
    ok = add_destination(chat.id, chat.title or chat.full_name or "")
    if ok:
        await message.answer(f"✅ مقصد اضافه شد:\n{chat.id} — {chat.title}")
    else:
        await message.answer("ℹ️ این مقصد قبلاً ثبت شده است.")


# --- حذف مقصد --- #

@router.callback_query(F.data == "dests_remove")
async def dests_remove_prompt(call: types.CallbackQuery):
    await call.message.edit_text(
        "🗑 آیدی مقصد را ارسال کنید:",
        reply_markup=menu_dests()
    )


@router.message(F.text.regexp(r"^-?\d+$"))
async def remove_dest(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    chat_id = int(message.text)
    ok = remove_destination(chat_id)
    await message.answer("🗑 حذف شد." if ok else "❗ مقصد یافت نشد.")


# --- لیست مقصدها --- #

@router.callback_query(F.data == "dests_list")
async def dests_list(call: types.CallbackQuery):
    dests = list_destinations()
    if not dests:
        await call.message.edit_text("❗ هیچ مقصدی ثبت نشده.")
        return
    text = "📍 **مقصدها:**\n\n"
    for d in dests:
        text += f"- `{d['chat_id']}` — {d.get('title','')}\n"
    await call.message.edit_text(text, reply_markup=menu_dests(), parse_mode="Markdown")


# ---------------------- مدیریت ادمین‌ها ---------------------- #

def admins_menu():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ افزودن ادمین", callback_data="adm_add")],
            [types.InlineKeyboardButton(text="🗑 حذف ادمین", callback_data="adm_del")],
            [types.InlineKeyboardButton(text="📋 لیست ادمین‌ها", callback_data="adm_list")],
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_main")],
        ]
    )


@router.callback_query(F.data == "menu_admins")
async def open_admins(call: types.CallbackQuery):
    await call.message.edit_text("👤 مدیریت ادمین‌ها", reply_markup=admins_menu())


# --- روش افزودن ادمین --- #

@router.callback_query(F.data == "adm_add")
async def adm_add_prompt(call: types.CallbackQuery):
    await call.message.edit_text(
        "➕ یکی از روش‌ها:\n"
        "- فوروارد پیام کاربر\n"
        "- @username\n"
        "- لینک t.me\n"
        "- chat_id عددی",
        reply_markup=admins_menu()
    )


@router.message(F.forward_from)
async def adm_add_from_forward(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    uid = message.forward_from.id
    ok = add_admin(uid)
    await message.answer("✅ افزوده شد." if ok else "ℹ️ قبلاً ادمین بود.")


@router.message(F.text.regexp(r"@([A-Za-z0-9_]{5,})"))
async def adm_add_from_username(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    username = message.text.replace("@", "")
    try:
        chat = await message.bot.get_chat(username)
        uid = chat.id
        ok = add_admin(uid)
        await message.answer("✅ افزوده شد." if ok else "ℹ️ قبلاً ادمین بود.")
    except:
        await message.answer("❗ کاربر یافت نشد.")


@router.message(F.text.regexp(r"^-?\d+$"))
async def adm_add_from_id(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    uid = int(message.text)
    ok = add_admin(uid)
    await message.answer("✅ افزوده شد." if ok else "ℹ️ قبلاً ادمین بود.")


# --- حذف ادمین --- #

@router.callback_query(F.data == "adm_del")
async def adm_del_prompt(call: types.CallbackQuery):
    await call.message.edit_text("🗑 chat_id ادمین را ارسال کنید:", reply_markup=admins_menu())


@router.message(F.text.regexp(r"^-?\d+$"))
async def adm_del_id(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    uid = int(message.text)
    ok = remove_admin(uid)
    await message.answer("🗑 حذف شد." if ok else "❗ یافت نشد یا حذف‌نشدنی.")


# --- لیست ادمین‌ها --- #

@router.callback_query(F.data == "adm_list")
async def adm_list(call: types.CallbackQuery):
    admins = list_admins()
    text = "👤 **ادمین‌ها:**\n\n"
    for a in admins:
        text += f"- `{a}`\n"
    await call.message.edit_text(text, reply_markup=admins_menu(), parse_mode="Markdown")


# ---------------------- تنظیم فاصله ---------------------- #

@router.callback_query(F.data == "menu_interval")
async def interval_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "⏱ مقدار فاصله را ارسال کنید:\nمثال:\n`5m`, `30m`, `2h`, `10`",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_main")]]
        )
    )


@router.message(F.text.regexp(r"^\d+[mh]?$"))
async def set_interval_value(message: types.Message):
    raw = message.text.lower()
    if raw.isdigit():
        seconds = int(raw) * 60
    elif raw.endswith("m"):
        seconds = int(raw[:-1]) * 60
    elif raw.endswith("h"):
        seconds = int(raw[:-1]) * 3600
    else:
        return await message.answer("❗ فرمت اشتباه است.")
    await set_interval(seconds)
    await message.answer(f"⏱ فاصله تنظیم شد: {seconds} ثانیه")


# ---------------------- پست‌های امروز ---------------------- #

@router.callback_query(F.data == "menu_posts")
async def posts_menu(call: types.CallbackQuery):
    posts = list_today_posts()
    if not posts:
        return await call.message.edit_text("📭 امروز هیچ پستی ثبت نشده.", reply_markup=admin_main_menu())

    lines = "📋 **پست‌های امروز:**\n\n"
    for p in posts:
        status = "🔔 فعال" if p["active"] else "❌ غیرفعال"
        lines += f"- ID `{p['message_id']}` → {status}\n"

    await call.message.edit_text(lines, parse_mode="Markdown", reply_markup=admin_main_menu())


# ---------------------- بازگشت ---------------------- #

@router.callback_query(F.data == "back_main")
async def back_main(call: types.CallbackQuery):
    await call.message.edit_text("🔧 **پنل مدیریت ربات**",
                                 reply_markup=admin_main_menu(),
                                 parse_mode="Markdown")


# ---------------------- خروج ---------------------- #

@router.callback_query(F.data == "menu_exit")
async def exit_admin(call: types.CallbackQuery):
    await call.message.edit_text("🔚 پنل بسته شد.")
