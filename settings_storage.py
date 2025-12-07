import json
from pathlib import Path

# فایل تنظیمات در مسیر پایدار
# SETTINGS_FILE = Path("/tmp/fwd_settings.json")
# SETTINGS_FILE = Path("data/fwd_settings.json")
SETTINGS_FILE = Path("/var/www/data/fwd_settings.json")



# ---------------------- ابزارهای داخلی ---------------------- #

def _load():
    """
    تنظیمات را از فایل بخوان.
    اگر فایل نبود، مقدار پیش‌فرض بساز.
    """
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except:
            pass

    # مقدارهای پیش‌فرض
    default = {
        "send_mode": "repeat",    # repeat or once
        "interval": 1800          # 30 minutes
    }
    _save(default)
    return default


def _save(data):
    """ذخیره تنظیمات در فایل JSON"""
    try:
        SETTINGS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except:
        pass


# ---------------------- حالت ارسال ---------------------- #

def get_send_mode() -> str:
    """send_mode را برگردان: repeat یا once"""
    data = _load()
    return data.get("send_mode", "repeat")


def set_send_mode(mode: str):
    """حالت جدید ارسال را ذخیره کن"""
    data = _load()
    data["send_mode"] = mode
    _save(data)


# ---------------------- فاصله ارسال ---------------------- #

def get_interval() -> int:
    """مقدار فاصله ارسال را برگردان (ثانیه)"""
    data = _load()
    return int(data.get("interval", 1800))


def set_interval_value(seconds: int):
    """تنظیم مقدار فاصله ارسال"""
    data = _load()
    data["interval"] = int(seconds)
    _save(data)
