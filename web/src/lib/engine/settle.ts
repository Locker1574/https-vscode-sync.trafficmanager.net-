import type { Status } from "./types";

const outcome = (h: number, a: number) => (h > a ? "1" : h === a ? "X" : "2");

/**
 * Règle un marché à partir du score final (même logique que backend/omniscore/markets.py).
 * Renvoie null si le marché ne peut pas être réglé (mi-temps inconnue).
 */
export function settle(key: string, hg: number, ag: number, hthg?: number | null, htag?: number | null): Status {
  const o = outcome(hg, ag);
  const total = hg + ag;
  if (key === "1" || key === "X" || key === "2") return o === key ? "V" : "P";
  if (key === "1X" || key === "X2" || key === "12") return key.includes(o) ? "V" : "P";
  if (key.startsWith("DNB")) return o === "X" ? "R" : o === key.at(-1) ? "V" : "P";
  if (key === "BTTS_Y") return hg > 0 && ag > 0 ? "V" : "P";
  if (key === "BTTS_N") return hg > 0 && ag > 0 ? "P" : "V";
  if (key.startsWith("CS")) {
    const [a, b] = key.slice(2).split("-").map(Number);
    return hg === a && ag === b ? "V" : "P";
  }
  if (key.startsWith("HT")) {
    if (hthg == null || htag == null) return null;
    const rest = key.slice(2);
    if (rest === "1" || rest === "X" || rest === "2") return outcome(hthg, htag) === rest ? "V" : "P";
    return hthg + htag > Number(rest.slice(1)) === (rest[0] === "O") ? "V" : "P";
  }
  if ((key[0] === "H" || key[0] === "A") && (key[1] === "O" || key[1] === "U")) {
    const g = key[0] === "H" ? hg : ag;
    return g > Number(key.slice(2)) === (key[1] === "O") ? "V" : "P";
  }
  if (key[0] === "O" || key[0] === "U") return total > Number(key.slice(1)) === (key[0] === "O") ? "V" : "P";
  throw new Error(`Marché inconnu : ${key}`);
}

/** Statut d'un coupon : perdu dès qu'une sélection est perdue, validé quand toutes sont réglées. */
export function couponStatus(items: Status[]): Status {
  if (items.includes("P")) return "P";
  if (items.some((s) => s === null)) return null;
  return items.every((s) => s === "R") ? "R" : "V";
}
