import os
import hashlib
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path

class QueryCache:
    """Simple file-based cache for query results to reduce API calls."""

    def __init__(self, cache_dir: str = ".cache", ttl_seconds: int = 3600):  # 1 hour default
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _get_cache_key(self, query: str, context_hash: str = "") -> str:
        """Generate a unique cache key for the query."""
        content = f"{query}:{context_hash}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{key}.json"

    def get(self, query: str, context_hash: str = "") -> Optional[Dict[str, Any]]:
        """Retrieve cached result if it exists and hasn't expired."""
        key = self._get_cache_key(query, context_hash)
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)

            # Check if cache has expired
            if time.time() - cached_data['timestamp'] > self.ttl_seconds:
                cache_path.unlink()  # Remove expired cache
                return None

            return cached_data['result']

        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return None

    def set(self, query: str, result: Dict[str, Any], context_hash: str = ""):
        """Cache a query result."""
        key = self._get_cache_key(query, context_hash)
        cache_path = self._get_cache_path(key)

        cached_data = {
            'timestamp': time.time(),
            'query': query,
            'context_hash': context_hash,
            'result': result
        }

        try:
            with open(cache_path, 'w') as f:
                json.dump(cached_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to cache result: {e}")

    def clear(self):
        """Clear all cached results."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

    def clear_expired(self):
        """Remove expired cache entries."""
        current_time = time.time()
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)

                if current_time - cached_data['timestamp'] > self.ttl_seconds:
                    cache_file.unlink()
            except Exception:
                # Remove corrupted cache files
                cache_file.unlink()
