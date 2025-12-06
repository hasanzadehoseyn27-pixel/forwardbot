import asyncio
from aiogram import types, Router
from aiogram.filters import CommandStart

from app.config import build_bot_and_dispatcher, SETTINGS
from app.storage.admins import bootstrap_admins
from app.handlers.source import router as source_router
from app.handlers.admin_panel import router as admin_router
from app.handlers.scheduler import start_scheduler


router = Router()


@router.message(CommandStart())
async def on_start(message: types.Message):
    await message.answer("سلام 👋\nربات فعال است.\nبرای مدیریت: /admin")


async def main():
    bot, dp, _ = build_bot_and_dispatcher()

    # ----------------------- بسیار مهم -----------------------
    # لود کردن OWNER_ID و ADMIN_IDS از .env
    bootstrap_admins(
        owner_id=SETTINGS.OWNER_ID,
        initial_admins=SETTINGS.ADMIN_IDS
    )
    # ----------------------------------------------------------

    dp.include_router(router)
    dp.include_router(source_router)
    dp.include_router(admin_router)

    asyncio.create_task(start_scheduler(bot))

    print("Bot is running…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
