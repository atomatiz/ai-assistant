# import asyncio
import uuid
from core.config import settings
from fastapi import Depends, WebSocket
from redis import Redis
from models.context import Context
from models.message import Message
from utils.websocket import manager
import openai
import google.generativeai as genai

openai.api_key = settings.OPENAI_API_KEY
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)


async def query_openai(prompt: str) -> str:
    response = openai.completions.create(
        model=settings.OPENAI_MODEL,
        prompt=prompt,
    )
    return await response.choices[0].text.strip()


async def query_gemini(prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text


# async def send_by_token(
#     websocket: WebSocket, message_id: str, words: list[str], delay: float = 0.1
# ):
#     for word in words:
#         await websocket.send_json(
#             {"type": "partial_message", "data": {"id": message_id, "prompt": word}}
#         )
#         await asyncio.sleep(delay)


async def generate_initial_conversation(
    websocket: WebSocket,
    locale: str,
    device_id: str,
    redis: Redis = Depends(manager.get_redis),
):
    context_key = f"context:{device_id}"
    await redis.delete(context_key)
    context = Context(id=str(uuid.uuid4()), messages=[])
    greeting = (
        "AI: Xin chào! Tôi có thể giúp gì cho bạn?"
        if locale == "vi"
        else "AI: Hello! How may I assist you today?"
    )
    initial_message = Message(id=str(uuid.uuid4()), prompt=greeting)
    context.messages.append(initial_message)
    await redis.set(context_key, context.json())
    await websocket.send_json(
        {
            "type": "context",
            "data": {"messages": [message.dict() for message in context.messages]},
        }
    )
