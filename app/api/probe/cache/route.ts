// P1a deployed probe: is Vercel Runtime Cache usable on this plan (for the per-instance spend counter)?
import { getCache } from "@vercel/functions";

export const dynamic = "force-dynamic";

export async function GET() {
  const t0 = Date.now();
  try {
    const cache = getCache();
    const key = "probe-counter";
    const prev = ((await cache.get(key)) as number | undefined) ?? 0;
    await cache.set(key, prev + 1, { ttl: 3600 });
    const now = (await cache.get(key)) as number | undefined;
    return Response.json({ ok: true, prev, now, ms: Date.now() - t0 });
  } catch (e) {
    return Response.json({ ok: false, error: String(e).slice(0, 300), ms: Date.now() - t0 });
  }
}
