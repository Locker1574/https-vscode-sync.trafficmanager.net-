import { BarChart3, Layers, ShieldCheck, Sparkles, TrendingUp, Zap } from "lucide-react";
import Link from "next/link";
import { Disclaimer } from "@/components/ui";
import { getUser } from "@/lib/auth/session";
import { backtest } from "@/server/data";
import { PLANS } from "@/server/plans";

export default async function Home() {
  const [user, bt] = await Promise.all([getUser(), backtest()]);
  const a = bt?.all_seasons;
  const features = [
    { icon: Sparkles, t: "Coupon du jour", d: "Coupons de 1 à 10 sélections, Générer / Régénérer : on ne remplace une sélection que par un pourcentage plus élevé." },
    { icon: Layers, t: "Combo", d: "Réglette de 1 à 20 matchs, 1 à 10 options par match, seuil de confiance de 1 à 100 %, modes Sûreté et Rendement." },
    { icon: TrendingUp, t: "Value bets", d: "Probabilité du modèle contre cote du marché : EV = p × cote − 1, mise Kelly fractionnée." },
    { icon: BarChart3, t: "Précision publique", d: "Backtest walk-forward, calibration et journal réel figé avant chaque match : Validé ou Perdu." },
    { icon: Zap, t: "Temps réel", d: "Les prédictions, cotes et résultats se mettent à jour automatiquement, tout est historisé." },
    { icon: ShieldCheck, t: "Jeu responsable", d: "18 ans et plus, pause volontaire, aucune promesse de gain." },
  ];
  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <header className="flex items-center justify-between">
        <span className="text-lg font-black tracking-tight">
          OMNI<span className="text-accent">SCORE</span>
        </span>
        <div className="flex gap-2">
          {user ? (
            <Link href="/tableau-de-bord" className="btn-primary">Ouvrir l&apos;application</Link>
          ) : (
            <>
              <Link href="/connexion" className="btn-ghost">Connexion</Link>
              <Link href="/inscription" className="btn-primary">Créer un compte</Link>
            </>
          )}
        </div>
      </header>

      <section className="py-16 text-center">
        <p className="text-sm font-semibold uppercase tracking-widest text-accent">Les données voient le match avant vous</p>
        <h1 className="mx-auto mt-4 max-w-3xl text-4xl font-black leading-tight tracking-tight sm:text-5xl">
          Des prédictions football calibrées, mesurées et transparentes.
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-muted">
          Modèle Dixon-Coles + Elo sur les résultats officiels de 8 championnats, calibration isotonique, 40 marchés par match,
          indice de confiance et coupons générés automatiquement.
        </p>
        {a && (
          <div className="mx-auto mt-10 grid max-w-3xl grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              [a.n.toLocaleString("fr-FR"), "matchs backtestés"],
              [`${(a.blend.accuracy * 100).toFixed(1)} %`, "précision 1X2"],
              [a.blend.rps.toFixed(3), "RPS (plus bas = mieux)"],
              [`${(a.top_picks.hit_rate * 100).toFixed(0)} %`, `réussite des sélections (annoncé ${(a.top_picks.mean_p * 100).toFixed(0)} %)`],
            ].map(([v, l]) => (
              <div key={l} className="card p-4">
                <div className="num text-2xl font-bold">{v}</div>
                <div className="text-xs text-muted">{l}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(({ icon: Icon, t, d }) => (
          <div key={t} className="card p-5">
            <Icon className="text-accent" size={22} />
            <h3 className="mt-3 font-semibold">{t}</h3>
            <p className="mt-1 text-sm text-muted">{d}</p>
          </div>
        ))}
      </section>

      <section className="mt-16 grid gap-4 sm:grid-cols-2">
        {Object.entries(PLANS).map(([id, p]) => (
          <div key={id} className={`card p-6 ${id === "pro" ? "border-accent" : ""}`}>
            <h3 className="text-lg font-bold">{p.name}</h3>
            <ul className="mt-3 space-y-1 text-sm text-muted">
              <li>Calendrier, fiches match et 40 marchés</li>
              <li>Coupons jusqu&apos;à {p.maxCoupon} sélections</li>
              <li>Combo jusqu&apos;à {p.maxCombo} matchs</li>
              <li>{p.valueBets ? "Value bets et mises Kelly" : "Value bets : aperçu"}</li>
              <li>{p.maxFavorites} favoris</li>
            </ul>
          </div>
        ))}
      </section>

      <footer className="mt-16 border-t border-line pt-6">
        <Disclaimer />
      </footer>
    </main>
  );
}
