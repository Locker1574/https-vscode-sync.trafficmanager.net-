import "server-only";
import Stripe from "stripe";
import { eq } from "drizzle-orm";
import { db, schema } from "@/lib/db";

export const stripe = () => new Stripe(process.env.STRIPE_SECRET_KEY!);
export const appUrl = () => (process.env.APP_URL ?? "http://localhost:3000").replace(/\/$/, "");

/** Met à jour l'abonnement et l'offre de l'utilisateur à partir de Stripe (source de vérité). */
export async function applySubscription(sub: Stripe.Subscription) {
  const customer = typeof sub.customer === "string" ? sub.customer : sub.customer.id;
  const [user] = await db.select().from(schema.users).where(eq(schema.users.stripeCustomerId, customer));
  if (!user) return;
  const item = sub.items.data[0];
  const periodEnd = item?.current_period_end ? new Date(item.current_period_end * 1000) : null;
  await db
    .insert(schema.subscriptions)
    .values({ id: sub.id, userId: user.id, status: sub.status, priceId: item?.price.id ?? null, currentPeriodEnd: periodEnd })
    .onConflictDoUpdate({
      target: schema.subscriptions.id,
      set: { status: sub.status, priceId: item?.price.id ?? null, currentPeriodEnd: periodEnd, updatedAt: new Date() },
    });
  const active = ["active", "trialing", "past_due"].includes(sub.status);
  await db.update(schema.users).set({ plan: active ? "pro" : "free" }).where(eq(schema.users.id, user.id));
}
