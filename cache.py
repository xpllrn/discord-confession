import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis
from config import Config

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        try:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                password=Config.REDIS_PASSWORD or None,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Operating with fallback mode.")
            self.redis_client = None

    async def close(self):
        if self.redis_client:
            await self.redis_client.aclose()

    async def get_guild_config(self, guild_id: int) -> Optional[Dict[str, Any]]:
        if not self.redis_client:
            return None
        try:
            data = await self.redis_client.get(f"guild_config:{guild_id}")
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error reading from Redis for guild {guild_id}: {e}")
        return None

    async def set_guild_config(self, guild_id: int, config_data: Dict[str, Any]):
        if not self.redis_client:
            return
        try:
            await self.redis_client.set(
                f"guild_config:{guild_id}",
                json.dumps(config_data),
                ex=86400  # 24 hours TTL cache
            )
        except Exception as e:
            logger.error(f"Error setting Redis cache for guild {guild_id}: {e}")

    async def clear_guild_config(self, guild_id: int):
        if not self.redis_client:
            return
        try:
            await self.redis_client.delete(f"guild_config:{guild_id}")
        except Exception as e:
            logger.error(f"Error clearing Redis cache for guild {guild_id}: {e}")
