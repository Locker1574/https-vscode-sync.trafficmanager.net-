"""Réglage des hyperparamètres par backtest walk-forward (RPS 1X2 sur les saisons de validation).

Validation : saisons 2023-24 et 2024-25. La saison 2025-26 et la saison en cours restent
intactes pour le test final, afin de ne pas sur-ajuster.
"""
from __future__ import annotations

import itertools
import json
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import timedelta
from pathlib import Path

import numpy as np

from .calibration import rps
from .data.openfootball import load
from .engine import run_elo
from .models.dixon_coles import DixonColes

OUT = Path(__file__).resolve().parents[1] / "data" / "params.json"
VALID = ("2023-24", "2024-25")


def _league_preds(args):
    code, hist, xi, l2, prior = args
    out = []
    tests = [m for m in hist if m.played and m.season in VALID]
    weeks = defaultdict(list)
    for m in tests:
        weeks[m.date - timedelta(days=m.date.weekday())].append(m)
    for wk in sorted(weeks):
        dc = DixonColes(xi=xi, l2=l2, use_prior=prior).fit(hist, wk)
        elo, _, _ = run_elo(hist, wk)
        for m in weeks[wk]:
            M = dc.matrix(m.home, m.away)
            i, j = np.indices(M.shape)
            y = [m.hg > m.ag, m.hg == m.ag, m.hg < m.ag]
            out.append(([M[i > j].sum(), np.trace(M), M[i < j].sum()], list(elo.probs(m.home, m.away)), y))
    return code, out


def main():
    ms = load(first=2020)
    leagues = sorted({m.league for m in ms})
    hist = {c: [m for m in ms if m.league == c] for c in leagues}
    grid = list(itertools.product([0.0012, 0.0019, 0.003], [1.0, 2.0, 4.0], [False, True]))
    results = []
    with ProcessPoolExecutor() as ex:
        for xi, l2, prior in grid:
            per = dict(ex.map(_league_preds, [(c, hist[c], xi, l2, prior) for c in leagues]))
            allr = [r for c in leagues for r in per[c]]
            Y = np.array([r[2] for r in allr], float)
            Pd, Pe = np.array([r[0] for r in allr]), np.array([r[1] for r in allr])
            best_w = min(np.linspace(0, 1, 11), key=lambda w: rps(w * Pd + (1 - w) * Pe, Y))
            res = {"xi": xi, "l2": l2, "prior": prior, "rps_dc": rps(Pd, Y), "w_dc": float(best_w),
                   "rps_blend": rps(best_w * Pd + (1 - best_w) * Pe, Y), "n": len(allr)}
            results.append(res)
            print(res, flush=True)
    best = min(results, key=lambda r: r["rps_blend"])
    OUT.write_text(json.dumps({"best": best, "grid": results}, indent=1))
    print("MEILLEUR", best)


if __name__ == "__main__":
    main()
