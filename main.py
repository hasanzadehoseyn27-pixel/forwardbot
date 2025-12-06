import asyncio

from aiogram import types
from aiogram.filters import CommandStart
from aiogram import Router

from app.config import build_bot_and_dispatcher
from app.handlers.source import router as source_router
from app.handlers.admin_panel import router as admin_router
from app.handlers.scheduler import start_scheduler

router = Router()


# ------------------ /start ------------------ #

@router.message(CommandStart())
async def on_start(message: types.Message):
    await message.answer(
        "سلام 👋\n"
        "ربات فوروارد خودکار فعال است.\n\n"
        "اگر ادمین هستید، برای مدیریت دستور زیر را بزنید:\n"
        "`/admin`",
        parse_mode="Markdown"
    )


# ------------------ MAIN ------------------ #

async def main():
    bot, dp, _ = build_bot_and_dispatcher()

    # اضافه کردن روترهای اصلی
    dp.include_router(router)
    dp.include_router(source_router)
    dp.include_router(admin_router)

    # اجرای Scheduler در پس‌زمینه
    asyncio.create_task(start_scheduler(bot))

    print("🚀 Bot started… polling…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
