import json
from pathlib import Path

DATA = Path("/tmp/forward_admins.json")

# مقدار Owner توسط bootstrap_admins مقداردهی می‌شود
OWNER_ID: int = 0


# ---------------------- ابزارهای داخلی ---------------------- #

def _load() -> set[int]:
    """
    خواندن لیست ادمین‌ها از فایل.
    فایل JSON باید شامل یک لیست از اعداد باشد.
    """
    if DATA.exists():
        try:
            raw = json.loads(DATA.read_text(encoding="utf-8"))
            return {int(x) for x in raw}
        except:
            return set()
    return set()


def _save(admins: set[int]):
    """
    ذخیره‌سازی لیست ادمین‌ها روی دیسک.
    """
    try:
        DATA.write_text(
            json.dumps(sorted(list(admins)), ensure_ascii=False),
            encoding="utf-8"
        )
    except:
        pass


# ---------------------- آماده‌سازی اولیه ---------------------- #

def bootstrap_admins(owner_id: int, initial_admins: set[int]):
    """
    در ابتدای اجرای ربات فراخوانی می‌شود.
    - Owner را تنظیم می‌کند
    - ادمین‌های اولیه (از .env) را اضافه می‌کند
    - فایل قدیمی را بارگذاری می‌کند
    """
    global OWNER_ID

    OWNER_ID = int(owner_id)

    admins = _load()
    admins.update(initial_admins)
    admins.add(OWNER_ID)  # Owner همیشه ادمین است

    _save(admins)


# ---------------------- API عمومی ---------------------- #

def list_admins() -> list[int]:
    """
    لیست کامل ادمین‌ها.
    """
    admins = _load()
    return sorted(list(admins))


def is_admin(uid: int) -> bool:
    """
    بررسی اینکه آیا uid ادمین است یا خیر.
    """
    admins = _load()
    return uid in admins or uid == OWNER_ID


def add_admin(uid: int) -> bool:
    """
    اضافه‌کردن ادمین جدید.
    خروجی:
    - True → اضافه شد
    - False → از قبل وجود داشته
    """
    uid = int(uid)
    admins = _load()

    if uid in admins:
        return False

    admins.add(uid)
    _save(admins)
    return True


def remove_admin(uid: int) -> bool:
    """
    حذف ادمین.
    Owner قابل حذف نیست.
    """
    uid = int(uid)

    if uid == OWNER_ID:
        return False  # Owner حذف نمی‌شود

    admins = _load()

    if uid not in admins:
        return False

    admins.remove(uid)
    _save(admins)
    return True
