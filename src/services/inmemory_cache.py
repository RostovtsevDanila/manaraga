import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel


class CacheEntry(BaseModel):
    expires_at: datetime
    payload: Any


class InMemoryTTLCache:
    def __init__(self, ttl_seconds: int, dump_path: str | None = None):
        self.ttl = ttl_seconds
        self._store: dict[str, CacheEntry] = {}
        self._dump_path = dump_path

    def _is_valid(self, key: str) -> bool:
        entry = self._store.get(key)
        return bool(entry and entry.expires_at > datetime.now(UTC))

    def get(self, key: str) -> Any | None:
        if self._is_valid(key):
            return self._store[key].payload
        if key in self._store:
            del self._store[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = CacheEntry(
            expires_at=datetime.now(UTC) + timedelta(seconds=self.ttl),
            payload=value,
        )

    def dump_to_disk(self) -> None:
        if not self._dump_path:
            return

        serializable = {
            k: {
                'expires_at': v.expires_at.isoformat(),
                'payload': v.payload,
            }
            for k, v in self._store.items()
            if self._is_valid(k)
        }
        os.makedirs(os.path.dirname(self._dump_path), exist_ok=True)

        with open(self._dump_path, 'w', encoding='utf-8') as f:
            json.dump(serializable, f)

    def load_from_disk(self) -> None:
        if not self._dump_path or not os.path.exists(self._dump_path):
            return

        with open(self._dump_path, encoding='utf-8') as f:
            data = json.load(f)

        for k, v in data.items():
            exp = datetime.fromisoformat(v['expires_at'])
            if exp > datetime.now(UTC):
                self._store[k] = CacheEntry(expires_at=exp, payload=v['payload'])
