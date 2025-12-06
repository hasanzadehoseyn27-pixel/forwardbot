import json
from pathlib import Path
from datetime import date

DATA = Path("/tmp/fwd_posts.json")


# ---------------------- ابزارهای داخلی ---------------------- #

def _load():
    if DATA.exists():
        try:
            return json.loads(DATA.read_text(encoding="utf-8"))
        except:
            return []
    return []


def _save(data):
    try:
        DATA.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except:
        pass


# ---------------------- افزودن پست جدید ---------------------- #

def add_post(message_id: int, msg_date: str):
    data = _load()

    for p in data:
        if p["message_id"] == message_id and p["date"] == msg_date:
            return

    data.append(
        {
            "message_id": message_id,
            "date": msg_date,
            "active": True,
        }
    )

    _save(data)


# ---------------------- پست‌های امروز ---------------------- #

def list_today_posts():
    today = date.today().isoformat()
    data = _load()
    return [p for p in data if p["date"] == today]


# ---------------------- فعال/غیرفعال کردن پست ---------------------- #

def toggle_post(message_id: int):
    data = _load()

    for p in data:
        if p["message_id"] == message_id:
            p["active"] = not p.get("active", True)
            _save(data)
            return p["active"]

    return None
