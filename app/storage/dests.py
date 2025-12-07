import json
from pathlib import Path

# مسیر ذخیره‌سازی (در صورت نیاز قابل تغییر به data/dests.json)
DATA = Path("/tmp/fwd_dests.json")


# ---------------------- ابزارهای فایل ---------------------- #

def _load():
    """
    خواندن فایل مقصدها.
    """
    if DATA.exists():
        try:
            return json.loads(DATA.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save(data):
    """
    ذخیره‌سازی در فایل JSON.
    """
    try:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ---------------------- افزودن مقصد ---------------------- #

def add_destination(chat_id: int, title: str = "") -> bool:
    """
    افزودن مقصد جدید:
    - chat_id
    - title (نام گروه)
    
    اگر آیدی تکراری باشد → False
    """

    data = _load()

    # جلوگیری از تکرار
    for d in data:
        if d["chat_id"] == chat_id:
            return False

    data.append({
        "chat_id": chat_id,
        "title": title or "گروه"
    })

    _save(data)
    return True


# ---------------------- حذف مقصد ---------------------- #

def remove_destination(chat_id: int) -> bool:
    """
    حذف یک مقصد با chat_id.
    """

    data = _load()
    new_data = [d for d in data if d["chat_id"] != chat_id]

    if len(new_data) == len(data):
        return False  # چیزی حذف نشد

    _save(new_data)
    return True


# ---------------------- لیست مقصدها ---------------------- #

def list_destinations():
    """
    لیست مقصدها را برمی‌گرداند.

    خروجی:
    [
        {"chat_id": -10012345, "title": "گروه تست"},
        ...
    ]
    """

    return _load()
