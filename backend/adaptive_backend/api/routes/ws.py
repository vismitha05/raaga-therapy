from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from adaptive_backend.api.dependencies import ws_manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
