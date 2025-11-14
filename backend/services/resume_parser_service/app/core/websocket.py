from typing import Dict, Set
import socketio
from common.logging import get_logger

logger = get_logger(__name__)

# Create Socket.IO async server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1000000,
)

# Track connected users: user_id -> set of session_ids
connected_users: Dict[str, Set[str]] = {}

# Allow up to 3 concurrent connections
MAX_CONNECTIONS_PER_USER = 3


class WebSocketManager:
    @staticmethod
    async def connect(sid: str, user_id: str):
        if user_id not in connected_users:
            connected_users[user_id] = set()

        # Check connection limit
        if len(connected_users[user_id]) >= MAX_CONNECTIONS_PER_USER:
            logger.warning(
                f"User {user_id} exceeded connection limit "
                f"({len(connected_users[user_id])} active). "
                f"Closing oldest connection."
            )
            # Close oldest connection
            oldest_sid = list(connected_users[user_id])[0]
            await sio.disconnect(oldest_sid)
            connected_users[user_id].discard(oldest_sid)

        connected_users[user_id].add(sid)
        logger.info(
            f"WebSocket connected: user={user_id}, sid={sid} "
            f"({len(connected_users[user_id])} active)"
        )

    @staticmethod
    async def disconnect(sid: str, user_id: str):
        if user_id in connected_users:
            connected_users[user_id].discard(sid)
            if not connected_users[user_id]:
                del connected_users[user_id]
        logger.info(f"WebSocket disconnected: user={user_id}, sid={sid}")

    @staticmethod
    async def emit_to_user(user_id: str, event: str, data: dict):
        if user_id not in connected_users:
            logger.debug(f"User {user_id} not connected via WebSocket")
            return

        for sid in connected_users[user_id]:
            try:
                await sio.emit(event, data, room=sid)
            except Exception as e:
                logger.error(f"Failed to emit to {sid}: {e}")

        logger.info(
            f"Sent '{event}' to user {user_id} "
            f"({len(connected_users[user_id])} sessions)"
        )

    @staticmethod
    async def emit_parsing_progress(
        user_id: str,
        resume_id: str,
        filename: str,
        stage: str,
        progress: int,
        message: str,
    ):

        await WebSocketManager.emit_to_user(
            user_id,
            "parsing_progress",
            {
                "resume_id": str(resume_id),
                "filename": filename,
                "stage": stage,
                "progress": progress,
                "message": message,
                "timestamp": None,  # Will be set by client
            },
        )

    @staticmethod
    async def emit_parsing_complete(
        user_id: str, resume_id: str, filename: str, success: bool, error: str = None
    ):
        await WebSocketManager.emit_to_user(
            user_id,
            "parsing_complete",
            {
                "resume_id": str(resume_id),
                "filename": filename,
                "success": success,
                "error": error,
                "timestamp": None,
            },
        )

    @staticmethod
    async def emit_batch_progress(
        user_id: str, batch_id: str, total: int, completed: int, failed: int
    ):
        await WebSocketManager.emit_to_user(
            user_id,
            "batch_progress",
            {
                "batch_id": batch_id,
                "total": total,
                "completed": completed,
                "failed": failed,
                "progress": int((completed + failed) / total * 100),
            },
        )


# Socket.IO Event Handlers


@sio.event
async def connect(sid, environ, auth):
    user_id = auth.get("user_id") if auth else None

    if not user_id:
        logger.warning(f"Connection rejected: no user_id (sid={sid})")
        return False

    await WebSocketManager.connect(sid, user_id)
    await sio.emit(
        "connected",
        {
            "message": "Successfully connected to Resume Parser WebSocket",
            "user_id": user_id,
        },
        room=sid,
    )

    return True


@sio.event
async def disconnect(sid):
    # Find user_id for this session
    for user_id, sids in list(connected_users.items()):
        if sid in sids:
            await WebSocketManager.disconnect(sid, user_id)
            break


@sio.event
async def ping(sid, data):
    await sio.emit("pong", {"timestamp": data.get("timestamp")}, room=sid)


ws_manager = WebSocketManager()
