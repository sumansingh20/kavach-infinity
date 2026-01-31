"""
KAVACH-INFINITY Redis Client
Async Redis connection for caching and pub/sub
"""

import redis.asyncio as redis
from typing import Optional, Any
import json
import structlog

from app.config import settings

logger = structlog.get_logger()

# Redis client instance
redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD,
            encoding="utf-8",
            decode_responses=True
        )
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error("Redis connection failed", error=str(e))
        raise


async def close_redis() -> None:
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


async def get_redis() -> redis.Redis:
    """Get Redis client instance"""
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client


class RedisCache:
    """Redis caching utilities"""
    
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            client = await get_redis()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("Redis get failed", key=key, error=str(e))
            return None
    
    @staticmethod
    async def set(key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """Set cached value with expiration"""
        try:
            client = await get_redis()
            await client.setex(key, expire_seconds, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.error("Redis set failed", key=key, error=str(e))
            return False
    
    @staticmethod
    async def delete(key: str) -> bool:
        """Delete cached value"""
        try:
            client = await get_redis()
            await client.delete(key)
            return True
        except Exception as e:
            logger.error("Redis delete failed", key=key, error=str(e))
            return False
    
    @staticmethod
    async def exists(key: str) -> bool:
        """Check if key exists"""
        try:
            client = await get_redis()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error("Redis exists check failed", key=key, error=str(e))
            return False
    
    @staticmethod
    async def increment(key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        try:
            client = await get_redis()
            return await client.incrby(key, amount)
        except Exception as e:
            logger.error("Redis increment failed", key=key, error=str(e))
            return None
    
    @staticmethod
    async def set_hash(key: str, mapping: dict, expire_seconds: int = 3600) -> bool:
        """Set hash values"""
        try:
            client = await get_redis()
            await client.hset(key, mapping=mapping)
            await client.expire(key, expire_seconds)
            return True
        except Exception as e:
            logger.error("Redis hash set failed", key=key, error=str(e))
            return False
    
    @staticmethod
    async def get_hash(key: str) -> Optional[dict]:
        """Get all hash values"""
        try:
            client = await get_redis()
            return await client.hgetall(key)
        except Exception as e:
            logger.error("Redis hash get failed", key=key, error=str(e))
            return None


class RedisPubSub:
    """Redis Pub/Sub for real-time messaging"""
    
    def __init__(self):
        self.pubsub = None
    
    async def subscribe(self, *channels: str):
        """Subscribe to channels"""
        try:
            client = await get_redis()
            self.pubsub = client.pubsub()
            await self.pubsub.subscribe(*channels)
            logger.info("Subscribed to channels", channels=channels)
        except Exception as e:
            logger.error("Subscribe failed", error=str(e))
            raise
    
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel"""
        try:
            client = await get_redis()
            data = json.dumps(message, default=str) if not isinstance(message, str) else message
            return await client.publish(channel, data)
        except Exception as e:
            logger.error("Publish failed", channel=channel, error=str(e))
            return 0
    
    async def listen(self):
        """Listen for messages"""
        if self.pubsub:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    yield message
    
    async def unsubscribe(self):
        """Unsubscribe from all channels"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()


# Export cache instance
cache = RedisCache()
pubsub = RedisPubSub()
