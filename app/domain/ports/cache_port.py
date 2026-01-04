"""Cache port interface.

This port defines the contract for cache operations, following the
Dependency Inversion Principle. Implementations can be Redis, in-memory,
or any other caching solution.
"""
from abc import ABC, abstractmethod
from typing import Optional, Any


class CachePort(ABC):
    """
    Port for cache operations.
    
    This interface allows the application layer to use caching without
    depending on specific cache implementations (Redis, Memcached, etc.).
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value if found, None otherwise.
        """
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Set a value in cache with optional TTL.
        
        Args:
            key: Cache key.
            value: Value to cache (must be serializable).
            ttl_seconds: Time to live in seconds. If None, no expiration.
            
        Returns:
            True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key to delete.
            
        Returns:
            True if deleted, False if key didn't exist.
        """
        pass
    
    @abstractmethod
    async def increment(
        self,
        key: str,
        amount: int = 1,
        ttl_seconds: Optional[int] = None
    ) -> int:
        """
        Increment a numeric value in cache (atomic operation).
        
        If the key doesn't exist, it will be created with the increment value.
        This is useful for rate limiting counters.
        
        Args:
            key: Cache key.
            amount: Amount to increment (default: 1).
            ttl_seconds: Time to live in seconds. If None, no expiration.
            
        Returns:
            The new value after increment.
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.
        
        Args:
            key: Cache key to check.
            
        Returns:
            True if key exists, False otherwise.
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the cache connection.
        
        This should be called during application shutdown.
        """
        pass

