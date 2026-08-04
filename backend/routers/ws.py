"""
Kariyer Ajanı 2.0 — WebSocket Ajan İletişim Katmanı
Her ajan oturumu için gerçek zamanlı durum akışı sağlar.
"""
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from backend.auth import verify_token

router = APIRouter(tags=["WebSocket"])
logger = logging.getLogger(__name__)

# Aktif WebSocket bağlantıları: session_id → WebSocket
_connections: dict[str, WebSocket] = {}


async def push_agent_event(
    session_id: str,
    agent: str,
    status: str,
    step: str = "",
    progress: int = 0,
    data: Optional[dict] = None,
):
    """
    Belirtilen session'a ajan durumu gönderir.
    Herhangi bir ajan modülünden import edip çağrılabilir.
    """
    ws = _connections.get(session_id)
    if not ws:
        return  # Bağlantı yoksa sessizce geç

    payload = {
        "agent": agent,
        "status": status,       # idle | running | done | failed
        "step": step,           # "GitHub taranıyor...", "CV oluşturuluyor..."
        "progress": max(0, min(100, progress)),
        "data": data or {},
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await ws.send_text(json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"[WS] session={session_id} mesaj gönderilemedi: {e}")
        _connections.pop(session_id, None)


@router.websocket("/ws/agents/{session_id}")
async def agent_websocket(websocket: WebSocket, session_id: str, token: str = Query(...)):
    """
    Frontend bağlantı noktası.
    Bağlandıktan sonra sunucu push eder, client sadece dinler.
    Ping/pong ile bağlantı canlı tutulur.

    Not: Tarayıcının native WebSocket API'si custom header (Authorization) taşıyamaz,
    bu yüzden token burada query parametresi olarak doğrulanır.
    """
    try:
        verify_token(token)
    except Exception:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    _connections[session_id] = websocket
    logger.info(f"[WS] Bağlandı: session={session_id}")

    try:
        # Bağlantı onayı gönder
        await websocket.send_text(json.dumps({
            "agent": "system",
            "status": "connected",
            "step": f"Ajan oturumu {session_id} aktif.",
            "progress": 0,
        }))

        # Bağlantıyı canlı tut — client disconnect edene kadar bekle
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Client'tan "ping" gelirse "pong" dön
                if msg.strip() == "ping":
                    await websocket.send_text(json.dumps({"agent": "system", "status": "pong"}))
            except asyncio.TimeoutError:
                # 30s timeout → server tarafından ping at
                await websocket.send_text(json.dumps({"agent": "system", "status": "heartbeat"}))

    except WebSocketDisconnect:
        logger.info(f"[WS] Bağlantı kesildi: session={session_id}")
    except Exception as e:
        logger.error(f"[WS] Hata: session={session_id}, {e}")
    finally:
        _connections.pop(session_id, None)
