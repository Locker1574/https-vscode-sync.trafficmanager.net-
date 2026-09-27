import type { Metadata } from "next";
import { AuthForm } from "@/components/auth-form";
import { login } from "@/server/actions/auth";

export const metadata: Metadata = { title: "Connexion" };

export default async function Page({ searchParams }: PageProps<"/connexion">) {
  const { suite } = await searchParams;
  return <main className="px-4"><AuthForm mode="login" action={login} next={typeof suite === "string" ? suite : undefined} /></main>;
}
