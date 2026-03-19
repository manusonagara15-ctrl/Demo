# utils.py
import os
import hashlib
import binascii
import uuid
from datetime import datetime

# ---------------- ID & time helpers ----------------
def gen_pid():
    return "P" + uuid.uuid4().hex[:8].upper()

def gen_txid():
    return "T" + uuid.uuid4().hex[:10].upper()

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

# ---------------- Password hashing (PBKDF2) ----------------
def hash_password(password: str, iterations: int = 160_000) -> dict:
    """
    Returns a dict with salt, hash and iterations. Store this dict in DB.
    """
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return {
        "algo": "pbkdf2_sha256",
        "iters": iterations,
        "salt": binascii.hexlify(salt).decode(),
        "hash": binascii.hexlify(dk).decode()
    }

def verify_password(stored: dict, password: str) -> bool:
    iters = int(stored.get("iters", 160_000))
    salt = binascii.unhexlify(stored["salt"].encode())
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
    return binascii.hexlify(dk).decode() == stored["hash"]
