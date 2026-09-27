import { readFile } from "node:fs/promises";
import path from "node:path";
import { and, eq, inArray, isNull, sql } from "drizzle-orm";
import { db, schema } from "@/lib/db";
import { dataDir } from "@/server/paths";
import { couponStatus, settle } from "@/lib/engine/settle";
import type { Status } from "@/lib/engine/types";

interface SourceMarket {
  group: string;
  key: string;
  label: string;
  p: number;
  confidence: number;
  fair_odds: number;
  odds?: number | null;
  bookmaker?: string | null;
  value?: number | null;
}
interface SourceMatch {
  id: string;
  league: string;
  league_name: string;
  date: string;
  time?: string | null;
  round?: string | null;
  home: string;
  away: string;
  xg?: { home: number; away: number };
  elo?: { home: number; away: number };
  model_agreement?: number;
  data_completeness?: number;
  markets: SourceMarket[];
}
interface TrackEntry {
  league: string;
  date: string;
  home: string;
  away: string;
  frozen: string;
  pick: { key: string; label: string; p: number; status?: Status } | null;
  result: [number, number] | null;
}
export interface SourcePayload {
  generated: string;
  matches: SourceMatch[];
  track: Record<string, TrackEntry>;
}

/** Lit les prédictions depuis l'API du moteur (OMNISCORE_API_URL) ou depuis ses fichiers JSON. */
export async function loadSource(): Promise<{ source: string; payload: SourcePayload }> {
  const api = process.env.OMNISCORE_API_URL;
  if (api) {
    const res = await fetch(`${api.replace(/\/$/, "")}/v1/export`, { cache: "no-store" });
    if (!res.ok) throw new Error(`API du moteur : HTTP ${res.status}`);
    return { source: api, payload: (await res.json()) as SourcePayload };
  }
  const dir = dataDir();
  const preds = JSON.parse(await readFile(path.join(dir, "predictions.json"), "utf8"));
  const track = JSON.parse(await readFile(path.join(dir, "track.json"), "utf8").catch(() => "{}"));
  return { source: dir, payload: { generated: preds.generated, matches: preds.matches, track } };
}

const round4 = (x: number) => Math.round(x * 10000) / 10000;

/**
 * Synchronise la base avec le moteur. Aucune donnée n'est perdue :
 * - les valeurs courantes sont mises à jour (upsert) ;
 * - chaque changement de prédiction ajoute un instantané, chaque changement de cote une ligne d'historique ;
 * - les résultats règlent les prédictions, le journal réel et les coupons des utilisateurs.
 */
export async function syncOnce() {
  const [run] = await db.insert(schema.syncRuns).values({ source: "pending" }).returning();
  try {
    const { source, payload } = await loadSource();
    const stats = await db.transaction(async (tx) => {
      let changed = 0;
      let oddsMoves = 0;
      let settled = 0;

      const leagues = new Map(payload.matches.map((m) => [m.league, m.league_name]));
      for (const t of Object.values(payload.track)) if (!leagues.has(t.league)) leagues.set(t.league, t.league);
      if (leagues.size)
        await tx
          .insert(schema.leagues)
          .values([...leagues].map(([code, name]) => ({ code, name })))
          .onConflictDoUpdate({ target: schema.leagues.code, set: { name: sql`case when excluded.name = excluded.code then leagues.name else excluded.name end` } });

      for (const m of payload.matches) {
        await tx
          .insert(schema.matches)
          .values({
            id: m.id, league: m.league, date: m.date, time: m.time ?? null, round: m.round ?? null, home: m.home, away: m.away,
            xgHome: m.xg?.home, xgAway: m.xg?.away, eloHome: m.elo?.home, eloAway: m.elo?.away,
            modelAgreement: m.model_agreement, dataCompleteness: m.data_completeness,
          })
          .onConflictDoUpdate({
            target: schema.matches.id,
            set: {
              date: m.date, time: m.time ?? null, round: m.round ?? null, xgHome: m.xg?.home, xgAway: m.xg?.away,
              eloHome: m.elo?.home, eloAway: m.elo?.away, modelAgreement: m.model_agreement,
              dataCompleteness: m.data_completeness, updatedAt: new Date(),
            },
          });

        const existing = await tx.select().from(schema.predictions).where(eq(schema.predictions.matchId, m.id));
        const prev = new Map(existing.map((e) => [e.key, e]));
        let matchChanged = existing.length !== m.markets.length;
        for (const x of m.markets) {
          const before = prev.get(x.key);
          if (!before || round4(before.p) !== round4(x.p)) matchChanged = true;
          if (x.odds && (!before || before.odds !== x.odds)) {
            await tx.insert(schema.oddsSnapshots).values({ matchId: m.id, key: x.key, odds: x.odds, bookmaker: x.bookmaker ?? null });
            oddsMoves++;
          }
        }
        if (!matchChanged) continue;
        changed++;
        await tx.insert(schema.predictionSnapshots).values({ matchId: m.id, generated: payload.generated, markets: m.markets });
        await tx
          .insert(schema.predictions)
          .values(
            m.markets.map((x) => ({
              matchId: m.id, key: x.key, group: x.group, label: x.label, p: x.p, confidence: x.confidence,
              fairOdds: x.fair_odds, odds: x.odds ?? null, bookmaker: x.bookmaker ?? null, value: x.value ?? null,
            })),
          )
          .onConflictDoUpdate({
            target: [schema.predictions.matchId, schema.predictions.key],
            set: {
              group: sql`excluded."group"`, label: sql`excluded.label`, p: sql`excluded.p`, confidence: sql`excluded.confidence`,
              fairOdds: sql`excluded.fair_odds`, odds: sql`excluded.odds`, bookmaker: sql`excluded.bookmaker`,
              value: sql`excluded.value`, updatedAt: new Date(),
            },
          });
      }

      // Journal réel figé par le moteur, puis résultats officiels.
      for (const [matchId, t] of Object.entries(payload.track)) {
        const row = {
          matchId, league: t.league, date: t.date, home: t.home, away: t.away, frozen: t.frozen,
          key: t.pick?.key ?? null, label: t.pick?.label ?? null, p: t.pick?.p ?? null, status: t.pick?.status ?? null,
          scoreHome: t.result?.[0] ?? null, scoreAway: t.result?.[1] ?? null,
        };
        // Une prédiction figée n'est jamais réécrite : seuls le statut et le score sont complétés.
        await tx
          .insert(schema.trackedPicks)
          .values(row)
          .onConflictDoUpdate({ target: schema.trackedPicks.matchId, set: { status: row.status, scoreHome: row.scoreHome, scoreAway: row.scoreAway } });
        if (!t.result) continue;
        const [hg, ag] = t.result;
        const upd = await tx
          .update(schema.matches)
          .set({ scoreHome: hg, scoreAway: ag, updatedAt: new Date() })
          .where(and(eq(schema.matches.id, matchId), isNull(schema.matches.scoreHome)))
          .returning({ id: schema.matches.id });
        if (!upd.length) continue;
        settled++;
        const preds = await tx.select().from(schema.predictions).where(eq(schema.predictions.matchId, matchId));
        for (const p of preds)
          await tx
            .update(schema.predictions)
            .set({ status: settle(p.key, hg, ag) })
            .where(and(eq(schema.predictions.matchId, matchId), eq(schema.predictions.key, p.key)));
        const items = await tx.select().from(schema.couponItems).where(eq(schema.couponItems.matchId, matchId));
        for (const it of items)
          await tx
            .update(schema.couponItems)
            .set({ status: settle(it.key, hg, ag) })
            .where(and(eq(schema.couponItems.couponId, it.couponId), eq(schema.couponItems.matchId, matchId), eq(schema.couponItems.key, it.key)));
        const couponIds = [...new Set(items.map((i) => i.couponId))];
        if (couponIds.length) {
          const all = await tx.select().from(schema.couponItems).where(inArray(schema.couponItems.couponId, couponIds));
          for (const id of couponIds)
            await tx
              .update(schema.coupons)
              .set({ status: couponStatus(all.filter((i) => i.couponId === id).map((i) => i.status as Status)) })
              .where(eq(schema.coupons.id, id));
        }
      }
      return { source, generated: payload.generated, matches: payload.matches.length, changed, oddsMoves, settled };
    });
    await db.update(schema.syncRuns).set({ ...stats, finishedAt: new Date() }).where(eq(schema.syncRuns.id, run.id));
    return stats;
  } catch (e) {
    await db
      .update(schema.syncRuns)
      .set({ ok: false, error: String(e), finishedAt: new Date() })
      .where(eq(schema.syncRuns.id, run.id));
    throw e;
  }
}
