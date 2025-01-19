from redis.asyncio import Redis
from constants.redis import REDIS_CONNECTION_PARAMETERS
from utils.logger import logger


class RedisManager:
    def __init__(self):
        self.redis = Redis(
            host=REDIS_CONNECTION_PARAMETERS.HOST,
            port=REDIS_CONNECTION_PARAMETERS.PORT,
            username=REDIS_CONNECTION_PARAMETERS.USERNAME,
            password=REDIS_CONNECTION_PARAMETERS.PASSWORD,
            decode_responses=REDIS_CONNECTION_PARAMETERS.DECODE_RESPONSE,
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
