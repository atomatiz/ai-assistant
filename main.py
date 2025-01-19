from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from gateways import ai
from utils.redis import redisManager
from fastapi.middleware.cors import CORSMiddleware
from constants.base import (
    ALLOWED_HEADERS,
    ALLOWED_METHODS,
    HOST,
    MODULE,
    ORIGINS,
    PORT,
    PREFIX,
)
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = await redisManager.check_redis_connection()
    yield
    # Shutdown
    app.state.shutdown = logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
)

app.include_router(ai.router, prefix=PREFIX)

if __name__ == MODULE:
    uvicorn.run(app, host=HOST, port=PORT)
