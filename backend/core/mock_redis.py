"""
In-memory mock Redis client for development/testing without needing Redis server.
This implements the minimal Redis async interface needed for SessionManager.
"""

import json
from typing import Optional
from datetime import datetime, timedelta


class MockRedisClient:
    """Mock async Redis client for development without a Redis server"""
    
    def __init__(self):
        self._storage = {}  # key -> (value, expiry_time)
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key"""
        if key in self._storage:
            value, expiry_time = self._storage[key]
            if expiry_time is None or datetime.now() < expiry_time:
                return value
            else:
                # Expired, delete it
                del self._storage[key]
                return None
        return None
    
    async def set(self, key: str, value: str) -> bool:
        """Set a value with optional expiry"""
        self._storage[key] = (value, None)
        return True
    
    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set a value with TTL (time to live in seconds)"""
        expiry_time = datetime.now() + timedelta(seconds=ttl)
        self._storage[key] = (value, expiry_time)
        return True
    
    async def expire(self, key: str, ttl: int) -> int:
        """Set expiry time for an existing key"""
        if key in self._storage:
            value, _ = self._storage[key]
            expiry_time = datetime.now() + timedelta(seconds=ttl)
            self._storage[key] = (value, expiry_time)
            return 1
        return 0
    
    async def delete(self, key: str) -> int:
        """Delete a key, return 1 if deleted, 0 if not found"""
        if key in self._storage:
            del self._storage[key]
            return 1
        return 0
    
    async def exists(self, key: str) -> int:
        """Check if key exists"""
        if key in self._storage:
            value, expiry_time = self._storage[key]
            if expiry_time is None or datetime.now() < expiry_time:
                return 1
        return 0
    
    async def keys(self, pattern: str = "*") -> list:
        """Get all keys matching pattern (simplified - only supports *)"""
        return list(self._storage.keys())
    
    async def close(self):
        """Close connection (no-op for mock)"""
        pass
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# For development, we can use this mock instead of real Redis
# Just replace the Redis import in main.py with this
