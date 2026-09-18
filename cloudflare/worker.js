/**
 * Cloudflare Worker edge shim.
 *
 * This isolate terminates TLS at a PoP, stamps shard/geo headers, and
 * proxies to the FastAPI origin. D1 is the SQLite-compatible shard.
 *
 * Upstream URLs are pinned to ORIGIN_URL's origin. `new URL(pathname, origin)`
 * treats protocol-relative paths (`//host/...`) as a different host, which
 * would otherwise turn this Worker into an open proxy that forwards cookies.
 */

const RATE_LIMIT = 50000;

const shardByCountry = {
  GB: "shard_emea_01",
  JP: "shard_apac_01",
  US: "shard_amer_01",
  BR: "shard_latam_01",
  AE: "shard_mea_01",
};

export function resolveUpstream(requestUrl, originUrl) {
  let incoming;
  let base;
  try {
    incoming = new URL(requestUrl);
    base = new URL(originUrl);
  } catch {
    return null;
  }
  const target = new URL(`${incoming.pathname}${incoming.search}`, base);
  if (target.origin !== base.origin) {
    return null;
  }
  return target;
}

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

    const origin = resolveUpstream(request.url, env.ORIGIN_URL);
    if (!origin) {
      return new Response("Invalid path", { status: 400 });
    }

    const headers = new Headers(request.headers);
    headers.set("X-Mesh-Shard", shard);
    headers.set("X-Mesh-Colo", colo);
    headers.delete("Host");

    const inbound = new Request(origin, {
      method: request.method,
      headers,
      body: request.body,
      redirect: "manual",
    });
    const response = await fetch(inbound);
    const outbound = new Response(response.body, response);
    outbound.headers.set("X-Mesh-Shard", shard);
    outbound.headers.set("X-Mesh-Colo", colo);
    return outbound;
  },
};
