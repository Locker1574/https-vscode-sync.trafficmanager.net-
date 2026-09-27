import type { Metadata } from "next";
import Link from "next/link";
import { MatchCard } from "@/components/match-card";
import { Empty, PageHeader } from "@/components/ui";
import { requireUser } from "@/lib/auth/session";
import { dateLabel, shortDate } from "@/lib/format";
import { db, schema } from "@/lib/db";
import { cards } from "@/server/cards";
import { leagues, listMatches, today } from "@/server/data";
import { asc, gte, sql } from "drizzle-orm";

export const metadata: Metadata = { title: "Calendrier" };

export default async function Calendar({ searchParams }: PageProps<"/calendrier">) {
  const user = await requireUser();
  const sp = await searchParams;
  const league = typeof sp.ligue === "string" ? sp.ligue : undefined;
  const days = await db
    .select({ d: schema.matches.date, n: sql<number>`count(*)::int` })
    .from(schema.matches)
    .where(gte(schema.matches.date, today()))
    .groupBy(schema.matches.date)
    .orderBy(asc(schema.matches.date))
    .limit(21);
  const dates = days.map((d) => [d.d, d.n] as const);
  const day = typeof sp.date === "string" ? sp.date : dates[0]?.[0];
  const [ls, rows] = await Promise.all([leagues(), day ? listMatches({ from: day, to: day, league }) : Promise.resolve([])]);
  const list = await cards(rows, user.id);
  const q = (o: Record<string, string | undefined>) =>
    "?" + new URLSearchParams(Object.entries({ date: day, ligue: league, ...o }).filter(([, v]) => v) as [string, string][]).toString();

  return (
    <>
      <PageHeader title="Calendrier" subtitle={day ? dateLabel(day) : undefined} />
      <div className="-mx-4 mb-4 flex gap-2 overflow-x-auto px-4 pb-1">
        {dates.map(([d, n]) => (
          <Link key={d} href={q({ date: d })} className={`shrink-0 rounded-lg border px-3 py-2 text-center text-xs ${d === day ? "border-accent bg-accent/15 text-accent" : "border-line bg-panel text-muted"}`}>
            <div className="font-semibold capitalize">{shortDate(d)}</div>
            <div>{n} matchs</div>
          </Link>
        ))}
      </div>
      <div className="mb-6 flex flex-wrap gap-2">
        <Link href={q({ ligue: undefined })} className={`rounded-full px-3 py-1 text-xs ${!league ? "bg-accent text-accent-fg" : "bg-panel-2 text-muted"}`}>Toutes</Link>
        {ls.map((l) => (
          <Link key={l.code} href={q({ ligue: l.code })} className={`rounded-full px-3 py-1 text-xs ${league === l.code ? "bg-accent text-accent-fg" : "bg-panel-2 text-muted"}`}>
            {l.name}
          </Link>
        ))}
      </div>
      {list.length ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{list.map((c) => <MatchCard key={c.id} m={c} />)}</div>
      ) : (
        <Empty>Aucun match pour cette sélection.</Empty>
      )}
    </>
  );
}
