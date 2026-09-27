import Link from "next/link";
import { Lock, LockOpen } from "lucide-react";
import type { Selection } from "@/lib/engine/types";
import { odds, shortDate } from "@/lib/format";
import { ConfidenceBar, Prob, StatusBadge } from "./ui";

export function SelectionRow({ s, onLock, showStatus }: { s: Selection; onLock?: () => void; showStatus?: boolean }) {
  return (
    <div className={`flex flex-wrap items-center gap-3 rounded-lg border p-3 text-sm ${s.isNew ? "border-accent/60 bg-accent/5" : "border-line bg-panel"}`}>
      {onLock && (
        <button type="button" onClick={onLock} aria-label={s.locked ? "Déverrouiller" : "Verrouiller"} className={s.locked ? "text-warn" : "text-muted"}>
          {s.locked ? <Lock size={16} /> : <LockOpen size={16} />}
        </button>
      )}
      <div className="min-w-0 flex-1">
        <Link href={`/match/${encodeURIComponent(s.matchId)}`} className="block truncate font-semibold hover:text-accent">{s.match}</Link>
        <div className="text-xs text-muted">
          <span className="capitalize">{shortDate(s.date)}</span> {s.time} · {s.label}
          {s.isNew && <span className="ml-2 font-semibold text-accent">nouveau</span>}
        </div>
      </div>
      <div className="w-28"><ConfidenceBar value={s.confidence} /></div>
      <Prob p={s.p} />
      <span className="num w-12 text-right text-muted">@{odds(s.odds ?? s.fairOdds)}</span>
      {showStatus && <StatusBadge status={s.status} />}
    </div>
  );
}
