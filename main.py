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
async def start(message: types.Message):
    await message.answer("سلام! برای مدیریت ربات بنویسید: /admin")

async def main():
    bot, dp, _ = build_bot_and_dispatcher()

    # ------------------------
    # 🔥 ثبت ادمین‌ها
    # ------------------------
    bootstrap_admins(
        owner_id=SETTINGS.OWNER_ID,
        initial_admins=SETTINGS.ADMIN_IDS
    )
    print("ADMINS LOADED:", SETTINGS.OWNER_ID, SETTINGS.ADMIN_IDS)

    dp.include_router(router)
    dp.include_router(source_router)
    dp.include_router(admin_router)

    asyncio.create_task(start_scheduler(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
