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

def add_post(message_id: int, msg_date: str, ad_number: int | None):
    """
    یک پست جدید با فیلدهای:
    - message_id
    - ad_number (شماره آگهی واقعی)
    - date
    - active
    - sent_once
    ذخیره می‌شود.
    """

    data = _load()

    # اگر پست تکراری باشد، دست نمی‌زنیم
    for p in data:
        if p["message_id"] == message_id and p["date"] == msg_date:
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


# ---------------------- ثبت ارسال یکبار ---------------------- #

def mark_sent_once(message_id: int):
    """
    وقتی پست در حالت one-time ارسال شد،
    sent_once = True می‌شود.
    """

    data = _load()

    for p in data:
        if p["message_id"] == message_id:
            p["sent_once"] = True
            _save(data)
            return True

    return False


# ---------------------- بررسی وضعیت ارسال یکبار ---------------------- #

def is_sent_once(message_id: int) -> bool:
    """
    آیا این پست قبلاً یکبار ارسال شده؟
    """

    data = _load()

    for p in data:
        if p["message_id"] == message_id:
            return p.get("sent_once", False)

    return False
