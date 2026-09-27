import { dataVersion } from "@/server/data";

export const dynamic = "force-dynamic";

/** Temps réel (Server-Sent Events) : envoie la version des données dès qu'une synchronisation change quelque chose. */
export async function GET(request: Request) {
  const encoder = new TextEncoder();
  let timer: ReturnType<typeof setInterval> | undefined;
  const stream = new ReadableStream({
    async start(controller) {
      let last = -1;
      let closed = false;
      const send = (s: string) => {
        if (closed) return;
        try {
          controller.enqueue(encoder.encode(s));
        } catch {
          closed = true;
          clearInterval(timer);
        }
      };
      const push = async () => {
        try {
          const v = await dataVersion();
          if (v !== last) {
            last = v;
            send(`event: version\ndata: ${v}\n\n`);
          } else send(`: ping\n\n`);
        } catch {
          send(`: erreur\n\n`);
        }
      };
      await push();
      timer = setInterval(push, 10_000);
      request.signal.addEventListener("abort", () => {
        closed = true;
        clearInterval(timer);
        try {
          controller.close();
        } catch {}
      });
    },
    cancel() {
      clearInterval(timer);
    },
  });
  return new Response(stream, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache, no-transform", Connection: "keep-alive" },
  });
}
