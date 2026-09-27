import "server-only";
import type { MatchCardData } from "@/components/match-card";
import { favoritesOf, listMatches, marketsFor, topPick } from "./data";

type Row = Awaited<ReturnType<typeof listMatches>>[number];

/** Données des cartes de match : 1X2, meilleure option et favori. */
export async function cards(rows: Row[], userId: string): Promise<MatchCardData[]> {
  const [markets, favs] = await Promise.all([marketsFor(rows.map((r) => r.m.id)), favoritesOf(userId)]);
  const fav = new Set(favs.filter((f) => f.kind === "match").map((f) => f.ref));
  return rows.map(({ m, leagueName }) => {
    const mk = markets.get(m.id) ?? [];
    const get = (k: string) => mk.find((x) => x.key === k)?.p;
    const p1 = get("1"), px = get("X"), p2 = get("2");
    return {
      id: m.id, league: m.league, leagueName, time: m.time, home: m.home, away: m.away,
      scoreHome: m.scoreHome, scoreAway: m.scoreAway,
      p1x2: p1 != null && px != null && p2 != null ? [p1, px, p2] : null,
      top: topPick(mk),
      favorite: fav.has(m.id),
    };
  });
}

export function groupByDate<T extends { date: string }>(items: T[]) {
  const out = new Map<string, T[]>();
  for (const it of items) out.set(it.date, [...(out.get(it.date) ?? []), it]);
  return out;
}
