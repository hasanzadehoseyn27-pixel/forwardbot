import json
from pathlib import Path
from datetime import date

# مسیر درست و پایدار برای لیارا
BASE = Path("/data")
BASE.mkdir(exist_ok=True)

DATA = BASE / "fwd_posts.json"


# ---------------------- ابزارهای داخلی ---------------------- #

def _load():
    """خواندن کل لیست پست‌ها از فایل JSON."""
    if DATA.exists():
        try:
            return json.loads(DATA.read_text(encoding="utf-8"))
        except:
            return []
    return []


def _save(data):
    """ذخیره لیست پست‌ها."""
    try:
        DATA.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except:
        pass


# ---------------------- افزودن پست جدید ---------------------- #

def add_post(message_id: int, msg_date: str):
    """
    افزودن پست جدید.
    message_id یکتا باشد.
    """
    data = _load()

    for p in data:
        if p["message_id"] == message_id:
            return

    data.append(
        {
            "message_id": message_id,
            "date": msg_date,
            "active": True,
            "sent": False,
        }
    )

    _save(data)


# ---------------------- لیست‌ها ---------------------- #

def list_all_posts():
    return _load()


def list_inactive_posts():
    data = _load()
    return [p for p in data if not p.get("active", True)]


def list_active_posts():
    data = _load()
    return [p for p in data if p.get("active", True)]


# ---------------------- وضعیت active ---------------------- #

def toggle_post(message_id: int):
    data = _load()

    for p in data:
        if p["message_id"] == message_id:
            p["active"] = not p.get("active", True)
            _save(data)
            return p["active"]

    return None


# ---------------------- وضعیت sent ---------------------- #

def toggle_sent(message_id: int):
    data = _load()

    for p in data:
        if p["message_id"] == message_id:
            p["sent"] = not p.get("sent", False)
            _save(data)
            return p["sent"]

    return None


def list_unsent_posts():
    data = _load()
    return [p for p in data if not p.get("sent", False)]
