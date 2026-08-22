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

# Aktif WebSocket bağlantıları: "{user_id}:{session_id}" → WebSocket
# session_id istemcinin kendi ürettiği bir UUID — tek başına anahtar olarak
# kullanmak, B kullanıcısının A'nın session_id'sini (tahmin/gözlem yoluyla)
# kullanarak A'nın bağlantısını düşürüp A'ya giden verileri okumasına izin
# veriyordu (oturum ele geçirme). Anahtara bağlanan JWT'nin user_id'sini de
# katmak bunu engelliyor.
_connections: dict[str, WebSocket] = {}


def _connection_key(user_id: int, session_id: str) -> str:
    return f"{user_id}:{session_id}"


async def push_agent_event(
    session_id: str,
    agent: str,
    status: str,
    step: str = "",
    progress: int = 0,
    data: Optional[dict] = None,
    *,
    user_id: int,
):
    """
    Belirtilen kullanıcının session'ına ajan durumu gönderir.
    Herhangi bir ajan modülünden import edip çağrılabilir. `user_id` zorunlu
    keyword-only argüman — çağıran taraf yanlışlıkla unutamasın diye.
    """
    ws = _connections.get(_connection_key(user_id, session_id))
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
        _connections.pop(_connection_key(user_id, session_id), None)


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
        payload = verify_token(token)
        user_id = int(payload["sub"])
    except Exception:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    key = _connection_key(user_id, session_id)
    _connections[key] = websocket
    logger.info(f"[WS] Bağlandı: user={user_id} session={session_id}")

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
        logger.info(f"[WS] Bağlantı kesildi: user={user_id} session={session_id}")
    except Exception as e:
        logger.error(f"[WS] Hata: user={user_id} session={session_id}, {e}")
    finally:
        # Yalnızca hâlâ bu bağlantıya ait olan girdiyi sil — bu bağlantı zaten
        # devre dışı bırakılıp aynı anahtarı yeni bir bağlantı devraldıysa
        # (ör. sekme yenileme sırasında kısa bir çakışma) o yeni bağlantıyı
        # yanlışlıkla kaldırmayalım.
        if _connections.get(key) is websocket:
            _connections.pop(key, None)
