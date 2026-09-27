"use server";
import { revalidatePath } from "next/cache";
import { z } from "zod";
import { db, schema } from "@/lib/db";
import { requireUser } from "@/lib/auth/session";
import { generate, regenerate, summarize, topOptions } from "@/lib/engine/coupon";
import type { CouponResult, RegenerateResult, Selection } from "@/lib/engine/types";
import { addDays, matchPool, nextMatchDate } from "@/server/data";
import { planOf } from "@/server/plans";

const params = z.object({
  size: z.number().int().min(1).max(20),
  pmin: z.number().min(0.01).max(1),
  mode: z.enum(["surete", "equilibre", "rendement"]),
  period: z.enum(["jour", "avenir"]),
  league: z.string().optional(),
  groups: z.array(z.string()).optional(),
});
export type CouponParams = z.infer<typeof params>;

const selection = z.object({
  matchId: z.string(), key: z.string(), group: z.string(), label: z.string(), p: z.number(), confidence: z.number(),
  fairOdds: z.number(), odds: z.number().nullable(), value: z.number().nullable(), match: z.string(), date: z.string(),
  time: z.string().nullable(), locked: z.boolean().optional(), isNew: z.boolean().optional(), status: z.enum(["V", "P", "R"]).nullable().optional(),
});

async function pool(p: CouponParams) {
  const from = await nextMatchDate();
  // « Jour » : la prochaine journée avec des matchs ; « À venir » : les 14 jours suivants.
  return matchPool(from, p.period === "jour" ? from : addDays(from, 14), p.league || undefined);
}

async function activeUser() {
  const user = await requireUser();
  if (user.pausedUntil && user.pausedUntil > new Date())
    throw new Error(`Pause jeu responsable active jusqu'au ${user.pausedUntil.toLocaleDateString("fr-FR")}.`);
  return user;
}

function clamp(p: CouponParams, max: number) {
  return { ...p, size: Math.min(p.size, max) };
}

export async function generateCoupon(raw: CouponParams): Promise<CouponResult & { limited: boolean }> {
  const user = await activeUser();
  const p = clamp(params.parse(raw), planOf(user).maxCoupon);
  const { infos, markets } = await pool(p);
  const res = generate(infos, markets, p.size, { pmin: p.pmin, mode: p.mode, groups: p.groups });
  await db.insert(schema.generations).values({ userId: user.id, action: "generate", params: p, result: res });
  return { ...res, limited: p.size < raw.size };
}

export async function regenerateCoupon(raw: CouponParams, current: Selection[]): Promise<RegenerateResult & { limited: boolean }> {
  const user = await activeUser();
  const p = clamp(params.parse(raw), planOf(user).maxCoupon);
  const cur = z.array(selection).max(20).parse(current);
  const { infos, markets } = await pool(p);
  const res = regenerate(infos, markets, cur, p.size, { pmin: p.pmin, mode: p.mode, groups: p.groups });
  await db.insert(schema.generations).values({ userId: user.id, action: "regenerate", params: p, result: res });
  return { ...res, limited: p.size < raw.size };
}

/** Combo : les N meilleures options par match (sélecteur 1-10) pour M matchs (réglette 1-20). */
export async function buildCombo(raw: CouponParams & { perMatch: number }) {
  const user = await activeUser();
  const perMatch = z.number().int().min(1).max(10).parse(raw.perMatch);
  const p = clamp(params.parse(raw), planOf(user).maxCombo);
  const { infos, markets } = await pool(p);
  const opts = { pmin: p.pmin, pmax: 0.99, mode: p.mode, groups: p.groups };
  const rows = infos
    .map((info) => topOptions(info, markets.get(info.id) ?? [], perMatch, opts))
    .filter((o) => o.length)
    .sort((a, b) => b[0].p * b[0].confidence - a[0].p * a[0].confidence)
    .slice(0, p.size);
  return { rows, limited: p.size < raw.size };
}

export async function saveCoupon(kind: "jour" | "combo", mode: string, pmin: number, selections: Selection[]) {
  const user = await requireUser();
  const sel = z.array(selection).min(1).max(20).parse(selections);
  const s = summarize(sel);
  await db.transaction(async (tx) => {
    const [c] = await tx
      .insert(schema.coupons)
      .values({ userId: user.id, kind, mode, pmin, combinedProbability: s.combinedProbability, totalOdds: s.totalOdds })
      .returning({ id: schema.coupons.id });
    await tx.insert(schema.couponItems).values(
      sel.map((x) => ({ couponId: c.id, matchId: x.matchId, key: x.key, match: x.match, label: x.label, p: x.p, confidence: x.confidence, odds: x.odds ?? x.fairOdds })),
    ).onConflictDoNothing();
  });
  revalidatePath("/mes-coupons");
  return { ok: true };
}
