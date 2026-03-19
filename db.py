# db.py
import json
import os
import tempfile
from utils import hash_password, verify_password, gen_pid, gen_txid, now_iso

DB_FILE = "db.json"

def _atomic_write(path, data):
    dirn = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dirn, text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def init_db_if_missing():
    if not os.path.exists(DB_FILE):
        db = {"users": [], "products": [], "transactions": []}
        # default admin
        admin_pw = "admin123"
        db["users"].append({
            "username": "admin",
            "password": hash_password(admin_pw),
            "role": "admin",
            "created": now_iso()
        })
        # sample product
        db["products"].append({
            "id": gen_pid(),
            "name": "Paracetamol 500mg",
            "brand": "AcmePharma",
            "price": 30.0,
            "stock": 100,
            "expiry": "",
            "description": "Pain reliever / fever reducer"
        })
        _atomic_write(DB_FILE, db)

def load_db():
    init_db_if_missing()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    _atomic_write(DB_FILE, db)

# ---------------- User management ----------------
def get_user(username: str):
    db = load_db()
    for u in db.get("users", []):
        if u["username"] == username:
            return u
    return None

def create_user(username: str, password: str, role: str = "user") -> bool:
    db = load_db()
    if get_user(username):
        return False
    db.setdefault("users", []).append({
        "username": username,
        "password": hash_password(password),
        "role": role,
        "created": now_iso()
    })
    save_db(db)
    return True

def authenticate(username: str, password: str):
    u = get_user(username)
    if not u:
        return None
    if verify_password(u["password"], password):
        return u
    return None

# ---------------- Product management ----------------
def list_products() -> list:
    return load_db().get("products", [])

def get_product(pid: str):
    for p in list_products():
        if p.get("id") == pid:
            return p
    return None

def add_product(product: dict):
    db = load_db()
    if "id" not in product or not product["id"]:
        product["id"] = gen_pid()
    db.setdefault("products", []).append(product)
    save_db(db)
    return product["id"]

def update_product(pid: str, newdata: dict) -> bool:
    db = load_db()
    for p in db.get("products", []):
        if p.get("id") == pid:
            p.update(newdata)
            save_db(db)
            return True
    return False

def delete_product(pid: str) -> bool:
    db = load_db()
    before = len(db.get("products", []))
    db["products"] = [p for p in db.get("products", []) if p.get("id") != pid]
    save_db(db)
    return len(db.get("products", [])) < before

# ---------------- transactions ----------------
def record_transaction(items: list, total: float, customer: str = "Walk-in"):
    db = load_db()
    tx = {
        "tx_id": gen_txid(),
        "datetime": now_iso(),
        "items": items,
        "total": float(total),
        "customer": customer
    }
    db.setdefault("transactions", []).append(tx)
    save_db(db)
    return tx["tx_id"]

def list_transactions():
    return load_db().get("transactions", [])
