"use client";
import { Star } from "lucide-react";
import { useOptimistic, useTransition } from "react";
import { toggleFavorite } from "@/server/actions/favorites";

export function FavoriteButton({ kind, refId, initial, label }: { kind: "match" | "team" | "league"; refId: string; initial: boolean; label?: string }) {
  const [on, setOn] = useOptimistic(initial);
  const [pending, start] = useTransition();
  return (
    <button
      type="button"
      aria-pressed={on}
      aria-label={on ? "Retirer des favoris" : "Ajouter aux favoris"}
      disabled={pending}
      onClick={() =>
        start(async () => {
          setOn(!on);
          const r = await toggleFavorite(kind, refId);
          if (r.error) alert(r.error);
        })
      }
      className="inline-flex items-center gap-1.5 rounded-md p-1 text-muted hover:text-warn"
    >
      <Star size={16} fill={on ? "var(--warn)" : "none"} color={on ? "var(--warn)" : "currentColor"} />
      {label && <span className="text-xs">{label}</span>}
    </button>
  );
}
