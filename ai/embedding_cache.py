import hashlib
import json
import threading
from pathlib import Path

_cache: dict = {}
_dirty: bool = False
_lock = threading.Lock()


def load(path: Path) -> None:
    global _cache
    if path.exists():
        try:
            _cache = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            _cache = {}


def cache_key(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def get(key: str) -> list | None:
    return _cache.get(key)


def put(key: str, embedding: list) -> None:
    global _dirty
    with _lock:
        _cache[key] = embedding
        _dirty = True


def flush(path: Path) -> None:
    global _dirty
    with _lock:
        if _dirty:
            path.write_text(json.dumps(_cache), encoding="utf-8")
            _dirty = False
