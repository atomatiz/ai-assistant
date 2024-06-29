# import asyncio
from collections import defaultdict
import time
import uuid
from constants.ai import (
    AI_MODEL,
    AI_MODEL_NAME,
    AI_WS_MESSAGE_TYPE,
    CONTEXT_EXPIRE_TIME,
    GEMINI_ROLES,
    GPT_ROLES,
    LOCALES,
    RATE_LIMIT_COUNT,
    RATE_LIMIT_PERIOD,
)
from core.config import settings
from fastapi import Depends, WebSocket
from redis import Redis
from models.context import Context
from models.message import Message
from utils.websocket import manager
import openai
import google.generativeai as genai

rate_limit_data = defaultdict(list)


async def handle_rate_limit(
    websocket: WebSocket,
    locale: str,
    device_id: str,
    context_key: str,
    context_data: Context,
    redis: Redis = Depends(manager.get_redis),
):
    current_time = time.time()
    rate_limit_data[device_id] = [
        timestamp
        for timestamp in rate_limit_data[device_id]
        if current_time - timestamp < RATE_LIMIT_PERIOD
    ]

    if len(rate_limit_data[device_id]) >= RATE_LIMIT_COUNT:
        context = Context.parse_raw(context_data)
        locale_message = (
            f"Rate limit exceeded. Try again later ❌"
            if locale == LOCALES[1]
            else f"Đã vượt quá giới hạn gửi. Hãy thử lại sau ❌"
        )
        message = Message(
            id=str(uuid.uuid4()),
            prompt=locale_message,
        )
        context.messages.append(message)
        await websocket.send_json(
            {"type": AI_WS_MESSAGE_TYPE.SYSTEM_MESSAGE, "data": message.dict()}
        )
        await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)
        await websocket.close()

    rate_limit_data[device_id].append(current_time)


async def query_openai(
    prompt: str,
    context_key: str,
    redis: Redis = Depends(manager.get_redis),
) -> str:
    openai.api_key = settings.OPENAI_API_KEY
    context_messages = await generate_context_messages(
        model=AI_MODEL[0], context_key=context_key, redis=redis
    )
    response = openai.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=context_messages
        + [
            {"role": GPT_ROLES.USER, "content": prompt},
        ],
    )
    return response.choices[0].message.content


async def query_gemini(
    prompt: str,
    context_key: str,
    redis: Redis = Depends(manager.get_redis),
) -> str:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
    context_messages = await generate_context_messages(
        model=AI_MODEL[1], context_key=context_key, redis=redis
    )
    context_messages.append({"role": GEMINI_ROLES.USER, "parts": [prompt]})
    response = model.generate_content(context_messages)
    return response.text


async def generate_context_messages(
    model: str, context_key: str, redis: Redis = Depends(manager.get_redis)
):
    context_data = await redis.get(context_key)
    context = Context.parse_raw(context_data)
    context_messages = (
        [{"role": GPT_ROLES.SYSTEM, "content": "You are a helpful assistant."}]
        if model == AI_MODEL[0]
        else []
    )
    for msg in context.messages:
        if msg.prompt.startswith("You:"):
            (
                context_messages.append(
                    {"role": GPT_ROLES.USER, "content": msg.prompt.replace("You:", "")}
                )
                if model == AI_MODEL[0]
                else context_messages.append(
                    {
                        "role": GEMINI_ROLES.USER,
                        "parts": [msg.prompt.replace("You:", "")],
                    }
                )
            )
        elif msg.prompt.startswith("AI:"):
            (
                context_messages.append(
                    {
                        "role": GPT_ROLES.ASSISTANT,
                        "content": msg.prompt.replace("AI:", ""),
                    }
                )
                if model == AI_MODEL[0]
                else context_messages.append(
                    {
                        "role": GEMINI_ROLES.MODEL,
                        "parts": [msg.prompt.replace("AI:", "")],
                    }
                )
            )
        else:
            continue
    return context_messages


async def handle_beginning_conversation(
    websocket: WebSocket,
    locale: str,
    context_key: str,
    context_data: Context,
    redis: Redis = Depends(manager.get_redis),
):
    context = Context.parse_raw(context_data)
    if len(context.messages) == 1:
        await generate_initial_conversation(
            websocket=websocket, locale=locale, context_key=context_key, redis=redis
        )
    else:
        await websocket.send_json(
            {
                "type": AI_WS_MESSAGE_TYPE.CONTEXT,
                "data": {"messages": [message.dict() for message in context.messages]},
            }
        )


async def handle_send_message(
    websocket: WebSocket,
    locale: str,
    context_key: str,
    data,
    redis: Redis = Depends(manager.get_redis),
):
    context_data = await redis.get(context_key)
    context = Context.parse_raw(context_data)
    model = data.get("model", AI_MODEL[0])
    prompt = data.get("prompt", "").strip()

    message = Message(id=str(uuid.uuid4()), prompt=f"You: {prompt}")
    context.messages.append(message)
    await websocket.send_json(
        {"type": AI_WS_MESSAGE_TYPE.CLIENT_MESSAGE, "data": message.dict()}
    )
    await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)

    try:
        if model == AI_MODEL[0]:
            response = await query_openai(
                prompt=prompt, context_key=context_key, redis=redis
            )
        else:
            response = await query_gemini(
                prompt=prompt, context_key=context_key, redis=redis
            )
    except Exception:
        response = (
            "Mẫu này hiện không hỗ trợ, vui lòng chọn mẫu khác ❗️"
            if locale == LOCALES[0]
            else "This model is currently unavailable, please select the other one ❗️"
        )

    ai_message = Message(id=str(uuid.uuid4()), prompt=f"AI: {response}")
    context.messages.append(ai_message)
    await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)

    # words = response.split()
    # await send_by_token(websocket, ai_message.id, words)
    await websocket.send_json(
        {"type": AI_WS_MESSAGE_TYPE.AI_MESSAGE, "data": ai_message.dict()}
    )


async def handle_switch_model(
    websocket: WebSocket,
    locale: str,
    context_key: str,
    data,
    redis: Redis = Depends(manager.get_redis),
):
    context_data = await redis.get(context_key)
    model = data.get("model", AI_MODEL[0])
    model_name = AI_MODEL_NAME[0] if model == AI_MODEL[0] else AI_MODEL_NAME[1]
    locale_message = (
        f"AI: {model_name} has been activated 🚀"
        if locale == LOCALES[1]
        else f"AI: {model_name} đã được kích hoạt 🚀"
    )
    context = Context.parse_raw(context_data)
    message = Message(id=str(uuid.uuid4()), prompt=locale_message)
    context.messages.append(message)
    await websocket.send_json(
        {"type": AI_WS_MESSAGE_TYPE.SWITCH_MODEL, "data": message.dict()}
    )
    await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)
    await handle_set_current_model(context_key=context_key, data=data, redis=redis)


async def generate_initial_conversation(
    websocket: WebSocket,
    locale: str,
    context_key: str,
    redis: Redis = Depends(manager.get_redis),
):
    await redis.delete(context_key)
    context = Context(id=str(uuid.uuid4()), messages=[])
    greeting = (
        "AI: Xin chào! Tôi có thể giúp gì cho bạn? 👋🏻"
        if locale == LOCALES[0]
        else "AI: Hello! How may I assist you today? 👋🏻"
    )
    initial_message = Message(id=str(uuid.uuid4()), prompt=greeting)
    context.messages.append(initial_message)
    await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)
    await websocket.send_json(
        {
            "type": AI_WS_MESSAGE_TYPE.CONTEXT,
            "data": {"messages": [message.dict() for message in context.messages]},
        }
    )


async def handle_set_current_model(
    context_key: str,
    data: str,
    redis: Redis = Depends(manager.get_redis),
):
    context_data = await redis.get(context_key)
    context = Context.parse_raw(context_data)
    model = data.get("model", AI_MODEL[0])
    if context.current_model != model:
        context.current_model = model
        await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)
    else:
        pass


async def handle_current_model(
    websocket: WebSocket,
    context_key: str,
    redis: Redis = Depends(manager.get_redis),
):
    context_data = await redis.get(context_key)
    context = Context.parse_raw(context_data)
    model = context.current_model
    if model == None:
        context.current_model = AI_MODEL[0]
        await websocket.send_json(
            {
                "type": AI_WS_MESSAGE_TYPE.CURRENT_MODEL,
                "data": {"model": AI_MODEL[0]},
            }
        )
        await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)
    else:
        await websocket.send_json(
            {
                "type": AI_WS_MESSAGE_TYPE.CURRENT_MODEL,
                "data": {"model": model},
            }
        )


# async def send_by_token(
#     websocket: WebSocket, message_id: str, words: list[str], delay: float = 0.1
# ):
#     for word in words:
#         await websocket.send_json(
#             {
#                 "type": AI_WS_MESSAGE_TYPE.PARTIAL_MESSAGE,
#                 "data": {"id": message_id, "prompt": word},
#             }
#         )
#         await asyncio.sleep(delay)
