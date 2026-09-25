"""Calibration isotonique (algorithme PAV) par famille de marchés, et métriques."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

FAMILIES = {"1": "1X2", "X": "1X2", "2": "1X2", "1X": "DC", "X2": "DC", "12": "DC", "BTTS_Y": "BTTS", "BTTS_N": "BTTS"}


def family(key: str) -> str:
    if key in FAMILIES:
        return FAMILIES[key]
    if key.startswith("DNB"):
        return "DNB"
    if key.startswith("HT"):
        return "HT"
    if key.startswith("CS"):
        return "CS"
    if key[0] in "HA" and key[1] in "OU":
        return "TEAM"
    return "OU"


def pav(p: np.ndarray, y: np.ndarray, bins: int = 40):
    """Régression isotonique sur des probabilités regroupées ; renvoie (x, y) pour interpolation."""
    order = np.argsort(p)
    p, y = p[order], y[order]
    edges = np.quantile(p, np.linspace(0, 1, bins + 1))
    xs, ys, ws = [], [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (p >= a) & (p <= b)
        if m.sum():
            xs.append(p[m].mean()); ys.append(y[m].mean()); ws.append(m.sum())
    xs, ys, ws = list(xs), list(ys), list(ws)
    i = 0
    while i < len(ys) - 1:
        if ys[i] > ys[i + 1]:
            w = ws[i] + ws[i + 1]
            ys[i] = (ys[i] * ws[i] + ys[i + 1] * ws[i + 1]) / w
            xs[i] = (xs[i] * ws[i] + xs[i + 1] * ws[i + 1]) / w
            ws[i] = w
            del ys[i + 1], xs[i + 1], ws[i + 1]
            i = max(i - 1, 0)
        else:
            i += 1
    return np.array(xs), np.array(ys)


class Calibrator:
    def __init__(self, maps: dict | None = None):
        self.maps = maps or {}

    def fit(self, rows):
        """rows: itérable de (clé, p, résultat 0/1)."""
        by = {}
        for k, p, y in rows:
            by.setdefault(family(k), ([], []))
            by[family(k)][0].append(p); by[family(k)][1].append(y)
        for f, (ps, ys) in by.items():
            if len(ps) >= 400:
                x, yy = pav(np.array(ps), np.array(ys, float))
                self.maps[f] = [x.tolist(), yy.tolist()]
        return self

    def __call__(self, key: str, p: float) -> float:
        m = self.maps.get(family(key))
        if not m:
            return p
        # mélange 50/50 avec la probabilité brute : évite les paliers trop marqués
        return float(np.clip(0.5 * p + 0.5 * np.interp(p, m[0], m[1]), 0.001, 0.999))

    def save(self, path: Path):
        path.write_text(json.dumps(self.maps))

    @classmethod
    def load(cls, path: Path):
        return cls(json.loads(path.read_text())) if path.exists() else cls()


def brier(p, y):
    p, y = np.asarray(p), np.asarray(y)
    return float(((p - y) ** 2).sum(axis=-1).mean()) if p.ndim > 1 else float(((p - y) ** 2).mean())


def log_loss(p, y):
    p, y = np.clip(np.asarray(p), 1e-9, 1), np.asarray(y)
    return float(-(y * np.log(p)).sum(axis=-1).mean()) if p.ndim > 1 else float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def rps(p, y):
    """Ranked Probability Score pour 1X2 (ordre dom < nul < ext), la mesure de référence en football."""
    cp, cy = np.cumsum(np.asarray(p), axis=1)[:, :-1], np.cumsum(np.asarray(y), axis=1)[:, :-1]
    return float(((cp - cy) ** 2).sum(axis=1).mean() / 2)


def buckets(rows, edges=(0.5, 0.6, 0.7, 0.8, 0.9, 0.98, 1.0)):
    out = []
    ps = np.array([r[0] for r in rows]); ys = np.array([r[1] for r in rows], float)
    for a, b in zip(edges[:-1], edges[1:]):
        m = (ps >= a) & (ps < b)
        out.append({"tranche": f"{int(a*100)}-{int(b*100)} %", "n": int(m.sum()),
                    "annonce": float(ps[m].mean()) if m.sum() else None,
                    "observe": float(ys[m].mean()) if m.sum() else None})
    return out
