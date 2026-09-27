/** Synchronisation automatique en arrière-plan (serveur Node auto-hébergé). */
export async function register() {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;
  const minutes = Number(process.env.SYNC_INTERVAL_MINUTES ?? 0);
  if (!minutes || !process.env.DATABASE_URL) return;
  const { syncOnce } = await import("./server/sync");
  let running = false;
  const run = async () => {
    if (running) return;
    running = true;
    try {
      await syncOnce();
    } catch (e) {
      console.error("[sync]", e);
    } finally {
      running = false;
    }
  };
  setTimeout(run, 5_000);
  setInterval(run, minutes * 60_000);
}
