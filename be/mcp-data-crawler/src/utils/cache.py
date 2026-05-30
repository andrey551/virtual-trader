import time
from typing import Any, Dict, Optional

class MemoryCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """
        Store a value in cache with a specific Time-To-Live (TTL) in seconds.
        """
        self._cache[key] = {
            "value": value,
            "expire_at": time.time() + ttl_seconds
        }

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache if it exists and has not expired.
        """
        if key not in self._cache:
            return None
        item = self._cache[key]
        if time.time() > item["expire_at"]:
            del self._cache[key]  # Clean up expired item
            return None
        return item["value"]

    def clear(self) -> None:
        """
        Clear all cache items.
        """
        self._cache.clear()

# Global cache instance to share across tools
global_cache = MemoryCache()
