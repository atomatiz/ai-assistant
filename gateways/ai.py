from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from constants.ai import AI_WS_ACTION_TYPE
from services.ai import (
    generate_initial_conversation,
    handle_beginning_conversation,
    handle_current_model,
    handle_rate_limit,
    handle_send_message,
    handle_set_current_model,
    handle_switch_model,
)
from utils.websocket import ConnectionManager
from redis.asyncio import Redis

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
        await handle_beginning_conversation(
            websocket=websocket,
            locale=locale,
            context_key=context_key,
            context_data=context_data,
            redis=redis,
        )
    else:
        await generate_initial_conversation(
            websocket=websocket, locale=locale, context_key=context_key, redis=redis
        )

    try:
        while True:

            await handle_rate_limit(
                websocket=websocket,
                locale=locale,
                device_id=device_id,
                context_key=context_key,
                context_data=context_data,
                redis=redis,
            )

            data = await websocket.receive_json()
            action = data.get("action", AI_WS_ACTION_TYPE.SEND_MESSAGE)

            if action == AI_WS_ACTION_TYPE.SEND_MESSAGE:
                await handle_send_message(
                    websocket=websocket,
                    locale=locale,
                    context_key=context_key,
                    data=data,
                    redis=redis,
                )

            elif action == AI_WS_ACTION_TYPE.SWITCH_MODEL:
                await handle_switch_model(
                    websocket=websocket,
                    locale=locale,
                    context_key=context_key,
                    data=data,
                    redis=redis,
                )

            elif action == AI_WS_ACTION_TYPE.NEW_CONTEXT:
                await generate_initial_conversation(
                    websocket=websocket,
                    locale=locale,
                    context_key=context_key,
                    redis=redis,
                )

            elif action == AI_WS_ACTION_TYPE.SET_CURRENT_MODEL:
                await handle_set_current_model(
                    context_key=context_key,
                    data=data,
                    redis=redis,
                )

            elif action == AI_WS_ACTION_TYPE.CURRENT_MODEL:
                await handle_current_model(
                    websocket=websocket,
                    context_key=context_key,
                    redis=redis,
                )

    except WebSocketDisconnect:
        manager.disconnect(device_id)
        print(f"Disconnected: {device_id}")
