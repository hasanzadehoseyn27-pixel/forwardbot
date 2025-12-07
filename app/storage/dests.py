import json
from pathlib import Path

# مسیر پایدار داخل پروژه
BASE = Path("data")
BASE.mkdir(parents=True, exist_ok=True)

DATA = BASE / "fwd_dests.json"


# ---------------------- ابزارهای فایل ---------------------- #

def _load():
    """خواندن لیست مقصدها از فایل"""
    if DATA.exists():
        try:
            return json.loads(DATA.read_text(encoding="utf-8"))
        except:
            return []
    return []


def _save(data):
    """ذخیره لیست مقصدها در فایل"""
    try:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except:
        pass


# ---------------------- افزودن مقصد ---------------------- #

def add_destination(chat_id: int, title: str = "") -> bool:
    """
    اگر chat_id قبلاً وجود داشته باشد → False
    در غیر این صورت اضافه می‌شود.
    """
    data = _load()

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
    data = _load()
    new_data = [d for d in data if d["chat_id"] != chat_id]

    if len(new_data) == len(data):
        return False

    _save(new_data)
    return True


# ---------------------- لیست مقصدها ---------------------- #

def list_destinations():
    """خروجی مثل: [{'chat_id': -100123, 'title': 'فلان گروه'}]"""
    return _load()
