export const pct = (p: number, digits = 0) => `${(p * 100).toFixed(digits)} %`;
export const odds = (o: number | null | undefined) => (o ? o.toFixed(2) : "–");

export function dateLabel(d: string) {
  return new Date(`${d}T12:00:00Z`).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
}
export const shortDate = (d: string) =>
  new Date(`${d}T12:00:00Z`).toLocaleDateString("fr-FR", { weekday: "short", day: "numeric", month: "short" });

/** Couleur de l'indice de confiance (1-100). */
export function confidenceTone(c: number) {
  if (c >= 80) return "var(--win)";
  if (c >= 65) return "var(--info)";
  if (c >= 50) return "var(--warn)";
  return "var(--loss)";
}

export const STATUS_LABEL: Record<string, string> = { V: "Validé", P: "Perdu", R: "Remboursé" };
export const MODE_LABEL: Record<string, string> = { surete: "Sûreté", equilibre: "Équilibré", rendement: "Rendement" };
