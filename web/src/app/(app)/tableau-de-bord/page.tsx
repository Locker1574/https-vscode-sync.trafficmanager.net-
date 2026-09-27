import type { Metadata } from "next";
import Link from "next/link";
import { MatchCard } from "@/components/match-card";
import { Disclaimer, Empty, PageHeader, Stat } from "@/components/ui";
import { requireUser } from "@/lib/auth/session";
import { dateLabel, pct } from "@/lib/format";
import { cards } from "@/server/cards";
import { addDays, favoritesOf, lastSync, listMatches, nextMatchDate, trackRecord, valueBetCount } from "@/server/data";

export const metadata: Metadata = { title: "Tableau de bord" };

export default async function Dashboard() {
  const user = await requireUser();
  const day = await nextMatchDate();
  const [rows, vb, track, sync, favs] = await Promise.all([
    listMatches({ from: day, to: day }),
    valueBetCount(),
    trackRecord(),
    lastSync(),
    favoritesOf(user.id),
  ]);
  const all = await cards(rows, user.id);
  const best = all.filter((c) => c.top).sort((a, b) => b.top!.confidence - a.top!.confidence).slice(0, 6);
  const favIds = favs.filter((f) => f.kind === "match").map((f) => f.ref);
  const favRows = favIds.length ? await listMatches({ ids: favIds, from: day, to: addDays(day, 30) }) : [];
  const favCards = await cards(favRows.slice(0, 6), user.id);

  return (
    <>
      <PageHeader title={`Bonjour ${user.name}`} subtitle={`Prochaine journée : ${dateLabel(day)}`}>
        <Link href="/coupons" className="btn-primary">Générer un coupon</Link>
      </PageHeader>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Matchs de la journée" value={rows.length} />
        <Stat label="Value bets" value={vb} hint={vb ? "cotes réelles disponibles" : "aucune cote réelle chargée"} />
        <Stat
          label="Journal réel"
          value={track.settled ? pct(track.won / track.settled) : "–"}
          hint={track.settled ? `${track.won}/${track.settled} validés · annoncé ${pct(track.meanP ?? 0)}` : `${track.frozen} prédictions figées, en attente des résultats`}
        />
        <Stat
          label="Dernière mise à jour"
          value={sync?.finishedAt ? sync.finishedAt.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }) : "–"}
          hint={sync?.generated ? `modèle du ${sync.generated}` : undefined}
        />
      </div>

      <h2 className="mb-3 mt-8 text-lg font-semibold">Plus forte confiance · {dateLabel(day)}</h2>
      {best.length ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{best.map((c) => <MatchCard key={c.id} m={c} />)}</div>
      ) : (
        <Empty>Aucune prédiction pour cette journée. Lancez une synchronisation (npm run sync).</Empty>
      )}

      {favCards.length > 0 && (
        <>
          <h2 className="mb-3 mt-8 text-lg font-semibold">Vos matchs suivis</h2>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{favCards.map((c) => <MatchCard key={c.id} m={c} />)}</div>
        </>
      )}
      <div className="mt-10"><Disclaimer /></div>
    </>
  );
}
