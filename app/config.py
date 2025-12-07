import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

load_dotenv()  # بارگذاری متغیرهای .env


@dataclass
class Settings:
    # ---------------------- تنظیمات اصلی ---------------------- #

    BOT_TOKEN: str = field(default_factory=lambda: (os.getenv("BOT_TOKEN") or "").strip())

    OWNER_ID: int = field(default_factory=lambda: int(os.getenv("OWNER_ID", "0") or "0"))

    ADMIN_IDS: set[int] = field(default_factory=lambda: {
        int(x)
        for x in (os.getenv("ADMIN_IDS") or "").replace(" ", "").split(",")
        if x
    })

    SOURCE_CHANNEL_ID: int = field(default_factory=lambda: int(os.getenv("SOURCE_CHANNEL_ID", "0") or "0"))

    PROXY_URL: str = field(default_factory=lambda: (os.getenv("PROXY_URL") or "").strip())

    # ---------------------- تنظیمات ارسال ---------------------- #
    # حالت ارسال:
    # - repeat  → ارسال دوره‌ای توسط Scheduler
    # - once    → ارسال فوری توسط source.py
    SEND_MODE: str = "repeat"    # مقدار اولیه

    # فاصله پیش‌فرض در حالت ارسال دوره‌ای (ثانیه)
    DEFAULT_INTERVAL: int = 60 * 30


# ایجاد شی تنظیمات
SETTINGS = Settings()


def build_bot_and_dispatcher():
    """
    ساخت Bot و Dispatcher.
    مقدار برگشتی همیشه:
        bot, dp, SETTINGS
    """
    if not SETTINGS.BOT_TOKEN:
        raise RuntimeError("❗ BOT_TOKEN در فایل .env تنظیم نشده است.")

    # Proxy (در صورت نیاز)
    session = None
    if SETTINGS.PROXY_URL:
        session = AiohttpSession(proxy=SETTINGS.PROXY_URL)

    # ساخت Bot و Dispatcher
    bot = Bot(token=SETTINGS.BOT_TOKEN, session=session)
    dp = Dispatcher()

    print("[CONFIG] Bot & Dispatcher created successfully.")

    return bot, dp, SETTINGS
