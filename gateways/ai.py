from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from constants.ai import CONTEXT_EXPIRE_TIME
from models.context import Context
from models.message import Message
from services.ai import (
    generate_initial_conversation,
    query_gemini,
    query_openai,
    # send_by_token,
)
from utils.websocket import ConnectionManager
from redis.asyncio import Redis
import uuid

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/{locale}/{device_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    locale: str,
    device_id: str,
    redis: Redis = Depends(manager.get_redis),
):

    await manager.connect(websocket, device_id)
    context_key = f"context:{device_id}"
    context_data = await redis.get(context_key)

    if context_data:
        context = Context.parse_raw(context_data)
        if len(context.messages) == 1:
            await generate_initial_conversation(
                websocket=websocket, locale=locale, device_id=device_id, redis=redis
            )
        else:
            await websocket.send_json(
                {
                    "type": "context",
                    "data": {
                        "messages": [message.dict() for message in context.messages]
                    },
                }
            )
    else:
        await generate_initial_conversation(
            websocket=websocket, locale=locale, device_id=device_id, redis=redis
        )

    try:
        while True:

            data = await websocket.receive_json()
            action = data.get("action", "send_message")

            if action == "send_message":
                model = data.get("model", "ChatGPT")
                prompt = data.get("prompt", "").strip()

                context_data = await redis.get(context_key)
                context = Context.parse_raw(context_data)

                message = Message(id=str(uuid.uuid4()), prompt=f"You: {prompt}")
                context.messages.append(message)
                await websocket.send_json(
                    {"type": "client_message", "data": message.dict()}
                )
                await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)

                try:
                    if model == "ChatGPT":
                        response = await query_openai(prompt)
                    else:
                        response = await query_gemini(prompt)
                except Exception:
                    response = (
                        "Mẫu này hiện không hỗ trợ, vui lòng chọn mẫu khác."
                        if locale == "vi"
                        else "This model is currently unavailable, please select the other one."
                    )

                ai_message = Message(id=str(uuid.uuid4()), prompt=f"AI: {response}")
                context.messages.append(ai_message)
                await redis.set(context_key, context.json(), ex=CONTEXT_EXPIRE_TIME)

                # words = response.split()
                # await send_by_token(websocket, ai_message.id, words)
                await websocket.send_json(
                    {"type": "ai_message", "data": ai_message.dict()}
                )

            elif action == "new_context":
                await generate_initial_conversation(
                    websocket=websocket, locale=locale, device_id=device_id, redis=redis
                )

    except WebSocketDisconnect:
        manager.disconnect(device_id)
        print(f"Disconnected: {device_id}")
