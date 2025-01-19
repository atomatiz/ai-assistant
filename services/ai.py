# import asyncio
from collections import defaultdict
import time
import uuid
from constants.ai import (
    AI_API_KEYS,
    AI_MODEL_NAMES,
    AI_MODELS,
    AI_QUERY_MODELS,
    GEMINI_CONTEXT_MESSAGE_KEYS,
    GEMINI_ROLES,
    GPT_CONTEXT_MESSAGE_KEYS,
    GPT_DEFAULT_CONTENT,
    GPT_ROLES,
)
from constants.base import RATE_LIMIT_COUNT, RATE_LIMIT_PERIOD, SYSTEM_ROLES
from constants.i18n import TRANSLATION_KEYS
from constants.redis import AI_REDIS_DATA_KEYS, CONTEXT_EXPIRE_TIME
from constants.websocket import AI_WS_MESSAGE_TYPE, AI_WS_SEND_KEYS
from fastapi import Depends, WebSocket
from redis import Redis
from models.context import Context
from models.message import Message
from utils.redis import redisManager
import openai
import google.generativeai as genai
from utils.i18n import t

rate_limit_data = defaultdict(list)

ai_mapper = {
    AI_MODELS.CHATGPT.value: AI_MODEL_NAMES.CHATGPT.value,
    AI_MODELS.GEMINI.value: AI_MODEL_NAMES.GEMINI.value,
}
ai_translation_key_mapper = {
    AI_MODEL_NAMES.CHATGPT.value: TRANSLATION_KEYS.AI_ACTIVATED_1.value,
    AI_MODEL_NAMES.GEMINI.value: TRANSLATION_KEYS.AI_ACTIVATED_2.value,
}


async def handle_rate_limit(
    websocket: WebSocket,
    locale: str,
    device_id: str,
    context_key: str,
    context_data: Context,
    redis: Redis = Depends(redisManager.get_redis),
):
    current_time = time.time()
    rate_limit_data[device_id] = [
        timestamp
        for timestamp in rate_limit_data[device_id]
        if current_time - timestamp < RATE_LIMIT_PERIOD
    ]

    if len(rate_limit_data[device_id]) >= RATE_LIMIT_COUNT:
        context = Context.parse_raw(context_data)
        locale_message = t(locale, TRANSLATION_KEYS.RATE_LIMIT.value)
        message = Message(
            id=str(uuid.uuid4()),
            prompt=locale_message,
        )
        context.messages.append(message)
        await websocket.send_json(
            {
                f"{AI_WS_SEND_KEYS.TYPE.value}": AI_WS_MESSAGE_TYPE.SYSTEM_MESSAGE.value,
                f"{AI_WS_SEND_KEYS.DATA.value}": message.dict(),
            }
        )
        await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)
        await websocket.close()

    rate_limit_data[device_id].append(current_time)


async def query_openai(
    prompt: str,
    context_key: str,
    redis: Redis = Depends(redisManager.get_redis),
) -> str:
    openai.api_key = AI_API_KEYS.OPENAI.value
    context_messages = await generate_context_messages(
        model=AI_MODELS.CHATGPT.value, context_key=context_key, redis=redis
    )
    response = openai.chat.completions.create(
        model=AI_QUERY_MODELS.OPENAI.value,
        messages=context_messages
        + [
            {
                f"{GPT_CONTEXT_MESSAGE_KEYS.ROLE.value}": GPT_ROLES.USER.value,
                f"{GPT_CONTEXT_MESSAGE_KEYS.CONTENT.value}": prompt,
            },
        ],
    )
    return response.choices[0].message.content


async def query_gemini(
    prompt: str,
    context_key: str,
    redis: Redis = Depends(redisManager.get_redis),
) -> str:
    genai.configure(api_key=AI_API_KEYS.GEMINI.value)
    model = genai.GenerativeModel(model_name=AI_QUERY_MODELS.GEMINI.value)
    context_messages = await generate_context_messages(
        model=AI_MODELS.GEMINI.value, context_key=context_key, redis=redis
    )
    context_messages.append(
        {
            f"{GEMINI_CONTEXT_MESSAGE_KEYS.ROLE.value}": GEMINI_ROLES.USER.value,
            f"{GEMINI_CONTEXT_MESSAGE_KEYS.PARTS.value}": [prompt],
        }
    )
    response = model.generate_content(context_messages)
    return response.text


async def generate_context_messages(
    model: str, context_key: str, redis: Redis = Depends(redisManager.get_redis)
):
    context_data = await redis.get(context_key)
    context = Context.parse_raw(context_data)
    context_messages = (
        [
            {
                f"{GPT_CONTEXT_MESSAGE_KEYS.ROLE.value}": GPT_ROLES.SYSTEM.value,
                f"{GPT_CONTEXT_MESSAGE_KEYS.CONTENT.value}": GPT_DEFAULT_CONTENT,
            }
        ]
        if model == AI_MODELS.CHATGPT.value
        else []
    )
    for msg in context.messages:
        if msg.prompt.startswith(f"{SYSTEM_ROLES.USER.value}:"):
            if model == AI_MODELS.CHATGPT.value:
                context_messages.append(
                    {
                        f"{GPT_CONTEXT_MESSAGE_KEYS.ROLE.value}": GPT_ROLES.USER.value,
                        f"{GPT_CONTEXT_MESSAGE_KEYS.CONTENT.value}": msg.prompt.replace(
                            f"{SYSTEM_ROLES.USER.value}:", ""
                        ),
                    }
                )
            elif model == AI_MODELS.GEMINI.value:
                context_messages.append(
                    {
                        f"{GEMINI_CONTEXT_MESSAGE_KEYS.ROLE.value}": GEMINI_ROLES.USER.value,
                        f"{GEMINI_CONTEXT_MESSAGE_KEYS.PARTS.value}": [
                            msg.prompt.replace(f"{SYSTEM_ROLES.USER.value}:", "")
                        ],
                    }
                )
        elif msg.prompt.startswith(f"{SYSTEM_ROLES.AI.value}:"):
            if model == AI_MODELS.CHATGPT.value:
                context_messages.append(
                    {
                        f"{GPT_CONTEXT_MESSAGE_KEYS.ROLE.value}": GPT_ROLES.ASSISTANT.value,
                        f"{GPT_CONTEXT_MESSAGE_KEYS.CONTENT.value}": msg.prompt.replace(
                            f"{SYSTEM_ROLES.AI.value}:", ""
                        ),
                    }
                )
            elif model == AI_MODELS.GEMINI.value:
                context_messages.append(
                    {
                        f"{GEMINI_CONTEXT_MESSAGE_KEYS.ROLE.value}": GEMINI_ROLES.MODEL.value,
                        f"{GEMINI_CONTEXT_MESSAGE_KEYS.PARTS.value}": [
                            msg.prompt.replace(f"{SYSTEM_ROLES.AI.value}:", "")
                        ],
                    }
                )
        else:
            continue
    return context_messages


async def handle_beginning_conversation(
    websocket: WebSocket,
    locale: str,
    context_key: str,
    context_data: Context,
    redis: Redis = Depends(redisManager.get_redis),
):
    context = Context.parse_raw(context_data)
    if len(context.messages) == 1:
        await generate_initial_conversation(
            websocket=websocket, locale=locale, context_key=context_key, redis=redis
        )
    else:
        await websocket.send_json(
            {
                f"{AI_WS_SEND_KEYS.TYPE.value}": AI_WS_MESSAGE_TYPE.CONTEXT.value,
                f"{AI_WS_SEND_KEYS.DATA.value}": {
                    f"{AI_WS_SEND_KEYS.MESSAGES.value}": [
                        message.dict() for message in context.messages
                    ]
                },
            }
        )


async def handle_send_message(
    websocket: WebSocket,
    locale: str,
    context_key: str,
    data,
    redis: Redis = Depends(redisManager.get_redis),
):
    context_data = await redis.get(context_key)
    context = Context.parse_raw(context_data)
    model = data.get(f"{AI_REDIS_DATA_KEYS.MODEL.value}", AI_MODELS.CHATGPT.value)
    prompt = data.get(f"{AI_REDIS_DATA_KEYS.PROMT.value}", "").strip()

    message = Message(
        id=str(uuid.uuid4()), prompt=f"{SYSTEM_ROLES.USER.value}: {prompt}"
    )
    context.messages.append(message)
    await websocket.send_json(
        {
            f"{AI_WS_SEND_KEYS.TYPE.value}": AI_WS_MESSAGE_TYPE.CLIENT_MESSAGE.value,
            f"{AI_WS_SEND_KEYS.DATA.value}": message.dict(),
        }
    )
    await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)

    try:
        if model == AI_MODELS.CHATGPT.value:
            response = await query_openai(
                prompt=prompt, context_key=context_key, redis=redis
            )
        elif model == AI_MODELS.GEMINI.value:
            response = await query_gemini(
                prompt=prompt, context_key=context_key, redis=redis
            )
    except Exception:
        response = t(locale, TRANSLATION_KEYS.UNAVAILABLE_MODEL.value)

    ai_message = Message(
        id=str(uuid.uuid4()), prompt=f"{SYSTEM_ROLES.AI.value}: {response}"
    )
    context.messages.append(ai_message)
    await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)

    # words = response.split()
    # await send_by_token(websocket, ai_message.id, words)
    await websocket.send_json(
        {
            f"{AI_WS_SEND_KEYS.TYPE.value}": AI_WS_MESSAGE_TYPE.AI_MESSAGE.value,
            f"{AI_WS_SEND_KEYS.DATA.value}": ai_message.dict(),
        }
    )


async def handle_switch_model(
    websocket: WebSocket,
    locale: str,
    context_key: str,
    data,
    redis: Redis = Depends(redisManager.get_redis),
):
    context_data = await redis.get(context_key)
    model = data.get(f"{AI_REDIS_DATA_KEYS.MODEL.value}", AI_MODELS.CHATGPT.value)
    locale_message = t(locale, ai_translation_key_mapper[ai_mapper[model]])
    context = Context.parse_raw(context_data)
    message = Message(id=str(uuid.uuid4()), prompt=locale_message)
    context.messages.append(message)
    await websocket.send_json(
        {
            f"{AI_WS_SEND_KEYS.TYPE.value}": AI_WS_MESSAGE_TYPE.SWITCH_MODEL.value,
            f"{AI_WS_SEND_KEYS.DATA.value}": message.dict(),
        }
    )
    await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)
    await handle_set_current_model(context_key=context_key, data=data, redis=redis)


async def generate_initial_conversation(
    websocket: WebSocket,
    locale: str,
    context_key: str,
    redis: Redis = Depends(redisManager.get_redis),
):
    context_data = await redis.get(context_key)
    previous_context = Context.parse_raw(context_data) if context_data != None else None
    current_model = (
        AI_MODELS.CHATGPT.value
        if previous_context == None
        else previous_context.current_model
    )
    await redis.delete(context_key)
    context = Context(id=str(uuid.uuid4()), messages=[])
    greeting = t(locale, TRANSLATION_KEYS.AI_GREETING.value)
    initial_message = Message(id=str(uuid.uuid4()), prompt=greeting)
    context.current_model = current_model
    context.messages.append(initial_message)
    await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)
    await websocket.send_json(
        {
            f"{AI_WS_SEND_KEYS.TYPE.value}": AI_WS_MESSAGE_TYPE.CONTEXT.value,
            f"{AI_WS_SEND_KEYS.DATA.value}": {
                f"{AI_WS_SEND_KEYS.MESSAGES.value}": [
                    message.dict() for message in context.messages
                ]
            },
        }
    )


async def handle_set_current_model(
    context_key: str,
    data: str,
    redis: Redis = Depends(redisManager.get_redis),
):
    context_data = await redis.get(context_key)
    context = Context.parse_raw(context_data)
    model = data.get(f"{AI_REDIS_DATA_KEYS.MODEL.value}", AI_MODELS.CHATGPT.value)
    if context.current_model != model:
        context.current_model = model
        await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)
    else:
        pass


async def handle_current_model(
    websocket: WebSocket,
    context_key: str,
    redis: Redis = Depends(redisManager.get_redis),
):
    context_data = await redis.get(context_key)
    context = Context.parse_raw(context_data)
    model = context.current_model
    if model == None:
        context.current_model = AI_MODELS.CHATGPT.value
        await websocket.send_json(
            {
                f"{AI_WS_SEND_KEYS.TYPE.value}": AI_WS_MESSAGE_TYPE.CURRENT_MODEL.value,
                f"{AI_WS_SEND_KEYS.DATA.value}": {
                    f"{AI_WS_SEND_KEYS.MODEL.value}": AI_MODELS.CHATGPT.value
                },
            }
        )
        await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)
    else:
        await websocket.send_json(
            {
                f"{AI_WS_SEND_KEYS.TYPE.value}": AI_WS_MESSAGE_TYPE.CURRENT_MODEL.value,
                f"{AI_WS_SEND_KEYS.DATA.value}": {
                    f"{AI_WS_SEND_KEYS.MODEL.value}": model
                },
            }
        )


# async def send_by_token(
#     websocket: WebSocket, message_id: str, words: list[str], delay: float = 0.1
# ):
#     for word in words:
#         await websocket.send_json(
#             {
#                 f"{AI_WS_SEND_KEYS.TYPE.value}": AI_WS_MESSAGE_TYPE.PARTIAL_MESSAGE.value,
#                 f"{AI_WS_SEND_KEYS.DATA.value}": {
#                     f"{AI_WS_SEND_KEYS.ID.value}": message_id,
#                     f"{AI_WS_SEND_KEYS.PROMPT.value}": word,
#                 },
#             }
#         )
#         await asyncio.sleep(delay)
