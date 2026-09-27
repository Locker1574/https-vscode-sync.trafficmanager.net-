import { confidenceTone, pct, STATUS_LABEL } from "@/lib/format";

export function ConfidenceBar({ value, label = true }: { value: number; label?: boolean }) {
  const v = Math.max(1, Math.min(100, Math.round(value)));
  return (
    <div className="flex items-center gap-2" title={`Indice de confiance : ${v}/100`}>
      <div className="h-1.5 w-full min-w-12 overflow-hidden rounded-full bg-panel-2">
        <div className="h-full rounded-full" style={{ width: `${v}%`, background: confidenceTone(v) }} />
      </div>
      {label && <span className="num w-8 text-right text-xs text-muted">{v}</span>}
    </div>
  );
}

export function Prob({ p }: { p: number }) {
  return (
    <span className="num font-semibold" style={{ color: confidenceTone(p * 100) }}>
      {pct(p)}
    </span>
  );
}

export function StatusBadge({ status }: { status: string | null | undefined }) {
  if (!status) return <span className="rounded-md bg-panel-2 px-2 py-0.5 text-xs text-muted">En attente</span>;
  const color = status === "V" ? "var(--win)" : status === "P" ? "var(--loss)" : "var(--info)";
  return (
    <span className="rounded-md px-2 py-0.5 text-xs font-semibold" style={{ color, background: `color-mix(in srgb, ${color} 15%, transparent)` }}>
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

export function PageHeader({ title, subtitle, children }: { title: string; subtitle?: string; children?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

export function Stat({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="card p-4">
      <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
      <div className="num mt-1 text-2xl font-bold">{value}</div>
      {hint && <div className="mt-1 text-xs text-muted">{hint}</div>}
    </div>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="card p-8 text-center text-sm text-muted">{children}</div>;
}

export function Disclaimer() {
  return (
    <p className="text-xs text-muted">
      Les pourcentages sont des probabilités calibrées, pas des certitudes : un pronostic à 80 % échoue environ une fois sur
      cinq. Pariez de façon responsable, 18 ans et plus. Aide : joueurs-info-service.fr, 09 74 75 13 13.
    </p>
  );
}
