import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { and, asc, desc, eq, gte, ilike, inArray, isNotNull, lte, or, sql } from "drizzle-orm";
import { db, schema } from "@/lib/db";
import type { Market, MatchInfo, Status } from "@/lib/engine/types";

export const today = () => new Date().toISOString().slice(0, 10);
export const addDays = (d: string, n: number) => {
  const x = new Date(`${d}T12:00:00Z`);
  x.setUTCDate(x.getUTCDate() + n);
  return x.toISOString().slice(0, 10);
};

export const toMarket = (p: typeof schema.predictions.$inferSelect): Market => ({
  matchId: p.matchId, key: p.key, group: p.group, label: p.label, p: p.p, confidence: p.confidence,
  fairOdds: p.fairOdds, odds: p.odds, value: p.value, status: p.status as Status,
});

export async function leagues() {
  return db.select().from(schema.leagues).orderBy(asc(schema.leagues.name));
}

/** Première date à venir qui a des matchs (les données du moteur peuvent commencer plus tard qu'aujourd'hui). */
export async function nextMatchDate(from = today()) {
  const [r] = await db
    .select({ d: sql<string>`min(${schema.matches.date})` })
    .from(schema.matches)
    .where(gte(schema.matches.date, from));
  return r?.d ?? from;
}

export interface MatchFilter {
  from?: string;
  to?: string;
  league?: string;
  ids?: string[];
  q?: string;
}

export async function listMatches(f: MatchFilter = {}) {
  const where = [
    f.from ? gte(schema.matches.date, f.from) : undefined,
    f.to ? lte(schema.matches.date, f.to) : undefined,
    f.league ? eq(schema.matches.league, f.league) : undefined,
    f.ids ? inArray(schema.matches.id, f.ids.length ? f.ids : ["-"]) : undefined,
    f.q ? or(ilike(schema.matches.home, `%${f.q}%`), ilike(schema.matches.away, `%${f.q}%`)) : undefined,
  ].filter(Boolean);
  return db
    .select({ m: schema.matches, leagueName: schema.leagues.name })
    .from(schema.matches)
    .innerJoin(schema.leagues, eq(schema.leagues.code, schema.matches.league))
    .where(and(...where))
    .orderBy(asc(schema.matches.date), asc(schema.matches.time), asc(schema.matches.home))
    .limit(500);
}

export async function marketsFor(ids: string[]) {
  const map = new Map<string, Market[]>();
  if (!ids.length) return map;
  const rows = await db.select().from(schema.predictions).where(inArray(schema.predictions.matchId, ids));
  for (const r of rows) {
    const list = map.get(r.matchId) ?? [];
    list.push(toMarket(r));
    map.set(r.matchId, list);
  }
  return map;
}

/** Option la plus sûre à afficher sur une carte de match (70-98 %, hors score exact), comme le moteur. */
export function topPick(markets: Market[] = []) {
  const ok = markets.filter((m) => m.p >= 0.7 && m.p <= 0.98 && !m.key.startsWith("CS"));
  return ok.length ? ok.reduce((a, b) => (b.confidence > a.confidence ? b : a)) : null;
}

export async function matchPool(from: string, to: string, league?: string) {
  const rows = await listMatches({ from, to, league });
  const infos: MatchInfo[] = rows
    .filter((r) => r.m.scoreHome === null)
    .map(({ m }) => ({ id: m.id, league: m.league, date: m.date, time: m.time, home: m.home, away: m.away }));
  return { infos, markets: await marketsFor(infos.map((i) => i.id)) };
}

export async function getMatch(id: string) {
  const [row] = await db
    .select({ m: schema.matches, leagueName: schema.leagues.name })
    .from(schema.matches)
    .innerJoin(schema.leagues, eq(schema.leagues.code, schema.matches.league))
    .where(eq(schema.matches.id, id));
  if (!row) return null;
  const [preds, odds, snaps, tracked] = await Promise.all([
    db.select().from(schema.predictions).where(eq(schema.predictions.matchId, id)),
    db.select().from(schema.oddsSnapshots).where(eq(schema.oddsSnapshots.matchId, id)).orderBy(asc(schema.oddsSnapshots.takenAt)),
    db
      .select({ generated: schema.predictionSnapshots.generated, takenAt: schema.predictionSnapshots.takenAt, markets: schema.predictionSnapshots.markets })
      .from(schema.predictionSnapshots)
      .where(eq(schema.predictionSnapshots.matchId, id))
      .orderBy(asc(schema.predictionSnapshots.takenAt)),
    db.select().from(schema.trackedPicks).where(eq(schema.trackedPicks.matchId, id)),
  ]);
  return { ...row, predictions: preds, odds, snapshots: snaps, tracked: tracked[0] ?? null };
}

export async function valueBets(minValue = 0.03, minP = 0.4) {
  return db
    .select({ p: schema.predictions, m: schema.matches })
    .from(schema.predictions)
    .innerJoin(schema.matches, eq(schema.matches.id, schema.predictions.matchId))
    .where(and(gte(schema.predictions.value, minValue), gte(schema.predictions.p, minP), gte(schema.matches.date, today())))
    .orderBy(desc(sql`${schema.predictions.value} * ${schema.predictions.confidence}`))
    .limit(200);
}

export async function valueBetCount() {
  const [r] = await db
    .select({ n: sql<number>`count(*)::int` })
    .from(schema.predictions)
    .innerJoin(schema.matches, eq(schema.matches.id, schema.predictions.matchId))
    .where(and(gte(schema.predictions.value, 0.03), gte(schema.matches.date, today())));
  return r?.n ?? 0;
}

export async function teams(q: string) {
  const rows = await db.execute<{ team: string; league: string; league_name: string }>(sql`
    select distinct t.team, t.league, l.name as league_name from (
      select home as team, league from matches union select away, league from matches
    ) t join leagues l on l.code = t.league where t.team ilike ${`%${q}%`} order by t.team limit 30`);
  return rows.rows;
}

export async function lastSync() {
  const [r] = await db.select().from(schema.syncRuns).where(isNotNull(schema.syncRuns.finishedAt)).orderBy(desc(schema.syncRuns.id)).limit(1);
  return r ?? null;
}

/** Version des données : change à chaque synchronisation qui modifie quelque chose. */
export async function dataVersion() {
  const [r] = await db
    .select({ v: sql<number>`coalesce(max(${schema.syncRuns.id}), 0)::int` })
    .from(schema.syncRuns)
    .where(sql`${schema.syncRuns.changed} + ${schema.syncRuns.oddsMoves} + ${schema.syncRuns.settled} > 0`);
  return r?.v ?? 0;
}

export async function trackRecord() {
  const rows = await db.select().from(schema.trackedPicks).orderBy(desc(schema.trackedPicks.date)).limit(2000);
  const settled = rows.filter((r) => r.status === "V" || r.status === "P");
  return {
    frozen: rows.length,
    settled: settled.length,
    won: settled.filter((r) => r.status === "V").length,
    meanP: settled.length ? settled.reduce((a, r) => a + (r.p ?? 0), 0) / settled.length : null,
    recent: rows.filter((r) => r.scoreHome !== null).slice(0, 40),
    upcoming: rows.filter((r) => r.scoreHome === null && r.key).reverse().slice(0, 20),
  };
}

/** Backtest et calibration produits par le moteur (fichiers JSON du dossier de données). */
export async function backtest() {
  try {
    const dir = path.resolve(/*turbopackIgnore: true*/ process.cwd(), process.env.OMNISCORE_DATA_DIR ?? "../backend/data");
    return JSON.parse(await readFile(path.join(dir, "backtest.json"), "utf8")) as BacktestFile;
  } catch {
    return null;
  }
}

export interface Metrics {
  log_loss: number;
  brier: number;
  rps: number;
  accuracy: number;
}
export interface BacktestFile {
  leagues: Record<string, string>;
  test_seasons: string[];
  all_seasons: {
    n: number;
    base: Metrics;
    elo: Metrics;
    dc: Metrics;
    blend: Metrics;
    calibration_all_markets: { tranche: string; n: number; annonce: number | null; observe: number | null }[];
    top_picks: { n: number; hit_rate: number; mean_p: number; by_market: { market: string; n: number; mean_p: number; hit_rate: number }[] };
    coupons: Record<string, { coupons: number; predicted_win_rate: number; observed_win_rate: number }>;
  };
}

export async function favoritesOf(userId: string) {
  return db.select().from(schema.favorites).where(eq(schema.favorites.userId, userId)).orderBy(desc(schema.favorites.createdAt));
}

export async function userCoupons(userId: string) {
  const cs = await db.select().from(schema.coupons).where(eq(schema.coupons.userId, userId)).orderBy(desc(schema.coupons.createdAt)).limit(100);
  const items = cs.length
    ? await db.select().from(schema.couponItems).where(inArray(schema.couponItems.couponId, cs.map((c) => c.id)))
    : [];
  return cs.map((c) => ({ ...c, items: items.filter((i) => i.couponId === c.id) }));
}
