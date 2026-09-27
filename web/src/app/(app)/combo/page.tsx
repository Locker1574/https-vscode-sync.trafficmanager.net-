import type { Metadata } from "next";
import { ComboBuilder } from "@/components/combo-builder";
import { Disclaimer, PageHeader } from "@/components/ui";
import { requireUser } from "@/lib/auth/session";
import { leagues } from "@/server/data";
import { planOf } from "@/server/plans";

export const metadata: Metadata = { title: "Combo" };

export default async function Combo() {
  const user = await requireUser();
  return (
    <>
      <PageHeader title="Combo" subtitle="Choisissez le nombre de matchs (1 à 20) et d'options proposées par match (1 à 10). Sûreté privilégie la probabilité, Rendement la cote." />
      <ComboBuilder paused={Boolean(user.pausedUntil && user.pausedUntil > new Date())} leagues={await leagues()} maxMatches={planOf(user).maxCombo} />
      <div className="mt-8"><Disclaimer /></div>
    </>
  );
}
