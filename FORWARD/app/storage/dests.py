import json
from pathlib import Path

DATA = Path("/tmp/fwd_dests.json")


# ---------------------- ابزارهای داخلی ---------------------- #

def _load():
    """
    خواندن لیست مقصدها از فایل.
    """
    if DATA.exists():
        try:
            return json.loads(DATA.read_text(encoding="utf-8"))
        except:
            return []
    return []


def _save(data):
    """
    ذخیره‌سازی لیست مقصدها.
    """
    try:
        DATA.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except:
        pass


# ---------------------- افزودن مقصد ---------------------- #

def add_destination(chat_id: int, title: str = "") -> bool:
    """
    افزودن یک کانال/گروه مقصد جدید.
    اگر قبلاً ثبت شده باشد → False برمی‌گرداند.
    """
    data = _load()

    for dest in data:
        if dest["chat_id"] == chat_id:
            return False  # تکراری

    data.append(
        {
            "chat_id": chat_id,
            "title": title
        }
    )

    _save(data)
    return True


# ---------------------- حذف مقصد ---------------------- #

def remove_destination(chat_id: int) -> bool:
    """
    حذف یک مقصد با chat_id.
    """
    data = _load()
    new_list = [d for d in data if d["chat_id"] != chat_id]

    if len(new_list) == len(data):
        return False  # چیزی حذف نشد

    _save(new_list)
    return True


# ---------------------- لیست مقصدها ---------------------- #

def list_destinations():
    """
    لیست کامل مقصدها را بازمی‌گرداند.
    """
    return _load()
