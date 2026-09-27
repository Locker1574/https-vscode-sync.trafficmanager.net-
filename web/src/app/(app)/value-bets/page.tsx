import type { Metadata } from "next";
import Link from "next/link";
import { ConfidenceBar, Disclaimer, Empty, PageHeader, Prob } from "@/components/ui";
import { requireUser } from "@/lib/auth/session";
import { odds, shortDate } from "@/lib/format";
import { valueBets } from "@/server/data";
import { planOf } from "@/server/plans";

export const metadata: Metadata = { title: "Value bets" };

/** Kelly fractionné (¼), plafonné à 5 % de la bankroll. */
const kelly = (p: number, o: number) => Math.min(Math.max(((p * o - 1) / (o - 1)) * 0.25, 0), 0.05);

export default async function ValueBets() {
  const user = await requireUser();
  const plan = planOf(user);
  const rows = await valueBets();
  return (
    <>
      <PageHeader title="Value bets" subtitle="Options où la probabilité du modèle dépasse la probabilité implicite de la meilleure cote du marché (EV = p × cote − 1 ≥ 3 %)." />
      {!rows.length ? (
        <Empty>
          Aucune value bet : les cotes réelles ne sont pas chargées. Définissez <code>ODDS_API_KEY</code> côté moteur (The Odds API) puis relancez la synchronisation.
        </Empty>
      ) : !plan.valueBets ? (
        <Empty>
          {rows.length} value bets disponibles. <Link className="text-accent" href="/compte">Passez à l&apos;offre Pro</Link> pour les voir avec les mises Kelly.
        </Empty>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[760px] text-sm">
            <thead className="text-left text-xs text-muted">
              <tr>{["Match", "Option", "Probabilité", "Confiance", "Cote juste", "Meilleure cote", "Value", "Mise ¼ Kelly"].map((h) => <th key={h} className="px-3 py-2 font-medium">{h}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map(({ p, m }) => (
                <tr key={`${p.matchId}-${p.key}`} className="border-t border-line/60">
                  <td className="px-3 py-2">
                    <Link href={`/match/${encodeURIComponent(m.id)}`} className="font-semibold hover:text-accent">{m.home} – {m.away}</Link>
                    <div className="text-xs capitalize text-muted">{shortDate(m.date)} {m.time}</div>
                  </td>
                  <td className="px-3 py-2">{p.label}</td>
                  <td className="px-3 py-2"><Prob p={p.p} /></td>
                  <td className="w-36 px-3 py-2"><ConfidenceBar value={p.confidence} /></td>
                  <td className="num px-3 py-2">{odds(p.fairOdds)}</td>
                  <td className="num px-3 py-2">{odds(p.odds)} <span className="text-xs text-muted">{p.bookmaker}</span></td>
                  <td className="num px-3 py-2 font-semibold text-win">+{((p.value ?? 0) * 100).toFixed(1)} %</td>
                  <td className="num px-3 py-2">{p.odds ? `${(kelly(p.p, p.odds) * 100).toFixed(1)} %` : "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="mt-6"><Disclaimer /></div>
    </>
  );
}
