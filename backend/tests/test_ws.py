"""
WebSocket ajan bağlantı anahtarlama testi.

session_id istemcinin kendi seçtiği bir değer — tek başına anahtar olarak
kullanmak, B kullanıcısının A'nın session_id'sini kullanarak A'ya giden
canlı ajan verilerini (soğuk e-posta taslağı, kariyer stratejisi, CV
içeriği) okumasına izin veriyordu (oturum ele geçirme). Anahtar artık
"{user_id}:{session_id}" — bu test push_agent_event'in gerçekten sadece
doğru kullanıcının bağlantısına yazdığını doğruluyor.
"""
import json
import pytest

from backend.routers import ws as ws_module


class _FakeWebSocket:
    def __init__(self):
        self.sent: list[str] = []

    async def send_text(self, text: str):
        self.sent.append(text)


@pytest.mark.asyncio
async def test_push_agent_event_only_reaches_owning_user():
    ws_module._connections.clear()
    try:
        shared_session_id = "shared-session-id"  # iki kullanıcı da aynı (çakışan) session_id'yi kullanıyor

        socket_a = _FakeWebSocket()
        socket_b = _FakeWebSocket()
        ws_module._connections[ws_module._connection_key(1, shared_session_id)] = socket_a
        ws_module._connections[ws_module._connection_key(2, shared_session_id)] = socket_b

        await ws_module.push_agent_event(
            shared_session_id, "cv_architect", "done", "Hazır!", 100, user_id=1
        )

        assert len(socket_a.sent) == 1, "Sahibi olan kullanıcı mesajı almalı"
        assert len(socket_b.sent) == 0, "Aynı session_id'yi kullanan başka bir kullanıcı mesajı ALMAMALI"
        payload = json.loads(socket_a.sent[0])
        assert payload["status"] == "done"
        assert payload["step"] == "Hazır!"
    finally:
        ws_module._connections.clear()
