import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { FavoriteButton } from "@/components/favorite-button";
import { ConfidenceBar, Disclaimer, PageHeader, Prob, Stat, StatusBadge } from "@/components/ui";
import { requireUser } from "@/lib/auth/session";
import { dateLabel, odds, pct } from "@/lib/format";
import { favoritesOf, getMatch } from "@/server/data";

export async function generateMetadata({ params }: PageProps<"/match/[id]">): Promise<Metadata> {
  const m = await getMatch(decodeURIComponent((await params).id));
  return { title: m ? `${m.m.home} – ${m.m.away}` : "Match" };
}

const GROUP_ORDER = ["Résultat", "Buts", "Équipes", "1re mi-temps", "Score exact"];

export default async function MatchPage({ params }: PageProps<"/match/[id]">) {
  const user = await requireUser();
  const data = await getMatch(decodeURIComponent((await params).id));
  if (!data) notFound();
  const { m, leagueName, predictions, odds: history, snapshots, tracked } = data;
  const favs = await favoritesOf(user.id);
  const isFav = (kind: string, ref: string) => favs.some((f) => f.kind === kind && f.ref === ref);

  // Mouvement de cote : dernière cote comparée à la précédente pour chaque marché.
  const moves = new Map<string, { first: number; last: number; n: number }>();
  for (const o of history) {
    const cur = moves.get(o.key);
    moves.set(o.key, cur ? { ...cur, last: o.odds, n: cur.n + 1 } : { first: o.odds, last: o.odds, n: 1 });
  }
  // Évolution des probabilités entre la première et la dernière version du modèle.
  const firstSnap = snapshots[0]?.markets as { key: string; p: number }[] | undefined;
  const firstP = new Map(firstSnap?.map((x) => [x.key, x.p]) ?? []);

  const groups = GROUP_ORDER.map((g) => ({
    g,
    rows: predictions.filter((p) => p.group === g).sort((a, b) => b.p - a.p),
  })).filter((x) => x.rows.length);
  const get = (k: string) => predictions.find((p) => p.key === k);
  const eloDiff = m.eloHome != null && m.eloAway != null ? m.eloHome - m.eloAway : null;

  return (
    <>
      <PageHeader title={`${m.home} – ${m.away}`} subtitle={`${leagueName} · ${dateLabel(m.date)} · ${m.time ?? ""} ${m.round ? `· ${m.round}` : ""}`}>
        <div className="flex gap-2">
          <FavoriteButton kind="match" refId={m.id} initial={isFav("match", m.id)} label="Match" />
          <FavoriteButton kind="team" refId={m.home} initial={isFav("team", m.home)} label={m.home} />
          <FavoriteButton kind="team" refId={m.away} initial={isFav("team", m.away)} label={m.away} />
        </div>
      </PageHeader>

      {m.scoreHome !== null && (
        <div className="card mb-4 p-4 text-center text-3xl font-black num">
          {m.scoreHome} – {m.scoreAway}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="1 · X · 2" value={[get("1"), get("X"), get("2")].map((x) => (x ? Math.round(x.p * 100) : "–")).join(" · ")} hint="probabilités calibrées (%)" />
        <Stat label="Buts attendus" value={`${m.xgHome?.toFixed(2) ?? "–"} – ${m.xgAway?.toFixed(2) ?? "–"}`} hint="modèle Dixon-Coles" />
        <Stat label="Elo" value={`${m.eloHome ?? "–"} – ${m.eloAway ?? "–"}`} hint={eloDiff != null ? `écart ${eloDiff > 0 ? "+" : ""}${eloDiff}` : undefined} />
        <Stat
          label="Accord des modèles"
          value={m.modelAgreement != null ? pct(m.modelAgreement) : "–"}
          hint={`données complètes à ${m.dataCompleteness != null ? pct(m.dataCompleteness) : "–"} · ${snapshots.length} version(s)`}
        />
      </div>

      {tracked?.key && (
        <div className="card mt-4 flex flex-wrap items-center justify-between gap-2 p-4 text-sm">
          <span>
            <span className="text-muted">Sélection figée le {tracked.frozen} (journal réel) :</span> <strong>{tracked.label}</strong> · {pct(tracked.p ?? 0)}
          </span>
          <StatusBadge status={tracked.status} />
        </div>
      )}

      <div className="mt-6 space-y-6">
        {groups.map(({ g, rows }) => (
          <section key={g} className="card overflow-hidden">
            <h2 className="border-b border-line px-4 py-3 font-semibold">{g}</h2>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-sm">
                <thead className="text-left text-xs text-muted">
                  <tr>
                    <th className="px-4 py-2 font-medium">Option</th>
                    <th className="px-2 py-2 font-medium">Probabilité</th>
                    <th className="w-40 px-2 py-2 font-medium">Confiance</th>
                    <th className="px-2 py-2 font-medium">Cote juste</th>
                    <th className="px-2 py-2 font-medium">Cote marché</th>
                    <th className="px-2 py-2 font-medium">Value</th>
                    <th className="px-4 py-2 font-medium">Statut</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((p) => {
                    const mv = moves.get(p.key);
                    const dp = firstP.has(p.key) ? p.p - firstP.get(p.key)! : 0;
                    return (
                      <tr key={p.key} className="border-t border-line/60">
                        <td className="px-4 py-2">{p.label}</td>
                        <td className="px-2 py-2">
                          <Prob p={p.p} />
                          {Math.abs(dp) >= 0.005 && (
                            <span className={`ml-1 text-xs ${dp > 0 ? "text-win" : "text-loss"}`}>
                              {dp > 0 ? "+" : ""}{(dp * 100).toFixed(1)}
                            </span>
                          )}
                        </td>
                        <td className="px-2 py-2"><ConfidenceBar value={p.confidence} /></td>
                        <td className="num px-2 py-2">{odds(p.fairOdds)}</td>
                        <td className="num px-2 py-2">
                          {odds(p.odds)}
                          {mv && mv.n > 1 && mv.last !== mv.first && (
                            mv.last < mv.first ? <ArrowDownRight className="ml-1 inline text-loss" size={14} /> : <ArrowUpRight className="ml-1 inline text-win" size={14} />
                          )}
                          {p.bookmaker && <span className="ml-1 text-xs text-muted">{p.bookmaker}</span>}
                        </td>
                        <td className="num px-2 py-2">
                          {p.value != null ? (
                            <span className={p.value > 0.03 ? "font-semibold text-win" : "text-muted"}>{(p.value * 100).toFixed(1)} %</span>
                          ) : "–"}
                        </td>
                        <td className="px-4 py-2">{m.scoreHome !== null && <StatusBadge status={p.status} />}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        ))}
      </div>
      <div className="mt-6 text-xs text-muted">
        Confiance = probabilité pondérée par l&apos;accord entre modèles et la complétude des données. Cote juste = 1 / probabilité.
        Value = probabilité × cote du marché − 1 (affichée quand des cotes réelles sont chargées).
      </div>
      <div className="mt-4"><Disclaimer /></div>
    </>
  );
}
