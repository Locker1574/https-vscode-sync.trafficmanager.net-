import { describe, expect, it } from "vitest";
import { candidates, generate, regenerate, summarize, topOptions } from "../coupon";
import { couponStatus, settle } from "../settle";
import type { Market, MatchInfo } from "../types";

const info = (id: string): MatchInfo => ({ id, league: "fr.1", date: "2026-10-01", time: "20:00", home: `H${id}`, away: `A${id}` });
const mk = (matchId: string, key: string, p: number, confidence = p * 100, odds: number | null = null): Market => ({
  matchId, key, group: "Buts", label: key, p, confidence, fairOdds: Math.round((1 / p) * 100) / 100, odds, value: null,
});

const matches = ["a", "b", "c", "d"].map(info);
const markets = new Map<string, Market[]>([
  ["a", [mk("a", "O0.5", 0.93), mk("a", "1", 0.75), mk("a", "CS1-0", 0.99)]],
  ["b", [mk("b", "O1.5", 0.8), mk("b", "X", 0.3)]],
  ["c", [mk("c", "U3.5", 0.72)]],
  ["d", [mk("d", "1X", 0.6)]],
]);

describe("settle", () => {
  it("règle les marchés principaux", () => {
    expect(settle("1", 2, 1)).toBe("V");
    expect(settle("X2", 2, 1)).toBe("P");
    expect(settle("DNB1", 1, 1)).toBe("R");
    expect(settle("O2.5", 2, 1)).toBe("V");
    expect(settle("U2.5", 2, 1)).toBe("P");
    expect(settle("BTTS_Y", 2, 0)).toBe("P");
    expect(settle("HO1.5", 2, 0)).toBe("V");
    expect(settle("AU0.5", 2, 0)).toBe("V");
    expect(settle("CS2-1", 2, 1)).toBe("V");
    expect(settle("HT1", 2, 1)).toBeNull();
    expect(settle("HTO0.5", 2, 1, 1, 0)).toBe("V");
  });
  it("calcule le statut d'un coupon", () => {
    expect(couponStatus(["V", "V"])).toBe("V");
    expect(couponStatus(["V", null])).toBeNull();
    expect(couponStatus(["V", "P", null])).toBe("P");
    expect(couponStatus(["R", "V"])).toBe("V");
  });
});

describe("coupons", () => {
  it("exclut les scores exacts et les probabilités hors seuil", () => {
    const c = candidates(matches, markets, { pmin: 0.7 });
    expect(c.map((s) => s.key)).toEqual(["O0.5", "O1.5", "U3.5"]);
  });
  it("génère un coupon avec probabilité combinée et cote totale", () => {
    const r = generate(matches, markets, 2, { pmin: 0.7 });
    expect(r.size).toBe(2);
    expect(r.combinedProbability).toBeCloseTo(0.93 * 0.8);
    expect(r.totalOdds).toBeCloseTo(1.08 * 1.25, 2);
  });
  it("régénérer garde le coupon quand les nouvelles sélections sont plus faibles", () => {
    const first = generate(matches, markets, 2, { pmin: 0.7 });
    const r = regenerate(matches, markets, first.selections, 2, { pmin: 0.7 });
    expect(r.replaced).toBe(0);
    expect(r.selections.map((s) => s.key)).toEqual(["O0.5", "O1.5"]);
    expect(r.alternative.selections.map((s) => s.key)).toEqual(["U3.5"]);
  });
  it("régénérer remplace par un pourcentage plus élevé, sauf les sélections verrouillées", () => {
    const current = summarize([
      { ...mk("c", "U3.5", 0.72), match: "c", date: "", time: null },
      { ...mk("d", "1X", 0.6), match: "d", date: "", time: null, locked: true },
    ]).selections;
    const r = regenerate(matches, markets, current, 2, { pmin: 0.7 });
    expect(r.replaced).toBe(1);
    expect(r.selections.find((s) => s.matchId === "d")?.locked).toBe(true);
    expect(r.selections.find((s) => s.isNew)?.p).toBeGreaterThan(0.72);
  });
  it("régénérer ne remplace pas une sélection fiable par un pourcentage élevé peu confiant", () => {
    const pool = new Map<string, Market[]>([["a", [mk("a", "O1.5", 0.8, 85)]], ["b", [mk("b", "O0.5", 0.97, 40)]]]);
    const first = generate([info("a")], pool, 1, { pmin: 0.7 });
    const r = regenerate([info("a"), info("b")], pool, first.selections, 1, { pmin: 0.7 });
    expect(r.replaced).toBe(0);
    expect(r.selections[0].matchId).toBe("a");
  });
  it("topOptions renvoie les N meilleures options d'un match", () => {
    expect(topOptions(info("a"), markets.get("a")!, 2).map((s) => s.key)).toEqual(["O0.5", "1"]);
  });
});
