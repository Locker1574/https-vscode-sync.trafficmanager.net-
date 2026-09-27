import type { Metadata } from "next";
import { AuthForm } from "@/components/auth-form";
import { register } from "@/server/actions/auth";

export const metadata: Metadata = { title: "Inscription" };

export default function Page() {
  return <main className="px-4"><AuthForm mode="register" action={register} /></main>;
}
