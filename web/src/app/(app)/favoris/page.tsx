import type { Metadata } from "next";
import Link from "next/link";
import { FavoriteButton } from "@/components/favorite-button";
import { MatchCard } from "@/components/match-card";
import { Empty, PageHeader } from "@/components/ui";
import { requireUser } from "@/lib/auth/session";
import { cards } from "@/server/cards";
import { favoritesOf, listMatches, today } from "@/server/data";

export const metadata: Metadata = { title: "Favoris" };

export default async function Favorites() {
  const user = await requireUser();
  const favs = await favoritesOf(user.id);
  const matchIds = favs.filter((f) => f.kind === "match").map((f) => f.ref);
  const teams = favs.filter((f) => f.kind === "team").map((f) => f.ref);
  const [followed, upcoming] = await Promise.all([
    matchIds.length ? listMatches({ ids: matchIds }) : Promise.resolve([]),
    teams.length ? listMatches({ from: today() }) : Promise.resolve([]),
  ]);
  const teamMatches = upcoming.filter((r) => teams.includes(r.m.home) || teams.includes(r.m.away)).slice(0, 30);
  const [a, b] = await Promise.all([cards(followed, user.id), cards(teamMatches, user.id)]);
  return (
    <>
      <PageHeader title="Favoris et suivi" subtitle="Matchs suivis et prochains matchs de vos équipes favorites." />
      {teams.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {teams.map((t) => (
            <span key={t} className="card flex items-center gap-1 py-1 pl-3 pr-1 text-sm">
              <Link href={`/recherche?q=${encodeURIComponent(t)}`}>{t}</Link>
              <FavoriteButton kind="team" refId={t} initial />
            </span>
          ))}
        </div>
      )}
      <h2 className="mb-3 text-lg font-semibold">Matchs suivis</h2>
      {a.length ? <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{a.map((c) => <MatchCard key={c.id} m={c} />)}</div> : <Empty>Touchez l&apos;étoile d&apos;un match pour le suivre.</Empty>}
      <h2 className="mb-3 mt-8 text-lg font-semibold">Prochains matchs de vos équipes</h2>
      {b.length ? <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{b.map((c) => <MatchCard key={c.id} m={c} />)}</div> : <Empty>Ajoutez une équipe favorite depuis une fiche match ou la recherche.</Empty>}
    </>
  );
}
