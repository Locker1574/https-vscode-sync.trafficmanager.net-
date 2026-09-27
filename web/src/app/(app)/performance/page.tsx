import type { Metadata } from "next";
import Link from "next/link";
import { Empty, PageHeader, Stat, StatusBadge } from "@/components/ui";
import { requireUser } from "@/lib/auth/session";
import { pct, shortDate } from "@/lib/format";
import { backtest, trackRecord } from "@/server/data";

export const metadata: Metadata = { title: "Performance" };

const MODELS = [["base", "Fréquences de la ligue"], ["elo", "Elo"], ["dc", "Dixon-Coles"], ["blend", "Mélange (production)"]] as const;

export default async function Performance() {
  await requireUser();
  const [bt, track] = await Promise.all([backtest(), trackRecord()]);
  const a = bt?.all_seasons;
  return (
    <>
      <PageHeader title="Performance" subtitle="Précision mesurée publiquement : backtest walk-forward (le modèle ne voit jamais le futur) et journal réel figé avant chaque match." />

      <h2 className="mb-3 text-lg font-semibold">Journal réel</h2>
      <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Prédictions figées" value={track.frozen} />
        <Stat label="Réglées" value={track.settled} />
        <Stat label="Validées" value={track.settled ? pct(track.won / track.settled) : "–"} hint={track.settled ? `${track.won}/${track.settled}` : "en attente des premiers résultats"} />
        <Stat label="Probabilité annoncée" value={track.meanP != null ? pct(track.meanP) : "–"} hint="à comparer au taux validé" />
      </div>
      {track.recent.length ? (
        <div className="card mb-8 divide-y divide-line/60">
          {track.recent.map((r) => (
            <div key={r.matchId} className="flex flex-wrap items-center justify-between gap-2 px-4 py-2 text-sm">
              <Link href={`/match/${encodeURIComponent(r.matchId)}`} className="hover:text-accent">
                <span className="capitalize text-muted">{shortDate(r.date)}</span> · {r.home} {r.scoreHome}–{r.scoreAway} {r.away}
              </Link>
              <span className="flex items-center gap-2">{r.label} · {pct(r.p ?? 0)} <StatusBadge status={r.status} /></span>
            </div>
          ))}
        </div>
      ) : (
        <div className="mb-8"><Empty>Les premières prédictions figées seront réglées après leurs matchs.</Empty></div>
      )}

      {!a ? (
        <Empty>Backtest indisponible : lancez <code>python -m omniscore.cli backtest</code> dans backend/.</Empty>
      ) : (
        <>
          <h2 className="mb-3 text-lg font-semibold">Backtest · {a.n.toLocaleString("fr-FR")} matchs réels</h2>
          <div className="card mb-8 overflow-x-auto">
            <table className="w-full min-w-[520px] text-sm">
              <thead className="text-left text-xs text-muted">
                <tr>{["Modèle", "RPS ↓", "Log-loss ↓", "Brier ↓", "Précision 1X2 ↑"].map((h) => <th key={h} className="px-4 py-2 font-medium">{h}</th>)}</tr>
              </thead>
              <tbody className="num">
                {MODELS.map(([k, l]) => (
                  <tr key={k} className={`border-t border-line/60 ${k === "blend" ? "font-semibold text-accent" : ""}`}>
                    <td className="px-4 py-2">{l}</td>
                    <td className="px-4 py-2">{a[k].rps.toFixed(4)}</td>
                    <td className="px-4 py-2">{a[k].log_loss.toFixed(4)}</td>
                    <td className="px-4 py-2">{a[k].brier.toFixed(4)}</td>
                    <td className="px-4 py-2">{pct(a[k].accuracy, 1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h2 className="mb-1 text-lg font-semibold">Calibration (tous marchés)</h2>
          <p className="mb-3 text-sm text-muted">Un modèle bien calibré a une réussite observée égale au pourcentage annoncé.</p>
          <div className="card mb-8 space-y-3 p-4">
            {a.calibration_all_markets.filter((c) => c.n > 0 && c.annonce != null).map((c) => (
              <div key={c.tranche} className="grid grid-cols-[80px_1fr_150px] items-center gap-3 text-sm">
                <span className="text-muted">{c.tranche}</span>
                <div className="relative h-3 rounded-full bg-panel-2">
                  <div className="absolute inset-y-0 left-0 rounded-full bg-accent/80" style={{ width: `${(c.observe ?? 0) * 100}%` }} />
                  <div className="absolute inset-y-[-3px] w-0.5 bg-fg" style={{ left: `${(c.annonce ?? 0) * 100}%` }} title="annoncé" />
                </div>
                <span className="num text-right text-xs">annoncé {pct(c.annonce ?? 0)} · observé <strong>{pct(c.observe ?? 0)}</strong></span>
              </div>
            ))}
            <p className="text-xs text-muted">Barre : réussite observée. Trait : probabilité annoncée. {a.calibration_all_markets.reduce((s, c) => s + c.n, 0).toLocaleString("fr-FR")} prédictions.</p>
          </div>

          <h2 className="mb-3 text-lg font-semibold">Coupons backtestés</h2>
          <div className="grid gap-3 sm:grid-cols-3">
            {Object.entries(a.coupons).map(([k, c]) => (
              <Stat key={k} label={`Coupon de ${k}`} value={pct(c.observed_win_rate)} hint={`annoncé ${pct(c.predicted_win_rate)} · ${c.coupons} coupons`} />
            ))}
          </div>
        </>
      )}
    </>
  );
}
