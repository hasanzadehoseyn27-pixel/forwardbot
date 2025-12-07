import json
from pathlib import Path

# محل ذخیره‌سازی تنظیمات
SETTINGS_FILE = Path("storage/fwd_settings.json")


def _load():
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except:
            pass

    default = {
        "send_mode": "repeat",
        "interval": 1800  # 30 دقیقه
    }
    _save(default)
    return default


def _save(data):
    SETTINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def get_send_mode():
    return _load().get("send_mode", "repeat")


def set_send_mode(mode: str):
    data = _load()
    data["send_mode"] = mode
    _save(data)


def get_interval():
    return int(_load().get("interval", 1800))


def set_interval_value(seconds: int):
    data = _load()
    data["interval"] = int(seconds)
    _save(data)
