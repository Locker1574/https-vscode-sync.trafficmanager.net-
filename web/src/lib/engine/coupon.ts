import type { CouponResult, Market, MatchInfo, Mode, RegenerateResult, Selection } from "./types";

export interface CandidateOptions {
  pmin?: number;
  pmax?: number;
  mode?: Mode;
  exclude?: Set<string>;
  /** Marchés autorisés (clés ou groupes) ; vide = tous. */
  groups?: string[];
}

export const oddsOf = (m: Market) => m.odds ?? m.fairOdds;

/** Même pondération que backend/omniscore/coupon.py. */
export function score(m: Market, mode: Mode): number {
  const odds = oddsOf(m);
  if (mode === "rendement") return odds * m.confidence;
  if (mode === "equilibre") return Math.sqrt(m.p) * m.p * odds * m.confidence;
  return m.p * m.confidence;
}

export const eligible = (m: Market, pmin: number, pmax: number, groups?: string[]) =>
  m.p >= pmin && m.p <= pmax && !m.key.startsWith("CS") && (!groups?.length || groups.includes(m.group));

const toSelection = (m: Market, info: MatchInfo): Selection => ({
  ...m,
  match: `${info.home} – ${info.away}`,
  date: info.date,
  time: info.time,
});

/** Meilleure option de chaque match, triée du meilleur score au moins bon. */
export function candidates(
  matches: MatchInfo[],
  markets: Map<string, Market[]>,
  { pmin = 0.7, pmax = 0.98, mode = "surete", exclude, groups }: CandidateOptions = {},
): Selection[] {
  const out: Selection[] = [];
  for (const info of matches) {
    if (exclude?.has(info.id)) continue;
    const ok = (markets.get(info.id) ?? []).filter((m) => eligible(m, pmin, pmax, groups));
    if (!ok.length) continue;
    const best = ok.reduce((a, b) => (score(b, mode) > score(a, mode) ? b : a));
    out.push(toSelection(best, info));
  }
  return out.sort((a, b) => score(b, mode) - score(a, mode));
}

/** Les N meilleures options d'un match (pour le sélecteur du Combo). */
export function topOptions(info: MatchInfo, markets: Market[], n: number, opts: CandidateOptions = {}): Selection[] {
  const { pmin = 0.5, pmax = 0.99, mode = "surete", groups } = opts;
  return markets
    .filter((m) => eligible(m, pmin, pmax, groups))
    .sort((a, b) => score(b, mode) - score(a, mode))
    .slice(0, n)
    .map((m) => toSelection(m, info));
}

export function summarize(selections: Selection[]): CouponResult {
  const combinedProbability = selections.length ? selections.reduce((acc, s) => acc * s.p, 1) : 0;
  const totalOdds = selections.length ? selections.reduce((acc, s) => acc * oddsOf(s), 1) : 0;
  return { selections, combinedProbability, totalOdds: Math.round(totalOdds * 100) / 100, size: selections.length };
}

export function generate(matches: MatchInfo[], markets: Map<string, Market[]>, size: number, opts: CandidateOptions = {}) {
  return summarize(candidates(matches, markets, opts).slice(0, size));
}

/**
 * Régénérer : une sélection n'est remplacée que par une nouvelle au pourcentage plus élevé
 * et au score au moins aussi bon (en Sûreté : probabilité × confiance), pour ne jamais
 * échanger une sélection fiable contre un pourcentage élevé mais peu confiant.
 * Si aucune nouvelle n'est meilleure, le coupon à haut pourcentage est conservé et les
 * nouvelles sélections sont proposées à côté (alternative).
 */
export function regenerate(
  matches: MatchInfo[],
  markets: Map<string, Market[]>,
  current: Selection[],
  size: number,
  opts: CandidateOptions = {},
): RegenerateResult {
  const mode = opts.mode ?? "surete";
  const fresh = candidates(matches, markets, { ...opts, exclude: new Set(current.map((c) => c.matchId)) });
  const alternative = summarize(fresh.slice(0, size));
  const locked = current.filter((c) => c.locked);
  const free = current.filter((c) => !c.locked).sort((a, b) => b.p - a.p);
  const final: Selection[] = locked.map((c) => ({ ...c, isNew: false }));
  let replaced = 0;
  for (const old of free) {
    const k = fresh.findIndex((n) => n.p > old.p && score(n, mode) >= score(old, mode));
    if (k === -1) final.push({ ...old, isNew: false });
    else {
      final.push({ ...fresh.splice(k, 1)[0], isNew: true });
      replaced++;
    }
  }
  while (final.length < size && fresh.length) {
    final.push({ ...fresh.shift()!, isNew: true });
    replaced++;
  }
  const res = summarize(final.slice(0, size));
  return {
    ...res,
    replaced,
    message: replaced
      ? `${replaced} sélection(s) remplacée(s) par un pourcentage plus élevé.`
      : "Coupon déjà optimal : aucune nouvelle sélection n'a un pourcentage plus élevé avec une confiance au moins égale. Les nouveaux matchs sont proposés en alternative.",
    alternative,
  };
}
