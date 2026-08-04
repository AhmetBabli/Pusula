"""
Kariyer Ajanı — SSE Task Tracker
Arka plan görevlerinin durumunu (pending → running → done/failed)
Server-Sent Events aracılığıyla frontend'e gerçek zamanlı bildirir.
"""
import json
import asyncio
from datetime import datetime, timezone
from typing import Any, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from backend.auth import get_current_user, verify_token
from backend.models.user import UserProfile

router = APIRouter(prefix="/tasks", tags=["Task Tracker"])

# Basit in-memory task store.
# Üretimde bunu Redis'e taşı: task_store = RedisClient(...)
task_store: dict[str, dict] = {}


def update_task(
    task_id: str,
    status: str,
    progress: int = 0,
    result: Optional[Any] = None,
    error: Optional[str] = None,
):
    """
    Görev durumunu günceller. Herhangi bir router'dan import edip çağrılabilir.
    status: "pending" | "running" | "done" | "failed"
    """
    task_store[task_id] = {
        "task_id": task_id,
        "status": status,
        "progress": max(0, min(100, progress)),
        "result": result,
        "error": error,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_task(task_id: str) -> Optional[dict]:
    return task_store.get(task_id)


async def _sse_generator(task_id: str) -> AsyncGenerator[str, None]:
    """
    Görev tamamlanana veya başarısız olana kadar durumu SSE akışı olarak gönderir.
    Görev yoksa 'not_found' ile hemen sonlanır.
    """
    MAX_WAIT_SECONDS = 300  # 5 dakika timeout
    elapsed = 0.0
    POLL_INTERVAL = 1.5

    while elapsed < MAX_WAIT_SECONDS:
        task = task_store.get(task_id)

        if task is None:
            payload = json.dumps({"task_id": task_id, "status": "not_found"})
            yield f"data: {payload}\n\n"
            return

        yield f"data: {json.dumps(task)}\n\n"

        if task["status"] in ("done", "failed"):
            return

        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

    # Timeout
    timeout_payload = json.dumps({
        "task_id": task_id,
        "status": "failed",
        "error": "Görev zaman aşımına uğradı (5 dakika).",
    })
    yield f"data: {timeout_payload}\n\n"


@router.get("/{task_id}")
def get_task_status(task_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Anlık görev durumu (SSE olmadan)."""
    task = task_store.get(task_id)
    if not task:
        return {"task_id": task_id, "status": "not_found"}
    return task


@router.get("/{task_id}/stream")
async def stream_task(task_id: str, token: str = Query(...)):
    """
    Server-Sent Events akışı.
    Frontend: const es = new EventSource('/api/tasks/{task_id}/stream?token=...')
    Görev done/failed olunca akış otomatik kapanır.

    Not: Tarayıcının native EventSource API'si custom header (Authorization) taşıyamaz,
    bu yüzden token burada query parametresi olarak doğrulanır.
    """
    verify_token(token)
    return StreamingResponse(
        _sse_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Nginx reverse proxy buffer'ı devre dışı
            "Connection": "keep-alive",
        },
    )
