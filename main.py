import uvicorn
from fastapi import FastAPI
from gateways import ai
from utils.websocket import manager
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

app = FastAPI()

origins = [
    settings.ALLOWED_HOST_1,
    settings.ALLOWED_HOST_2
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await manager.check_redis_connection()


app.include_router(ai.router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
