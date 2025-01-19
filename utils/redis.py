from redis.asyncio import Redis
from constants.redis import REDIS_CONNECTION_PARAMETERS
from utils.logger import logger


class RedisManager:
    def __init__(self):
        self.redis = Redis(
            host=REDIS_CONNECTION_PARAMETERS.HOST.value,
            port=REDIS_CONNECTION_PARAMETERS.PORT.value,
            username=REDIS_CONNECTION_PARAMETERS.USERNAME.value,
            password=REDIS_CONNECTION_PARAMETERS.PASSWORD.value,
            decode_responses=REDIS_CONNECTION_PARAMETERS.DECODE_RESPONSE.value,
        )

    async def check_redis_connection(self):
        try:
            await self.redis.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")

    def get_redis(self) -> Redis:
        return self.redis


redisManager = RedisManager()
