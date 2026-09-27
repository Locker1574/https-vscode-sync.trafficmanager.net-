"use client";
import Link from "next/link";
import { Layers, Save } from "lucide-react";
import { useMemo, useState, useTransition } from "react";
import { summarize } from "@/lib/engine/coupon";
import type { Selection } from "@/lib/engine/types";
import { odds, pct } from "@/lib/format";
import { buildCombo, saveCoupon } from "@/server/actions/coupons";
import { ControlsPanel, type Controls } from "./coupon-controls";
import { ConfidenceBar } from "./ui";

export function ComboBuilder({ leagues, maxMatches, paused }: { leagues: { code: string; name: string }[]; maxMatches: number; paused: boolean }) {
  const [matches, setMatches] = useState(5);
  const [perMatch, setPerMatch] = useState(3);
  const [controls, setControls] = useState<Controls>({ pmin: 0.6, mode: "surete", period: "jour", league: "", groups: [] });
  const [rows, setRows] = useState<Selection[][]>([]);
  const [chosen, setChosen] = useState<number[]>([]);
  const [singles, setSingles] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [pending, start] = useTransition();

  const onBuild = () =>
    start(async () => {
      setMsg(null);
      try {
        const r = await buildCombo({ size: matches, perMatch, ...controls, league: controls.league || undefined });
        setRows(r.rows);
        setChosen(r.rows.map(() => 0));
        if (r.limited) setMsg(`Votre offre limite le Combo à ${maxMatches} matchs.`);
        else if (!r.rows.length) setMsg("Aucun match ne correspond. Baissez le seuil de confiance.");
      } catch {
        setMsg("Action impossible (pause jeu responsable active ou erreur serveur).");
      }
    });

  const picked = useMemo(() => rows.map((r, i) => (chosen[i] >= 0 ? r[chosen[i]] : null)).filter((s): s is Selection => !!s), [rows, chosen]);
  const combo = summarize(picked);

  const onSave = () =>
    start(async () => {
      await saveCoupon("combo", controls.mode, controls.pmin, picked);
      setMsg("Combo enregistré dans « Mes coupons ».");
    });

  return (
    <div className="space-y-6">
      <div className="card space-y-5 p-5">
        <div className="grid gap-5 sm:grid-cols-2">
          <label className="text-sm">
            <span className="flex justify-between">Nombre de matchs <strong className="num text-accent">{matches}</strong></span>
            <input type="range" min={1} max={20} value={matches} onChange={(e) => setMatches(Number(e.target.value))} className="mt-2 w-full" />
            <div className="flex justify-between text-xs text-muted"><span>1</span><span>20</span></div>
          </label>
          <div className="text-sm">
            Options proposées par match
            <div className="mt-2 flex flex-wrap gap-1.5">
              {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                <button key={n} type="button" onClick={() => setPerMatch(n)}
                  className={`num h-9 w-9 rounded-lg border text-sm font-semibold ${perMatch === n ? "border-accent bg-accent text-accent-fg" : "border-line bg-panel"}`}>
                  {n}
                </button>
              ))}
            </div>
          </div>
        </div>
        <ControlsPanel value={controls} onChange={setControls} leagues={leagues} />
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" onClick={onBuild} disabled={pending || paused} className="btn-primary"><Layers size={16} /> Construire le combo</button>
          <button type="button" onClick={onSave} disabled={pending || !picked.length} className="btn-ghost"><Save size={16} /> Enregistrer</button>
          <label className="ml-auto flex items-center gap-2 text-sm text-muted">
            <input type="checkbox" checked={singles} onChange={(e) => setSingles(e.target.checked)} /> Paris simples (cotes seules)
          </label>
        </div>
        {msg && <p className="text-sm text-muted" role="status">{msg}</p>}
      </div>

      {rows.length > 0 && (
        <>
          <div className="card flex flex-wrap gap-6 p-5">
            {singles ? (
              <>
                <div><div className="text-xs text-muted">Paris simples</div><div className="num text-2xl font-bold">{picked.length}</div></div>
                <div><div className="text-xs text-muted">Réussite moyenne attendue</div><div className="num text-2xl font-bold text-accent">{pct(picked.reduce((a, s) => a + s.p, 0) / (picked.length || 1), 1)}</div></div>
                <div><div className="text-xs text-muted">Sélections attendues gagnantes</div><div className="num text-2xl font-bold">{picked.reduce((a, s) => a + s.p, 0).toFixed(1)} / {picked.length}</div></div>
              </>
            ) : (
              <>
                <div><div className="text-xs text-muted">Probabilité combinée</div><div className="num text-2xl font-bold text-accent">{pct(combo.combinedProbability, 1)}</div></div>
                <div><div className="text-xs text-muted">Cote totale</div><div className="num text-2xl font-bold">{odds(combo.totalOdds)}</div></div>
                <div><div className="text-xs text-muted">Matchs</div><div className="num text-2xl font-bold">{picked.length}</div></div>
              </>
            )}
          </div>
          <div className="space-y-3">
            {rows.map((opts, i) => (
              <div key={opts[0].matchId} className="card p-4">
                <div className="mb-2 flex items-center justify-between gap-2 text-sm">
                  <Link href={`/match/${encodeURIComponent(opts[0].matchId)}`} className="truncate font-semibold hover:text-accent">{opts[0].match}</Link>
                  <button type="button" className="text-xs text-muted hover:text-loss" onClick={() => setChosen((c) => c.map((v, j) => (j === i ? (v >= 0 ? -1 : 0) : v)))}>
                    {chosen[i] >= 0 ? "Retirer" : "Remettre"}
                  </button>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {opts.map((s, k) => (
                    <button key={s.key} type="button" onClick={() => setChosen((c) => c.map((v, j) => (j === i ? k : v)))}
                      className={`rounded-lg border p-2.5 text-left text-sm ${chosen[i] === k ? "border-accent bg-accent/10" : "border-line"}`}>
                      <div className="flex justify-between gap-2"><span className="truncate">{s.label}</span><span className="num font-semibold">{pct(s.p)}</span></div>
                      <div className="mt-1 flex items-center gap-2"><div className="flex-1"><ConfidenceBar value={s.confidence} /></div><span className="num text-xs text-muted">@{odds(s.odds ?? s.fairOdds)}</span></div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
