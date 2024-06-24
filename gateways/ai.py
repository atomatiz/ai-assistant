from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from models.context import Context
from models.message import Message
from services.ai import generate_initial_conversation, query_gemini, query_openai, send_by_token
from utils.websocket import ConnectionManager
from redis.asyncio import Redis
import uuid

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str, redis: Redis = Depends(manager.get_redis)):

    await manager.connect(websocket, device_id)
    context_key = f"context:{device_id}"
    context_data = await redis.get(context_key)
    
    if context_data:
        context = Context.parse_raw(context_data)
        await websocket.send_json({"type": "context", "data": {"messages": [message.dict() for message in context.messages]}})
    else:
        await generate_initial_conversation(websocket=websocket, device_id=device_id, redis=redis)
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "send_message")
            
            if action == "send_message":
                model = data.get("model", "ChatGPT")
                prompt = data.get("prompt", "").strip()
                
                if not prompt:
                    await websocket.send_json({"type": "error", "data": "AI: Message shouldn't be empty"})
                    continue
                
                message = Message(id=str(uuid.uuid4()), prompt=f"You: {prompt}")
                context_data = await redis.get(context_key)
                context = Context.parse_raw(context_data)
                context.messages.append(message)
                await websocket.send_json({"type": "message", "data": message.dict()})
                await redis.set(context_key, context.json())
    
                try:
                    if model == "ChatGPT":
                        response = await query_openai(prompt)
                    else:
                        response = await query_gemini(prompt)
                except Exception:
                    response = "This model is currently unavailable, please select the other one."
                
                ai_message = Message(id=str(uuid.uuid4()), prompt=f"AI: {response}")
                context.messages.append(ai_message)
                await redis.set(context_key, context.json())
                
                words = response.split()
                await send_by_token(websocket, ai_message.id, words)
                await websocket.send_json({"type": "message", "data": ai_message.dict()})
            
            elif action == "new_context":        
                await generate_initial_conversation(websocket=websocket, device_id=device_id, redis=redis)
            
            elif action == "cleanup_session":
                await redis.delete(context_key)
                    
    except WebSocketDisconnect:
        manager.disconnect(device_id)
        print(f"Disconnected: {device_id}")
