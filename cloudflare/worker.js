/**
 * Cloudflare Worker edge shim.
 *
 * This isolate terminates TLS at a PoP, stamps shard/geo headers, and
 * proxies to the FastAPI origin. D1 is the SQLite-compatible shard.
 */

const RATE_LIMIT = 50000;

const shardByCountry = {
  GB: "shard_emea_01",
  JP: "shard_apac_01",
  US: "shard_amer_01",
  BR: "shard_latam_01",
  AE: "shard_mea_01",
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const country = request.cf?.country || "US";
    const colo = request.cf?.colo || "IAD";
    const shard = shardByCountry[country] || "shard_amer_01";

    if (url.pathname === "/ops/edge") {
      return Response.json({
        colo,
        country,
        shard,
        rate_limit_per_minute: RATE_LIMIT,
        origin: env.ORIGIN_URL || null,
      });
    }

    if (!env.ORIGIN_URL) {
      return new Response("ORIGIN_URL is not configured", { status: 500 });
    }

    const origin = new URL(url.pathname + url.search, env.ORIGIN_URL);
    const headers = new Headers(request.headers);
    headers.set("X-Mesh-Shard", shard);
    headers.set("X-Mesh-Colo", colo);

    const inbound = new Request(origin, {
      method: request.method,
      headers,
      body: request.body,
      redirect: "follow",
    });
    const response = await fetch(inbound);
    const outbound = new Response(response.body, response);
    outbound.headers.set("X-Mesh-Shard", shard);
    outbound.headers.set("X-Mesh-Colo", colo);
    outbound.headers.set("Cache-Control", "public, max-age=30");
    return outbound;
  },
};
