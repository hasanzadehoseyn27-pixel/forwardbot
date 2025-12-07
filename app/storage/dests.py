import json
from pathlib import Path

# مسیر صحیح و پایدار داخل پروژه
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
    """نوشتن تغییرات در فایل"""
    try:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except:
        pass


# ---------------------- افزودن مقصد ---------------------- #

def add_destination(chat_id: int, title: str = "") -> bool:
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
    return _load()
# ششششش