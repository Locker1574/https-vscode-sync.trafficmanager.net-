import Link from "next/link";
import type { Market } from "@/lib/engine/types";
import { odds } from "@/lib/format";
import { FavoriteButton } from "./favorite-button";
import { ConfidenceBar, Prob, StatusBadge } from "./ui";

export interface MatchCardData {
  id: string;
  league: string;
  leagueName: string;
  time: string | null;
  home: string;
  away: string;
  scoreHome: number | null;
  scoreAway: number | null;
  p1x2: [number, number, number] | null;
  top: (Market & { status?: string | null }) | null;
  favorite: boolean;
}

export function MatchCard({ m }: { m: MatchCardData }) {
  const played = m.scoreHome !== null;
  return (
    <div className="card flex flex-col gap-3 p-4 transition hover:border-accent/60">
      <div className="flex items-center justify-between text-xs text-muted">
        <span>
          {m.leagueName} · {m.time ?? "–"}
        </span>
        <FavoriteButton kind="match" refId={m.id} initial={m.favorite} />
      </div>
      <Link href={`/match/${encodeURIComponent(m.id)}`} className="flex items-center justify-between gap-3">
        <div className="min-w-0 space-y-1 text-sm font-semibold">
          <div className="truncate">{m.home}</div>
          <div className="truncate">{m.away}</div>
        </div>
        {played ? (
          <div className="num space-y-1 text-right text-lg font-bold">
            <div>{m.scoreHome}</div>
            <div>{m.scoreAway}</div>
          </div>
        ) : (
          m.p1x2 && (
            <div className="num grid grid-cols-3 gap-1 text-center text-xs">
              {(["1", "X", "2"] as const).map((k, i) => (
                <div key={k} className="rounded-md bg-panel-2 px-2 py-1">
                  <div className="text-muted">{k}</div>
                  <div className="font-semibold">{Math.round(m.p1x2![i] * 100)}</div>
                </div>
              ))}
            </div>
          )
        )}
      </Link>
      {m.top && (
        <div className="rounded-lg bg-panel-2 p-2.5">
          <div className="flex items-center justify-between gap-2 text-sm">
            <span className="truncate">{m.top.label}</span>
            <span className="flex items-center gap-2">
              <Prob p={m.top.p} />
              <span className="num text-xs text-muted">@{odds(m.top.odds ?? m.top.fairOdds)}</span>
              {played && <StatusBadge status={m.top.status} />}
            </span>
          </div>
          <div className="mt-1.5">
            <ConfidenceBar value={m.top.confidence} />
          </div>
        </div>
      )}
    </div>
  );
}
