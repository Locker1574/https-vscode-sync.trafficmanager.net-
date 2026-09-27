"use client";
import Link from "next/link";
import { useActionState } from "react";
import type { FormState } from "@/server/actions/auth";

export function AuthForm({ mode, action, next }: { mode: "login" | "register"; action: (s: FormState, f: FormData) => Promise<FormState>; next?: string }) {
  const [state, formAction, pending] = useActionState(action, {});
  const register = mode === "register";
  return (
    <form action={formAction} className="card mx-auto mt-16 w-full max-w-sm space-y-4 p-6">
      <h1 className="text-xl font-bold">{register ? "Créer un compte" : "Connexion"}</h1>
      <input type="hidden" name="suite" value={next ?? ""} />
      {register && (
        <label className="block text-sm">
          Nom
          <input name="name" required autoComplete="name" className="input mt-1" />
        </label>
      )}
      <label className="block text-sm">
        E-mail
        <input name="email" type="email" required autoComplete="email" className="input mt-1" />
      </label>
      <label className="block text-sm">
        Mot de passe
        <input name="password" type="password" required minLength={register ? 10 : 1} autoComplete={register ? "new-password" : "current-password"} className="input mt-1" />
      </label>
      {register && (
        <label className="flex items-start gap-2 text-sm text-muted">
          <input type="checkbox" name="adult" required className="mt-1" />
          J&apos;ai 18 ans ou plus et je comprends qu&apos;aucune prédiction n&apos;est garantie.
        </label>
      )}
      {state.error && <p className="text-sm text-loss" role="alert">{state.error}</p>}
      <button className="btn-primary w-full" disabled={pending}>
        {pending ? "…" : register ? "Créer mon compte" : "Se connecter"}
      </button>
      <p className="text-center text-sm text-muted">
        {register ? (
          <>Déjà inscrit ? <Link className="text-accent" href="/connexion">Connexion</Link></>
        ) : (
          <>Pas encore de compte ? <Link className="text-accent" href="/inscription">Inscription</Link></>
        )}
      </p>
    </form>
  );
}
