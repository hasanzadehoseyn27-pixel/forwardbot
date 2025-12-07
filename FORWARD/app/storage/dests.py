import json
from pathlib import Path

# ذخیره امن و پایدار در لیارا
BASE = Path("/data")
BASE.mkdir(exist_ok=True)

DATA = BASE / "fwd_dests.json"


def _load():
    """خواندن لیست مقصدها."""
    if DATA.exists():
        try:
            return json.loads(DATA.read_text(encoding="utf-8"))
        except:
            return []
    return []


def _save(data):
    """ذخیره‌سازی مقصدها."""
    try:
        DATA.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except:
        pass


def add_destination(chat_id: int, title: str = "") -> bool:
    """افزودن مقصد جدید"""
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


def remove_destination(chat_id: int) -> bool:
    """حذف مقصد"""
    data = _load()
    new_data = [d for d in data if d["chat_id"] != chat_id]

    if len(new_data) == len(data):
        return False

    _save(new_data)
    return True


def list_destinations():
    """لیست مقصدها"""
    return _load()
