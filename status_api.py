"""Public status HTTP server for confess.adore.rest/status."""

from __future__ import annotations

import logging
import os
import time
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from bot import ConfessionBot

log = logging.getLogger("confess.status_api")


def _payload(bot: "ConfessionBot") -> dict:
    started = getattr(bot, "_status_started_at", None) or time.time()
    latency_ms = round(float(bot.latency) * 1000, 1) if bot.latency is not None else None
    closed = bot.is_closed()
    guilds = len(bot.guilds)
        redis_ok = bool(getattr(bot, "cache", None) and getattr(bot.cache, "redis_client", None))
        db_ok = bool(getattr(bot, "db", None))

    services = [
        {
            "name": "Discord Gateway",
            "status": "offline" if closed else "operational",
            "details": f"{latency_ms if latency_ms is not None else '--'} ms latency",
        },
        {
            "name": "SQLite Database",
            "status": "operational" if db_ok else "offline",
            "details": "Confession storage",
        },
        {
            "name": "Redis Cache",
            "status": "operational" if redis_ok else "degraded",
            "details": "Rate limits and hot paths",
        },
    ]
    degraded = closed or not db_ok
    return {
        "bot": "confession",
        "status": "degraded" if degraded else "operational",
        "latency_ms": latency_ms,
        "guilds": guilds,
        "users": sum(getattr(g, "member_count", 0) or 0 for g in bot.guilds),
        "uptime_seconds": int(time.time() - started),
        "services": services,
        "checked_at": int(time.time()),
    }


async def start_status_api(bot: "ConfessionBot") -> web.AppRunner | None:
    port = int(os.getenv("STATUS_API_PORT", "8082") or "0")
    if port <= 0:
        log.info("STATUS_API_PORT disabled — skipping status API")
        return None

    bot._status_started_at = time.time()
    app = web.Application()

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"ok": True, "bot": "confession"})

    async def status(_: web.Request) -> web.Response:
        return web.json_response(_payload(bot))

    app.router.add_get("/health", health)
    app.router.add_get("/api/status", status)
    app.router.add_get("/status", status)

    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, os.getenv("STATUS_API_HOST", "0.0.0.0"), port)
    await site.start()
    log.info("Status API listening on port %s", port)
    return runner


async def stop_status_api(runner: web.AppRunner | None) -> None:
    if runner is None:
        return
    await runner.cleanup()
