import { LogOut } from "lucide-react";
import Link from "next/link";
import { LiveRefresh } from "@/components/live";
import { BottomNav, SideNav } from "@/components/nav";
import { requireUser } from "@/lib/auth/session";
import { logout } from "@/server/actions/auth";
import { planOf } from "@/server/plans";

export default async function AppLayout({ children }: LayoutProps<"/">) {
  const user = await requireUser();
  const paused = user.pausedUntil && user.pausedUntil > new Date();
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="sticky top-0 hidden h-screen flex-col gap-6 border-r border-line bg-panel p-4 lg:flex">
        <Link href="/tableau-de-bord" className="px-3 text-lg font-black tracking-tight">
          OMNI<span className="text-accent">SCORE</span>
        </Link>
        <SideNav />
        <div className="mt-auto space-y-2 px-3 text-xs text-muted">
          <div>
            {user.name} · <span className="font-semibold text-accent">{planOf(user).name}</span>
          </div>
          <form action={logout}>
            <button className="inline-flex items-center gap-1 hover:text-fg"><LogOut size={14} /> Déconnexion</button>
          </form>
        </div>
      </aside>
      <div className="min-w-0 pb-20 lg:pb-0">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-bg/85 px-4 py-3 backdrop-blur lg:px-8">
          <Link href="/tableau-de-bord" className="font-black tracking-tight lg:hidden">
            OMNI<span className="text-accent">SCORE</span>
          </Link>
          <LiveRefresh />
          <Link href="/compte" className="text-xs text-muted hover:text-fg">{planOf(user).name}</Link>
        </header>
        {paused && (
          <div className="border-b border-warn/40 bg-warn/10 px-4 py-2 text-center text-sm text-warn">
            Pause jeu responsable active jusqu&apos;au {user.pausedUntil!.toLocaleDateString("fr-FR")} : les générateurs sont désactivés.
          </div>
        )}
        <main className="mx-auto max-w-7xl px-4 py-6 lg:px-8">{children}</main>
      </div>
      <BottomNav />
    </div>
  );
}
