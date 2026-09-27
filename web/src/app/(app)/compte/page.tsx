import type { Metadata } from "next";
import { Disclaimer, PageHeader } from "@/components/ui";
import { requireUser } from "@/lib/auth/session";
import { pauseAccount } from "@/server/actions/account";
import { PLANS, planOf, stripeEnabled } from "@/server/plans";

export const metadata: Metadata = { title: "Compte" };

export default async function Account({ searchParams }: PageProps<"/compte">) {
  const user = await requireUser();
  const { paiement } = await searchParams;
  const plan = planOf(user);
  const paused = user.pausedUntil && user.pausedUntil > new Date();
  return (
    <>
      <PageHeader title="Compte" subtitle={`${user.name} · ${user.email}`} />
      {paiement === "ok" && <div className="card mb-4 border-win p-4 text-sm text-win">Paiement reçu : votre offre sera activée dans quelques secondes.</div>}
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-5">
          <h2 className="font-semibold">Offre actuelle : <span className="text-accent">{plan.name}</span></h2>
          <ul className="mt-3 space-y-1 text-sm text-muted">
            <li>Coupons jusqu&apos;à {plan.maxCoupon} sélections</li>
            <li>Combo jusqu&apos;à {plan.maxCombo} matchs</li>
            <li>Value bets : {plan.valueBets ? "oui" : "aperçu"}</li>
          </ul>
          <div className="mt-4 flex flex-wrap gap-2">
            {!stripeEnabled() ? (
              <p className="text-sm text-muted">Le paiement n&apos;est pas encore configuré sur cette instance.</p>
            ) : user.plan === "pro" ? (
              <form action="/api/stripe/portal" method="post"><button className="btn-ghost">Gérer mon abonnement</button></form>
            ) : (
              <form action="/api/stripe/checkout" method="post"><button className="btn-primary">Passer à {PLANS.pro.name}</button></form>
            )}
          </div>
        </section>
        <section className="card p-5">
          <h2 className="font-semibold">Jeu responsable</h2>
          <p className="mt-2 text-sm text-muted">
            Faites une pause : les générateurs de coupons et le Combo seront désactivés pendant la durée choisie. Une pause ne peut pas être raccourcie.
          </p>
          {paused && <p className="mt-2 text-sm text-warn">Pause active jusqu&apos;au {user.pausedUntil!.toLocaleDateString("fr-FR")}.</p>}
          <form action={pauseAccount} className="mt-4 flex flex-wrap gap-2">
            <select name="days" className="input max-w-[200px]" defaultValue="7">
              <option value="1">24 heures</option>
              <option value="7">7 jours</option>
              <option value="30">30 jours</option>
              <option value="90">90 jours</option>
            </select>
            <button className="btn-ghost">Valider</button>
          </form>
          <div className="mt-4"><Disclaimer /></div>
        </section>
      </div>
    </>
  );
}
