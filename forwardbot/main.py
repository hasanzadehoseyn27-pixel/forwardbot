import asyncio

from aiogram import Router, types
from aiogram.filters import CommandStart

from app.config import build_bot_and_dispatcher, SETTINGS

router = Router()


@router.message(CommandStart())
async def on_start(message: types.Message):
    text = (
        "سلام 👋\n"
        "این ربات فورواردِ روزانه است (نسخه‌ی تست).\n\n"
        f"🔹 شناسه کانال مبدا: {SETTINGS.SOURCE_CHANNEL_ID}\n"
        "بعداً منطق فوروارد خودکار را اضافه می‌کنیم."
    )
    await message.answer(text)


async def main():
    bot, dp, _ = build_bot_and_dispatcher()
    dp.include_router(router)

    print("Bot is starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
