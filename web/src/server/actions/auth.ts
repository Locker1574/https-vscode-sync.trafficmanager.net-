"use server";
import bcrypt from "bcryptjs";
import { eq } from "drizzle-orm";
import { redirect } from "next/navigation";
import { z } from "zod";
import { db, schema } from "@/lib/db";
import { createSession, deleteSession, sessionConfigured } from "@/lib/auth/session";

export interface FormState {
  error?: string;
}

const safeNext = (v: FormDataEntryValue | null) => {
  const s = typeof v === "string" ? v : "";
  return s.startsWith("/") && !s.startsWith("//") ? s : "/tableau-de-bord";
};

const registerSchema = z.object({
  name: z.string().trim().min(2, "Nom trop court").max(60),
  email: z.email("E-mail invalide").transform((e) => e.toLowerCase()),
  password: z.string().min(10, "10 caractères minimum").max(200),
  adult: z.literal("on", { error: "Vous devez avoir 18 ans ou plus." }),
});

const MISSING_SECRET = "Configuration manquante : SESSION_SECRET (32 caractères minimum) doit être défini sur le serveur.";

export async function register(_: FormState, form: FormData): Promise<FormState> {
  if (!sessionConfigured()) return { error: MISSING_SECRET };
  const parsed = registerSchema.safeParse(Object.fromEntries(form));
  if (!parsed.success) return { error: parsed.error.issues[0].message };
  const { name, email, password } = parsed.data;
  const [exists] = await db.select({ id: schema.users.id }).from(schema.users).where(eq(schema.users.email, email));
  if (exists) return { error: "Un compte existe déjà avec cet e-mail." };
  const [user] = await db
    .insert(schema.users)
    .values({ name, email, passwordHash: await bcrypt.hash(password, 12) })
    .returning({ id: schema.users.id });
  await createSession(user.id);
  redirect(safeNext(form.get("suite")));
}

const loginSchema = z.object({ email: z.string().trim().toLowerCase(), password: z.string().min(1) });

export async function login(_: FormState, form: FormData): Promise<FormState> {
  if (!sessionConfigured()) return { error: MISSING_SECRET };
  const parsed = loginSchema.safeParse(Object.fromEntries(form));
  if (!parsed.success) return { error: "Identifiants invalides." };
  const [user] = await db.select().from(schema.users).where(eq(schema.users.email, parsed.data.email));
  // Comparaison même si l'utilisateur n'existe pas, pour ne pas révéler les e-mails inscrits par le temps de réponse.
  const ok = await bcrypt.compare(parsed.data.password, user?.passwordHash ?? "$2b$12$invalidinvalidinvalidinvalidinvalidinvalidinvalidinv");
  if (!user || !ok) return { error: "E-mail ou mot de passe incorrect." };
  await createSession(user.id);
  redirect(safeNext(form.get("suite")));
}

export async function logout() {
  await deleteSession();
  redirect("/");
}
