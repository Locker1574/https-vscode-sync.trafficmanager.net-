import type { Metadata } from "next";
import { CouponBuilder } from "@/components/coupon-builder";
import { Disclaimer, PageHeader } from "@/components/ui";
import { requireUser } from "@/lib/auth/session";
import { leagues } from "@/server/data";
import { planOf } from "@/server/plans";

export const metadata: Metadata = { title: "Coupon du jour" };

export default async function Coupons() {
  const user = await requireUser();
  return (
    <>
      <PageHeader title="Coupon du jour" subtitle="Générer choisit la meilleure option de chaque match au-dessus du seuil. Régénérer ne remplace une sélection que par un pourcentage plus élevé." />
      <CouponBuilder paused={Boolean(user.pausedUntil && user.pausedUntil > new Date())} leagues={await leagues()} maxSize={planOf(user).maxCoupon} />
      <div className="mt-8"><Disclaimer /></div>
    </>
  );
}
