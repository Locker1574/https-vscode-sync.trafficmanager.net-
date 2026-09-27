"use server";
import { eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { db, schema } from "@/lib/db";
import { requireUser } from "@/lib/auth/session";

/**
 * Jeu responsable : pause volontaire (les générateurs sont désactivés pendant la pause).
 * Une pause peut être prolongée mais jamais raccourcie.
 */
export async function pauseAccount(form: FormData) {
  const user = await requireUser();
  const days = Math.min(Math.max(Number(form.get("days")) || 1, 1), 365);
  const until = new Date(Date.now() + days * 86_400_000);
  if (user.pausedUntil && user.pausedUntil > until) return;
  await db.update(schema.users).set({ pausedUntil: until }).where(eq(schema.users.id, user.id));
  revalidatePath("/", "layout");
}
