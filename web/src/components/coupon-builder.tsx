"use client";
import { RefreshCw, Save, Sparkles } from "lucide-react";
import { useState, useTransition } from "react";
import type { CouponResult, RegenerateResult, Selection } from "@/lib/engine/types";
import { odds, pct } from "@/lib/format";
import { generateCoupon, regenerateCoupon, saveCoupon } from "@/server/actions/coupons";
import { ControlsPanel, type Controls } from "./coupon-controls";
import { SelectionRow } from "./selection-row";

const SIZES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

export function CouponBuilder({ leagues, maxSize, paused }: { leagues: { code: string; name: string }[]; maxSize: number; paused: boolean }) {
  const [size, setSize] = useState(3);
  const [controls, setControls] = useState<Controls>({ pmin: 0.7, mode: "surete", period: "jour", league: "", groups: [] });
  const [coupon, setCoupon] = useState<CouponResult | null>(null);
  const [regen, setRegen] = useState<RegenerateResult | null>(null);
  const [filter, setFilter] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [pending, start] = useTransition();
  const params = () => ({ size, ...controls, league: controls.league || undefined });

  const run = (fn: () => Promise<void>) =>
    start(async () => {
      setMsg(null);
      try {
        await fn();
      } catch {
        setMsg("Action impossible (pause jeu responsable active ou erreur serveur).");
      }
    });

  const onGenerate = () =>
    run(async () => {
      const r = await generateCoupon(params());
      setCoupon(r);
      setRegen(null);
      if (r.limited) setMsg(`Votre offre limite les coupons à ${maxSize} sélections.`);
      if (!r.size) setMsg("Aucune sélection ne dépasse ce seuil de confiance. Baissez le seuil ou élargissez la période.");
    });

  const onRegenerate = () =>
    run(async () => {
      if (!coupon) return;
      const r = await regenerateCoupon(params(), coupon.selections);
      setRegen(r);
      setCoupon(r);
      setMsg(r.message);
    });

  const toggleLock = (i: number) =>
    setCoupon((c) => c && { ...c, selections: c.selections.map((s, j) => (j === i ? { ...s, locked: !s.locked } : s)) });

  const useAlternative = () => regen && setCoupon(regen.alternative);

  const onSave = () =>
    run(async () => {
      if (!coupon?.size) return;
      await saveCoupon("jour", controls.mode, controls.pmin, coupon.selections);
      setMsg("Coupon enregistré dans « Mes coupons ». Il sera réglé automatiquement (Validé / Perdu).");
    });

  const visible = (coupon?.selections ?? []).map((s, i) => ({ s, i })).filter(({ s }) =>
    !filter || `${s.match} ${s.label}`.toLowerCase().includes(filter.toLowerCase()));

  return (
    <div className="space-y-6">
      <div className="card space-y-5 p-5">
        <div>
          <div className="mb-2 text-sm">Nombre de sélections</div>
          <div className="flex flex-wrap gap-2">
            {SIZES.map((n) => (
              <button key={n} type="button" onClick={() => setSize(n)} disabled={n > maxSize}
                title={n > maxSize ? "Disponible avec l'offre Pro" : undefined}
                className={`num h-10 w-10 rounded-lg border text-sm font-semibold ${size === n ? "border-accent bg-accent text-accent-fg" : "border-line bg-panel"} disabled:opacity-40`}>
                {n}
              </button>
            ))}
          </div>
        </div>
        <ControlsPanel value={controls} onChange={setControls} leagues={leagues} />
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={onGenerate} disabled={pending || paused} className="btn-primary"><Sparkles size={16} /> Générer</button>
          <button type="button" onClick={onRegenerate} disabled={pending || paused || !coupon?.size} className="btn-ghost"><RefreshCw size={16} className={pending ? "animate-spin" : ""} /> Régénérer</button>
          <button type="button" onClick={onSave} disabled={pending || !coupon?.size} className="btn-ghost"><Save size={16} /> Enregistrer</button>
        </div>
        {msg && <p className="text-sm text-muted" role="status">{msg}</p>}
      </div>

      {coupon && coupon.size > 0 && (
        <div className="card p-5">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div className="flex gap-6">
              <div><div className="text-xs text-muted">Probabilité combinée</div><div className="num text-2xl font-bold text-accent">{pct(coupon.combinedProbability, 1)}</div></div>
              <div><div className="text-xs text-muted">Cote totale</div><div className="num text-2xl font-bold">{odds(coupon.totalOdds)}</div></div>
              <div><div className="text-xs text-muted">Sélections</div><div className="num text-2xl font-bold">{coupon.size}</div></div>
            </div>
            <input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Rechercher dans le coupon…" className="input max-w-xs" />
          </div>
          <div className="space-y-2">
            {visible.map(({ s, i }) => <SelectionRow key={`${s.matchId}-${s.key}`} s={s} onLock={() => toggleLock(i)} />)}
          </div>
          <p className="mt-3 text-xs text-muted">Verrouillez une sélection pour la garder lors de la régénération. Les cotes affichées sont les cotes justes (1 / probabilité) quand aucune cote réelle n&apos;est chargée.</p>
        </div>
      )}

      {regen && regen.alternative.size > 0 && (
        <div className="card p-5">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="font-semibold">Alternative (nouveaux matchs)</h3>
              <p className="text-xs text-muted">Probabilité combinée {pct(regen.alternative.combinedProbability, 1)} · cote {odds(regen.alternative.totalOdds)}</p>
            </div>
            <button type="button" onClick={useAlternative} className="btn-ghost text-xs">Utiliser cette alternative</button>
          </div>
          <div className="space-y-2">
            {regen.alternative.selections.map((s: Selection) => <SelectionRow key={`${s.matchId}-${s.key}`} s={s} />)}
          </div>
        </div>
      )}
    </div>
  );
}
