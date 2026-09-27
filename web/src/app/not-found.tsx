import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-md px-4 py-24 text-center">
      <h1 className="text-2xl font-bold">Page introuvable</h1>
      <Link href="/tableau-de-bord" className="btn-primary mt-6">Retour au tableau de bord</Link>
    </main>
  );
}
