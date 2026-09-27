import type { User } from "@/lib/db/schema";

export const PLANS = {
  free: { name: "Gratuit", maxCoupon: 3, maxCombo: 3, valueBets: false, maxFavorites: 10 },
  pro: { name: "Pro", maxCoupon: 10, maxCombo: 20, valueBets: true, maxFavorites: 500 },
} as const;

export type PlanId = keyof typeof PLANS;
export const planOf = (u: Pick<User, "plan">) => PLANS[(u.plan as PlanId) in PLANS ? (u.plan as PlanId) : "free"];
export const stripeEnabled = () => Boolean(process.env.STRIPE_SECRET_KEY && process.env.STRIPE_PRICE_PRO);
