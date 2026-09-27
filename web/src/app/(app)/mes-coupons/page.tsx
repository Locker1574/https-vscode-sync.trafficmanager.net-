import type { Metadata } from "next";
import { SelectionRow } from "@/components/selection-row";
import { Empty, PageHeader, Stat, StatusBadge } from "@/components/ui";
import { requireUser } from "@/lib/auth/session";
import { MODE_LABEL, odds, pct } from "@/lib/format";
import { userCoupons } from "@/server/data";

export const metadata: Metadata = { title: "Mes coupons" };

export default async function MyCoupons() {
  const user = await requireUser();
  const list = await userCoupons(user.id);
  const settled = list.filter((c) => c.status === "V" || c.status === "P");
  const won = settled.filter((c) => c.status === "V");
  return (
    <>
      <PageHeader title="Mes coupons" subtitle="Réglés automatiquement dès que les résultats officiels arrivent." />
      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Coupons" value={list.length} />
        <Stat label="Réglés" value={settled.length} />
        <Stat label="Validés" value={settled.length ? pct(won.length / settled.length) : "–"} hint={`${won.length}/${settled.length}`} />
        <Stat label="Réussite annoncée" value={settled.length ? pct(settled.reduce((a, c) => a + c.combinedProbability, 0) / settled.length) : "–"} hint="moyenne des probabilités combinées" />
      </div>
      {!list.length ? (
        <Empty>Aucun coupon enregistré. Générez-en un dans « Coupon du jour » ou « Combo ».</Empty>
      ) : (
        <div className="space-y-4">
          {list.map((c) => (
            <div key={c.id} className="card p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-sm">
                <span>
                  <strong>{c.kind === "combo" ? "Combo" : "Coupon du jour"}</strong>
                  <span className="text-muted"> · {MODE_LABEL[c.mode] ?? c.mode} · {c.createdAt.toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" })}</span>
                </span>
                <span className="flex items-center gap-3">
                  <span className="num">{pct(c.combinedProbability, 1)} · @{odds(c.totalOdds)}</span>
                  <StatusBadge status={c.status} />
                </span>
              </div>
              <div className="space-y-2">
                {c.items.map((it) => (
                  <SelectionRow
                    key={`${it.matchId}-${it.key}`}
                    showStatus
                    s={{ ...it, group: "", fairOdds: it.odds, odds: it.odds, value: null, date: it.matchId.split(":")[1] ?? "", time: null, status: it.status as "V" | "P" | "R" | null }}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
