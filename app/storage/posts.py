import json
from pathlib import Path
from datetime import date

# مسیر امن و قابل نوشتن در لیارا
BASE = Path("storage")
BASE.mkdir(parents=True, exist_ok=True)

DATA = BASE / "fwd_posts.json"


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
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except:
        pass


# ---------------------- افزودن پست ---------------------- #

def add_post(message_id: int, msg_date: str, ad_number: int | None):
    data = _load()

    # جلوگیری از تکرار
    for p in data:
        if p["message_id"] == message_id:
            return

    data.append({
        "message_id": message_id,
        "ad_number": ad_number,
        "date": msg_date,
        "active": True,
        "sent_once": False
    })

    _save(data)


# ---------------------- لیست پست‌های امروز ---------------------- #

def list_today_posts():
    today = date.today().isoformat()
    return [p for p in _load() if p["date"] == today]


# ---------------------- فعال / غیرفعال کردن ---------------------- #

def toggle_post(message_id: int):
    data = _load()
    for p in data:
        if p["message_id"] == message_id:
            p["active"] = not p.get("active", True)
            _save(data)
            return p["active"]
    return None


# ---------------------- ارسال یکبار ---------------------- #

def mark_sent_once(message_id: int):
    data = _load()
    for p in data:
        if p["message_id"] == message_id:
            p["sent_once"] = True
            _save(data)
            return True
    return False


def is_sent_once(message_id: int) -> bool:
    for p in _load():
        if p["message_id"] == message_id:
            return p.get("sent_once", False)
    return False
