import "server-only";
import { cache } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { eq } from "drizzle-orm";
import { jwtVerify, SignJWT } from "jose";
import { db, schema } from "@/lib/db";

const COOKIE = "omniscore_session";
const MAX_AGE = 60 * 60 * 24 * 30; // 30 jours

function key() {
  const secret = process.env.SESSION_SECRET;
  if (!secret || secret.length < 32) throw new Error("SESSION_SECRET doit contenir au moins 32 caractères.");
  return new TextEncoder().encode(secret);
}

export async function createSession(userId: string) {
  const token = await new SignJWT({ sub: userId })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${MAX_AGE}s`)
    .sign(key());
  (await cookies()).set(COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: MAX_AGE,
  });
}

export async function deleteSession() {
  (await cookies()).delete(COOKIE);
}

export const sessionConfigured = () => (process.env.SESSION_SECRET?.length ?? 0) >= 32;

export async function readSession(token: string | undefined): Promise<string | null> {
  if (!token || !sessionConfigured()) return null;
  try {
    const { payload } = await jwtVerify(token, key(), { algorithms: ["HS256"] });
    return typeof payload.sub === "string" ? payload.sub : null;
  } catch {
    return null;
  }
}

/** Utilisateur connecté (une seule requête par rendu). */
export const getUser = cache(async () => {
  const id = await readSession((await cookies()).get(COOKIE)?.value);
  if (!id) return null;
  const [user] = await db.select().from(schema.users).where(eq(schema.users.id, id));
  return user ?? null;
});

export async function requireUser() {
  const user = await getUser();
  if (!user) redirect("/connexion");
  return user;
}

export const SESSION_COOKIE = COOKIE;
