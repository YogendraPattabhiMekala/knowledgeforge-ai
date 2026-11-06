"""Request safeguards. Only the immediate peer IP is trusted, never forwarded input."""

import hashlib
import time
from collections import OrderedDict
import structlog
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from .config import settings

log = structlog.get_logger()


class RateLimiter:
    """Redis atomic fixed windows; bounded local fallback for the single-process demo."""

    def __init__(self):
        self.windows = OrderedDict()
        self.redis = None

    async def allow(self, key, maximum=30, now=None):
        now = time.time() if now is None else now
        bucket = int(now // 60)
        digest = hashlib.sha256(key.encode()).hexdigest()
        if settings.task_mode == "celery":
            if self.redis is None:
                self.redis = Redis.from_url(
                    settings.redis_url, socket_connect_timeout=2, socket_timeout=2
                )
            # Script is atomic; TTL is installed even on the first request.
            script = "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],65) end; return n"
            return (
                await self.redis.eval(script, 1, f"ratelimit:{bucket}:{digest}")
                <= maximum
            )
        value = self.windows.pop(digest, (bucket, 0))
        count = value[1] + 1 if value[0] == bucket else 1
        self.windows[digest] = (bucket, count)
        while len(self.windows) > 4096:
            self.windows.popitem(last=False)
        return count <= maximum


limiter = RateLimiter()


def install_security(app):
    @app.middleware("http")
    async def security(request, call_next):
        started = time.monotonic()
        response = None
        body_too_large = False
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin and origin not in {
                settings.public_url.rstrip("/"),
                *settings.allowed_origins,
            }:
                response = JSONResponse({"detail": "Origin not allowed"}, 403)
            # Count actual streamed bytes, not just a spoofable Content-Length.
            if response is None:
                total = 0
                receive = request._receive

                async def bounded_receive():
                    nonlocal total, body_too_large
                    message = await receive()
                    total += len(message.get("body", b""))
                    if total > 21 * 1024 * 1024:
                        body_too_large = True
                        from starlette.exceptions import HTTPException

                        raise HTTPException(413, "Request exceeds 21 MB")
                    return message

                request._receive = bounded_receive
                length = request.headers.get("content-length", "0")
                if length.isdigit() and int(length) > 21 * 1024 * 1024:
                    response = JSONResponse({"detail": "Request exceeds 21 MB"}, 413)
        path = request.url.path
        protected = (
            path.startswith("/api/auth/") and request.method == "POST"
        ) or path.endswith("/chat")
        if response is None and protected:
            # Group chat across tenant paths; /me polling does not consume login quota.
            category = "chat" if path.endswith("/chat") else path
            session = request.cookies.get("kf_session", "")
            peer = request.client.host if request.client else "unknown"
            key = (
                hashlib.sha256(session.encode()).hexdigest()
                if session and category == "chat"
                else peer
            ) + category
            try:
                allowed = await limiter.allow(key)
                if not allowed:
                    response = JSONResponse(
                        {"detail": "Too many requests. Try again in a minute."},
                        429,
                        headers={"Retry-After": "60"},
                    )
            except Exception:
                log.error("rate_limit_backend_unavailable")
                response = JSONResponse(
                    {"detail": "Request protection temporarily unavailable"}, 503
                )
        if response is None:
            try:
                response = await call_next(request)
            except Exception:
                # Do not log exception messages/locals: providers may include sensitive payloads.
                log.error("unhandled_request_error", path=path)
                response = JSONResponse(
                    {"detail": "Service operation failed. Please retry."}, 500
                )
        # Multipart/JSON parsers can translate receive errors to 400. Preserve the
        # actual size-limit status without reading or buffering the remaining body.
        if body_too_large:
            response = JSONResponse({"detail": "Request exceeds 21 MB"}, 413)
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "same-origin",
                "Cache-Control": "no-store",
            }
        )
        log.info(
            "http_request",
            method=request.method,
            path=path,
            status=response.status_code,
            duration_ms=round((time.monotonic() - started) * 1000),
        )
        return response
