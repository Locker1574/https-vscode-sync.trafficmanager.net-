import type { Metadata } from "next";
import { FavoriteButton } from "@/components/favorite-button";
import { MatchCard } from "@/components/match-card";
import { Empty, PageHeader } from "@/components/ui";
import { requireUser } from "@/lib/auth/session";
import { cards } from "@/server/cards";
import { favoritesOf, listMatches, teams, today } from "@/server/data";

export const metadata: Metadata = { title: "Recherche" };

export default async function Search({ searchParams }: PageProps<"/recherche">) {
  const user = await requireUser();
  const raw = (await searchParams).q;
  const q = (typeof raw === "string" ? raw : "").trim().slice(0, 60);
  const [ts, rows, favs] = q.length >= 2
    ? await Promise.all([teams(q), listMatches({ q, from: today() }), favoritesOf(user.id)])
    : [[], [], []];
  const list = await cards(rows.slice(0, 30), user.id);
  const favTeams = new Set(favs.filter((f) => f.kind === "team").map((f) => f.ref));
  return (
    <>
      <PageHeader title="Recherche" />
      <form className="mb-6 flex gap-2">
        <input name="q" defaultValue={q} placeholder="Équipe, par ex. Arsenal, Lyon, Benfica…" className="input" autoFocus />
        <button className="btn-primary">Rechercher</button>
      </form>
      {q.length >= 2 && (
        <>
          <h2 className="mb-3 text-lg font-semibold">Équipes</h2>
          {ts.length ? (
            <div className="mb-8 flex flex-wrap gap-2">
              {ts.map((t) => (
                <span key={t.team} className="card flex items-center gap-2 py-1 pl-3 pr-1 text-sm">
                  {t.team} <span className="text-xs text-muted">{t.league_name}</span>
                  <FavoriteButton kind="team" refId={t.team} initial={favTeams.has(t.team)} />
                </span>
              ))}
            </div>
          ) : <p className="mb-8 text-sm text-muted">Aucune équipe.</p>}
          <h2 className="mb-3 text-lg font-semibold">Prochains matchs</h2>
          {list.length ? <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{list.map((c) => <MatchCard key={c.id} m={c} />)}</div> : <Empty>Aucun match à venir.</Empty>}
        </>
      )}
    </>
  );
}
