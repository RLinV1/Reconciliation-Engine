import hashlib
import json
import time

from httpx import delete

class Cache:
    def __init__(self):  # 1 hour 
        self._store = {}

    def _make_key(self, data: dict) -> str:
        # make the key based on the content of the data
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def get(self, data: dict):
        key = self._make_key(data)
        if key in self._store:
            value = self._store[key]
            return value
        return None
    
    def delete(self, data: dict):
        key = self._make_key(data)
        if key in self._store:
            del self._store[key]

    def set(self, data: dict, value: dict):
        key = self._make_key(data)
        self._store[key] = value

cache = Cache()