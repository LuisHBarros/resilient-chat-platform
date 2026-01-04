"""Redis cache client implementation.

This module provides a Redis-based implementation of the CachePort interface.
It uses aioredis (via redis[asyncio]) for async Redis operations.
"""
from typing import Optional, Any
import json
import logging
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
from app.domain.ports.cache_port import CachePort
from app.infrastructure.config.settings import settings
from app.infrastructure.exceptions import InfrastructureException

logger = logging.getLogger(__name__)


class RedisConnectionError(InfrastructureException):
    """Raised when Redis connection fails."""
    pass


class RedisCacheClient(CachePort):
    """
    Redis implementation of CachePort.
    
    This client provides async Redis operations for caching and rate limiting.
    It automatically handles connection pooling and error handling.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis client.
        
        Args:
            redis_url: Redis connection URL. If None, uses settings.redis_url.
            
        Raises:
            RedisConnectionError: If Redis URL is not configured.
        """
        self.redis_url = redis_url or settings.redis_url
        if not self.redis_url:
            raise RedisConnectionError(
                "Redis URL is not configured. Set REDIS_URL environment variable."
            )
        
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._connected = False
    
    async def _ensure_connected(self) -> Redis:
        """
        Ensure Redis connection is established.
        
        Returns:
            Redis client instance.
            
        Raises:
            RedisConnectionError: If connection fails.
        """
        if self._client and self._connected:
            return self._client
        
        try:
            # Create connection pool if not exists
            if self._pool is None:
                self._pool = ConnectionPool.from_url(
                    self.redis_url,
                    decode_responses=False,  # We'll handle encoding ourselves
                    max_connections=10,
                    retry_on_timeout=True,
                )
            
            # Create Redis client
            if self._client is None:
                self._client = Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.debug("Redis connection established")
            
            return self._client
            
        except RedisConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            self._connected = False
            raise RedisConnectionError(f"Failed to connect to Redis: {e}")
        except Exception as e:
            logger.error(f"Unexpected Redis error: {e}")
            self._connected = False
            raise RedisConnectionError(f"Unexpected Redis error: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from Redis cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value if found, None otherwise.
        """
        try:
            client = await self._ensure_connected()
            value = await client.get(key)
            
            if value is None:
                return None
            
            # Deserialize JSON
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If not JSON, return as string
                return value.decode('utf-8')
                
        except RedisError as e:
            logger.warning(f"Redis get error for key '{key}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting key '{key}': {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Set a value in Redis cache with optional TTL.
        
        Args:
            key: Cache key.
            value: Value to cache (must be JSON serializable).
            ttl_seconds: Time to live in seconds. If None, no expiration.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            client = await self._ensure_connected()
            
            # Serialize value to JSON
            if isinstance(value, (str, bytes)):
                # String values: encode directly
                serialized = value.encode('utf-8') if isinstance(value, str) else value
            else:
                # Complex objects: serialize to JSON
                serialized = json.dumps(value).encode('utf-8')
            
            # Set with optional TTL
            if ttl_seconds:
                result = await client.setex(key, ttl_seconds, serialized)
            else:
                result = await client.set(key, serialized)
            
            return bool(result)
            
        except (RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Redis set error for key '{key}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis cache.
        
        Args:
            key: Cache key to delete.
            
        Returns:
            True if deleted, False if key didn't exist.
        """
        try:
            client = await self._ensure_connected()
            result = await client.delete(key)
            return bool(result)
            
        except RedisError as e:
            logger.warning(f"Redis delete error for key '{key}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting key '{key}': {e}")
            return False
    
    async def increment(
        self,
        key: str,
        amount: int = 1,
        ttl_seconds: Optional[int] = None
    ) -> int:
        """
        Increment a numeric value in Redis (atomic operation).
        
        If the key doesn't exist, it will be created with the increment value.
        This is useful for rate limiting counters.
        
        Args:
            key: Cache key.
            amount: Amount to increment (default: 1).
            ttl_seconds: Time to live in seconds. If None, no expiration.
                        If key is new, TTL will be set.
            
        Returns:
            The new value after increment.
        """
        try:
            client = await self._ensure_connected()
            
            # Use pipeline for atomic operation
            pipe = client.pipeline()
            pipe.incrby(key, amount)
            
            # Set TTL if specified and key is new
            if ttl_seconds:
                # Check if key exists first
                exists = await client.exists(key)
                if not exists:
                    # Key is new, set TTL
                    pipe.expire(key, ttl_seconds)
                else:
                    # Key exists, only set TTL if it doesn't have one
                    current_ttl = await client.ttl(key)
                    if current_ttl == -1:  # No expiration set
                        pipe.expire(key, ttl_seconds)
            
            results = await pipe.execute()
            new_value = results[0]
            
            return int(new_value)
            
        except RedisError as e:
            logger.warning(f"Redis increment error for key '{key}': {e}")
            # Return a safe default (allow request through)
            return 1
        except Exception as e:
            logger.error(f"Unexpected error incrementing key '{key}': {e}")
            return 1
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            key: Cache key to check.
            
        Returns:
            True if key exists, False otherwise.
        """
        try:
            client = await self._ensure_connected()
            result = await client.exists(key)
            return bool(result)
            
        except RedisError as e:
            logger.warning(f"Redis exists error for key '{key}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking key '{key}': {e}")
            return False
    
    async def close(self) -> None:
        """
        Close the Redis connection.
        
        This should be called during application shutdown.
        """
        try:
            if self._client:
                await self._client.close()
                self._connected = False
                logger.debug("Redis connection closed")
            
            if self._pool:
                await self._pool.disconnect()
                self._pool = None
                
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")


# Global cache instance (singleton)
_cache_client: Optional[RedisCacheClient] = None


def get_cache_client() -> Optional[CachePort]:
    """
    Get the global cache client instance.
    
    Returns:
        CachePort instance if Redis is configured, None otherwise.
    """
    global _cache_client
    
    if not settings.redis_url:
        logger.debug("Redis URL not configured, cache disabled")
        return None
    
    if _cache_client is None:
        try:
            _cache_client = RedisCacheClient()
        except RedisConnectionError as e:
            logger.warning(f"Failed to initialize Redis cache: {e}")
            return None
    
    return _cache_client


async def close_cache_client() -> None:
    """Close the global cache client (for shutdown)."""
    global _cache_client
    if _cache_client:
        await _cache_client.close()
        _cache_client = None

