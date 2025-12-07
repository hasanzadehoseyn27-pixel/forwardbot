import asyncio
import os
from aiohttp import web

from aiogram import Router, types
from aiogram.filters import CommandStart

from app.config import build_bot_and_dispatcher, SETTINGS
from app.handlers.source import router as source_router
from app.handlers.admin_panel import (
    router as admin_router,
    admin_keyboard,
    is_admin,
)
from app.handlers.scheduler import start_scheduler


async def main():
    # ---- ساخت Bot و Dispatcher صحیح ---- #
    result = build_bot_and_dispatcher()

    # پشتیبانی از حالت‌های مختلف مقدار خروجی تابع
    if isinstance(result, tuple):
        if len(result) == 3:
            bot, dp, _settings = result
        else:
            bot, dp = result[0], result[1]
    else:
        bot, dp = result

    # ---- هندلر /start ---- #
    start_router = Router()

    @start_router.message(CommandStart())
    async def cmd_start(message: types.Message):
        if is_admin(message.from_user.id):
            await message.answer(
                "سلام 👋\nبه پنل مدیریت خوش آمدید:",
                reply_markup=admin_keyboard(),
            )
        else:
            await message.answer("⛔ این ربات فقط مخصوص مدیران است.")

    # ثبت روترها
    dp.include_router(start_router)
    dp.include_router(source_router)
    dp.include_router(admin_router)

    # ---- Scheduler فقط در پس‌زمینه ---- #
    asyncio.create_task(start_scheduler(bot))
    print("[MAIN] Scheduler started in background.")

    # ---- وب‌سرور برای healthcheck ---- #
    async def healthcheck(_):
        return web.Response(text="Bot is running!")

    app = web.Application()
    app.router.add_get("/", healthcheck)

    port = int(os.environ.get("PORT", "8080"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()

    print(f"[MAIN] HTTP healthcheck server running on port {port}")

    # ---- استارت Polling ---- #
    try:
        print("[MAIN] Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"[MAIN] Polling crashed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
