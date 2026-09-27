"use server";
import { and, count, eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { z } from "zod";
import { db, schema } from "@/lib/db";
import { requireUser } from "@/lib/auth/session";
import { planOf } from "@/server/plans";

const input = z.object({ kind: z.enum(["match", "team", "league"]), ref: z.string().min(1).max(200) });

export async function toggleFavorite(kind: string, ref: string): Promise<{ on: boolean; error?: string }> {
  const user = await requireUser();
  const f = input.parse({ kind, ref });
  const where = and(eq(schema.favorites.userId, user.id), eq(schema.favorites.kind, f.kind), eq(schema.favorites.ref, f.ref));
  const removed = await db.delete(schema.favorites).where(where).returning();
  if (removed.length) {
    revalidatePath("/favoris");
    return { on: false };
  }
  const [{ n }] = await db.select({ n: count() }).from(schema.favorites).where(eq(schema.favorites.userId, user.id));
  if (n >= planOf(user).maxFavorites) return { on: false, error: "Limite de favoris atteinte pour votre offre." };
  await db.insert(schema.favorites).values({ userId: user.id, ...f }).onConflictDoNothing();
  revalidatePath("/favoris");
  return { on: true };
}
