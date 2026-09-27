"use client";
import { BarChart3, CalendarDays, Gauge, Heart, Layers, Search, Sparkles, Ticket, TrendingUp, UserRound } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export const NAV = [
  { href: "/tableau-de-bord", label: "Tableau de bord", icon: Gauge },
  { href: "/calendrier", label: "Calendrier", icon: CalendarDays },
  { href: "/coupons", label: "Coupon du jour", icon: Sparkles },
  { href: "/combo", label: "Combo", icon: Layers },
  { href: "/value-bets", label: "Value bets", icon: TrendingUp },
  { href: "/mes-coupons", label: "Mes coupons", icon: Ticket },
  { href: "/favoris", label: "Favoris", icon: Heart },
  { href: "/recherche", label: "Recherche", icon: Search },
  { href: "/performance", label: "Performance", icon: BarChart3 },
  { href: "/compte", label: "Compte", icon: UserRound },
];

const MOBILE = ["/tableau-de-bord", "/calendrier", "/coupons", "/combo", "/recherche"];

export function SideNav() {
  const path = usePathname();
  return (
    <nav className="flex flex-col gap-1">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = path.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${active ? "bg-accent/15 font-semibold text-accent" : "text-muted hover:bg-panel-2 hover:text-fg"}`}
          >
            <Icon size={18} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

export function BottomNav() {
  const path = usePathname();
  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-5 border-t border-line bg-panel/95 backdrop-blur lg:hidden">
      {NAV.filter((n) => MOBILE.includes(n.href)).map(({ href, label, icon: Icon }) => (
        <Link key={href} href={href} className={`flex flex-col items-center gap-0.5 py-2 text-[10px] ${path.startsWith(href) ? "text-accent" : "text-muted"}`}>
          <Icon size={20} />
          {label.split(" ")[0]}
        </Link>
      ))}
    </nav>
  );
}
