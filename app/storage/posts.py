import json
from pathlib import Path
from datetime import date

DATA = Path("/tmp/fwd_posts.json")


# ---------------------- ابزارهای داخلی ---------------------- #

def _load():
    """
    خواندن کل لیست پست‌ها از فایل.
    """
    if DATA.exists():
        try:
            return json.loads(DATA.read_text(encoding="utf-8"))
        except:
            return []
    return []


def _save(data):
    """
    ذخیره کل لیست پست‌ها در فایل.
    """
    try:
        DATA.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except:
        pass


# ---------------------- افزودن پست جدید ---------------------- #

def add_post(message_id: int, msg_date: str):
    """
    افزودن پست جدید به لیست.
    اگر پست برای امروز تکراری باشد، اضافه نمی‌شود.
    """
    data = _load()

    # جلوگیری از ثبت تکراری
    for p in data:
        if p["message_id"] == message_id and p["date"] == msg_date:
            return  # همین پست قبلاً ثبت شده است!

    data.append(
        {
            "message_id": message_id,
            "date": msg_date,
            "active": True,  # پیش‌فرض فعال
        }
    )

    _save(data)


# ---------------------- گرفتن پست‌های امروز ---------------------- #

def list_today_posts():
    """
    تمام پست‌هایی که تاریخشان برابر با امروز است را بازمی‌گرداند.
    """
    today = date.today().isoformat()
    data = _load()
    return [p for p in data if p["date"] == today]


# ---------------------- تغییر وضعیت active / inactive ---------------------- #

def set_post_active(message_id: int, active: bool):
    """
    تغییر وضعیت یک پست خاص به فعال یا غیرفعال.
    """
    data = _load()

    for p in data:
        if p["message_id"] == message_id:
            p["active"] = active
            break

    _save(data)
