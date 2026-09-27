import { eq } from "drizzle-orm";
import { db, schema } from "@/lib/db";
import { getUser } from "@/lib/auth/session";
import { stripeEnabled } from "@/server/plans";
import { appUrl, stripe } from "@/server/stripe";

export async function POST() {
  const user = await getUser();
  if (!user) return Response.redirect(`${appUrl()}/connexion`, 303);
  if (!stripeEnabled()) return Response.json({ error: "Paiement non configuré" }, { status: 503 });
  const s = stripe();
  let customer = user.stripeCustomerId;
  if (!customer) {
    customer = (await s.customers.create({ email: user.email, name: user.name, metadata: { userId: user.id } })).id;
    await db.update(schema.users).set({ stripeCustomerId: customer }).where(eq(schema.users.id, user.id));
  }
  const session = await s.checkout.sessions.create({
    mode: "subscription",
    customer,
    line_items: [{ price: process.env.STRIPE_PRICE_PRO!, quantity: 1 }],
    allow_promotion_codes: true,
    success_url: `${appUrl()}/compte?paiement=ok`,
    cancel_url: `${appUrl()}/compte`,
  });
  return Response.redirect(session.url!, 303);
}
