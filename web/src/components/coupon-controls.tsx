"use client";
import { MODE_LABEL } from "@/lib/format";
import type { Mode } from "@/lib/engine/types";

export const GROUPS = ["Résultat", "Buts", "Équipes", "1re mi-temps"];

export interface Controls {
  pmin: number;
  mode: Mode;
  period: "jour" | "avenir";
  league: string;
  groups: string[];
}

export function ControlsPanel({ value, onChange, leagues }: { value: Controls; onChange: (c: Controls) => void; leagues: { code: string; name: string }[] }) {
  const set = (patch: Partial<Controls>) => onChange({ ...value, ...patch });
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <label className="text-sm">
        <span className="flex justify-between">
          Confiance minimale <strong className="num text-accent">{Math.round(value.pmin * 100)} %</strong>
        </span>
        <input type="range" min={1} max={99} value={Math.round(value.pmin * 100)} onChange={(e) => set({ pmin: Number(e.target.value) / 100 })} className="mt-2 w-full" />
      </label>
      <div className="text-sm">
        Mode
        <div className="mt-2 grid grid-cols-3 gap-1 rounded-lg bg-panel-2 p-1">
          {(["surete", "equilibre", "rendement"] as const).map((m) => (
            <button key={m} type="button" onClick={() => set({ mode: m })} className={`rounded-md px-2 py-1 text-xs ${value.mode === m ? "bg-panel font-semibold text-accent shadow" : "text-muted"}`}>
              {MODE_LABEL[m]}
            </button>
          ))}
        </div>
      </div>
      <div className="text-sm">
        Période
        <div className="mt-2 grid grid-cols-2 gap-1 rounded-lg bg-panel-2 p-1">
          {([["jour", "Matchs du jour"], ["avenir", "À venir (14 j)"]] as const).map(([k, l]) => (
            <button key={k} type="button" onClick={() => set({ period: k })} className={`rounded-md px-2 py-1 text-xs ${value.period === k ? "bg-panel font-semibold text-accent shadow" : "text-muted"}`}>
              {l}
            </button>
          ))}
        </div>
      </div>
      <label className="text-sm">
        Championnat
        <select value={value.league} onChange={(e) => set({ league: e.target.value })} className="input mt-2">
          <option value="">Tous</option>
          {leagues.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
        </select>
      </label>
      <div className="text-sm sm:col-span-2 lg:col-span-4">
        Marchés
        <div className="mt-2 flex flex-wrap gap-2">
          {GROUPS.map((g) => {
            const on = value.groups.includes(g);
            return (
              <button key={g} type="button" onClick={() => set({ groups: on ? value.groups.filter((x) => x !== g) : [...value.groups, g] })}
                className={`rounded-full border px-3 py-1 text-xs ${on ? "border-accent bg-accent/15 text-accent" : "border-line text-muted"}`}>
                {g}
              </button>
            );
          })}
          <span className="self-center text-xs text-muted">{value.groups.length ? "" : "(tous)"}</span>
        </div>
      </div>
    </div>
  );
}
