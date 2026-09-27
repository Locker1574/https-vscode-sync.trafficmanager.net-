import type Stripe from "stripe";
import { applySubscription, stripe } from "@/server/stripe";

export async function POST(request: Request) {
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!secret) return Response.json({ error: "Webhook non configuré" }, { status: 503 });
  let event: Stripe.Event;
  try {
    event = stripe().webhooks.constructEvent(await request.text(), request.headers.get("stripe-signature") ?? "", secret);
  } catch {
    return Response.json({ error: "Signature invalide" }, { status: 400 });
  }
  if (event.type.startsWith("customer.subscription.")) await applySubscription(event.data.object as Stripe.Subscription);
  return Response.json({ received: true });
}
