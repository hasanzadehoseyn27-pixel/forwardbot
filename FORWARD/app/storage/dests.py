import json
from pathlib import Path

# مسیر قابل نوشتن در لیارا
BASE = Path("/var/www/data")
BASE.mkdir(parents=True, exist_ok=True)

DATA = BASE / "fwd_dests.json"


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


def add_destination(chat_id: int, title: str = "") -> bool:
    data = _load()
    for d in data:
        if d["chat_id"] == chat_id:
            return False
    data.append({"chat_id": chat_id, "title": title or "گروه"})
    _save(data)
    return True


def remove_destination(chat_id: int):
    data = _load()
    new_data = [d for d in data if d["chat_id"] != chat_id]
    if len(new_data) == len(data):
        return False
    _save(new_data)
    return True


def list_destinations():
    return _load()
