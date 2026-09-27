import { syncOnce } from "@/server/sync";

export const dynamic = "force-dynamic";

/** Déclenché par un planificateur externe (ex. Vercel Cron) : Authorization: Bearer CRON_SECRET. */
export async function GET(request: Request) {
  const secret = process.env.CRON_SECRET;
  if (!secret || request.headers.get("authorization") !== `Bearer ${secret}`)
    return Response.json({ error: "Non autorisé" }, { status: 401 });
  try {
    return Response.json(await syncOnce());
  } catch (e) {
    return Response.json({ error: String(e) }, { status: 500 });
  }
}
