from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from constants.websocket import AI_WS_ACTION_TYPE, WS_KEYS
from utils.websocket import webSocketManager
from utils.redis import redisManager
from redis.asyncio import Redis
from services.ai import (
    generate_initial_conversation,
    handle_beginning_conversation,
    handle_current_model,
    handle_rate_limit,
    handle_send_message,
    handle_set_current_model,
    handle_switch_model,
)
from utils.logger import logger

router = APIRouter()


@router.websocket("/ws/{locale}/{device_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    locale: str,
    device_id: str,
    redis: Redis = Depends(redisManager.get_redis),
):
    await webSocketManager.connect(websocket, device_id)
    context_key = f"{WS_KEYS.CONTEXT}:{device_id}"
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
            action = data.get(f"{WS_KEYS.ACTION}", AI_WS_ACTION_TYPE.SEND_MESSAGE)

            match action:
                case AI_WS_ACTION_TYPE.SEND_MESSAGE:
                    await handle_send_message(
                        websocket=websocket,
                        locale=locale,
                        context_key=context_key,
                        data=data,
                        redis=redis,
                    )
                case AI_WS_ACTION_TYPE.SWITCH_MODEL:
                    await handle_switch_model(
                        websocket=websocket,
                        locale=locale,
                        context_key=context_key,
                        data=data,
                        redis=redis,
                    )
                case AI_WS_ACTION_TYPE.NEW_CONTEXT:
                    await generate_initial_conversation(
                        websocket=websocket,
                        locale=locale,
                        context_key=context_key,
                        redis=redis,
                    )
                case AI_WS_ACTION_TYPE.SET_CURRENT_MODEL:
                    await handle_set_current_model(
                        context_key=context_key,
                        data=data,
                        redis=redis,
                    )
                case AI_WS_ACTION_TYPE.CURRENT_MODEL:
                    await handle_current_model(
                        websocket=websocket,
                        context_key=context_key,
                        redis=redis,
                    )

    except WebSocketDisconnect:
        webSocketManager.disconnect(device_id)
        logger.info(f"Websocket disconnected: {device_id}")
