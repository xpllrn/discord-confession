export async function onRequestGet(context) {
  const origins = [
    context.env.STATUS_API_ORIGIN,
    "https://api.confess.adore.rest",
  ].filter(Boolean);
  for (const origin of origins) {
    try {
      const res = await fetch(origin.replace(/\/$/, "") + "/api/status", {
        headers: { Accept: "application/json" },
        cf: { cacheTtl: 5 },
      });
      if (res.ok) {
        const body = await res.text();
        return new Response(body, {
          status: 200,
          headers: {
            "content-type": "application/json",
            "cache-control": "public, max-age=5",
            "access-control-allow-origin": "*",
          },
        });
      }
    } catch (_) {}
  }
  return new Response(JSON.stringify({
    bot: "confession",
    status: "offline",
    latency_ms: null,
    guilds: null,
    users: null,
    uptime_seconds: null,
    services: [{ name: "Status API", status: "offline", details: "Upstream unreachable" }],
    checked_at: Math.floor(Date.now() / 1000),
  }), {
    status: 503,
    headers: { "content-type": "application/json", "access-control-allow-origin": "*" },
  });
}
