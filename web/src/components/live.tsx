"use client";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

/** Écoute /api/stream et rafraîchit la page (sans perte de l'état local) quand les données changent. */
export function LiveRefresh() {
  const router = useRouter();
  const version = useRef<string | null>(null);
  const [state, setState] = useState<"on" | "off">("off");
  const [updated, setUpdated] = useState<Date | null>(null);

  useEffect(() => {
    let es: EventSource | null = null;
    let retry: ReturnType<typeof setTimeout>;
    const connect = () => {
      es = new EventSource("/api/stream");
      es.onopen = () => setState("on");
      es.addEventListener("version", (e) => {
        const v = (e as MessageEvent).data;
        if (version.current !== null && version.current !== v) {
          router.refresh();
          setUpdated(new Date());
        }
        version.current = v;
      });
      es.onerror = () => {
        setState("off");
        es?.close();
        retry = setTimeout(connect, 5_000);
      };
    };
    connect();
    return () => {
      clearTimeout(retry);
      es?.close();
    };
  }, [router]);

  return (
    <span className="inline-flex items-center gap-2 text-xs text-muted" title="Données mises à jour automatiquement">
      <span className={`h-2 w-2 rounded-full ${state === "on" ? "animate-pulse bg-win" : "bg-loss"}`} />
      {state === "on" ? "Temps réel" : "Reconnexion…"}
      {updated && <span>· maj {updated.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}</span>}
    </span>
  );
}
