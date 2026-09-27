import { lastSync } from "@/server/data";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const s = await lastSync();
    return Response.json({ ok: true, lastSync: s?.finishedAt ?? null, generated: s?.generated ?? null });
  } catch (e) {
    return Response.json({ ok: false, error: String(e) }, { status: 503 });
  }
}
