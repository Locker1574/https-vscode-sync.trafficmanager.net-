import { getUser } from "@/lib/auth/session";
import { appUrl, stripe } from "@/server/stripe";

export async function POST() {
  const user = await getUser();
  if (!user?.stripeCustomerId) return Response.redirect(`${appUrl()}/compte`, 303);
  const session = await stripe().billingPortal.sessions.create({ customer: user.stripeCustomerId, return_url: `${appUrl()}/compte` });
  return Response.redirect(session.url, 303);
}
